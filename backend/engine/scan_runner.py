import asyncio
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import ScanJob
from engine.tool_manager import TOOLS, check_tool, _get_go_env
from parsers.subfinder import parse_subfinder
from parsers.httpx_parser import parse_httpx
from parsers.waybackurls import parse_waybackurls
from parsers.nuclei import parse_nuclei

# In-memory registry of active scans for SSE streaming
active_scans: dict[str, dict] = {}

FULL_AUTO_CHAIN = ["subfinder", "httpx", "waybackurls", "nuclei"]


async def _append_log(scan_id: str, line: str):
    if scan_id in active_scans:
        active_scans[scan_id]["log_lines"].append(line)


async def _update_job(scan_id: str, **kwargs):
    async with async_session() as db:
        result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
        job = result.scalar_one_or_none()
        if job:
            for k, v in kwargs.items():
                setattr(job, k, v)
            await db.commit()


async def _check_pause(scan_id: str):
    """Block until scan is unpaused. Returns immediately if not paused."""
    if scan_id not in active_scans:
        return
    event = active_scans[scan_id].get("pause_event")
    if event and not event.is_set():
        await _append_log(scan_id, "[*] Scan paused. Waiting to resume...")
        await _update_job(scan_id, status="paused", current_step="Paused")
        await event.wait()
        if _is_stopped(scan_id):
            return
        await _append_log(scan_id, "[*] Scan resumed.")
        await _update_job(scan_id, status="running")
        active_scans[scan_id]["status"] = "running"


def _is_stopped(scan_id: str) -> bool:
    """Check if scan has been stopped by user."""
    return (scan_id in active_scans and
            active_scans[scan_id].get("status") in ("stopped", "cancelled"))


def get_scan_details(scan_id: str) -> dict | None:
    """Get detailed progress information for a running scan."""
    if scan_id not in active_scans:
        return None
    scan = active_scans[scan_id]
    stats = scan.get("stats", {})
    started = stats.get("started_at")
    elapsed = None
    if started:
        start_dt = datetime.fromisoformat(started)
        elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()

    return {
        "subdomains_found": stats.get("subdomains_found", 0),
        "urls_discovered": stats.get("urls_discovered", 0),
        "params_classified": stats.get("params_classified", 0),
        "findings_count": stats.get("findings_count", 0),
        "current_tool": stats.get("current_tool"),
        "elapsed_seconds": elapsed,
        "log_line_count": len(scan.get("log_lines", [])),
        "tool_timings": stats.get("tool_timings", {}),
        "status": scan.get("status"),
    }


async def _run_tool_subprocess(scan_id: str, cmd: list[str], stdin_data: str | None = None, timeout: int = 600) -> str:
    """Run a tool subprocess and stream output lines to the scan log."""
    env = _get_go_env()

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin_data else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    # Store subprocess reference for stop/kill
    if scan_id in active_scans:
        active_scans[scan_id]["subprocess"] = proc

    # Write stdin if provided, then close it
    if stdin_data and proc.stdin:
        proc.stdin.write(stdin_data.encode())
        await proc.stdin.drain()
        proc.stdin.close()

    output_lines = []
    while True:
        # Check if scan was cancelled or stopped
        if _is_stopped(scan_id):
            proc.kill()
            status = active_scans.get(scan_id, {}).get("status", "cancelled")
            await _append_log(scan_id, f"[!] Scan {status} by user")
            break

        line = await proc.stdout.readline()
        if not line:
            break
        decoded = line.decode().strip()
        if decoded:
            output_lines.append(decoded)
            await _append_log(scan_id, decoded)

    await proc.wait()

    stderr_output = (await proc.stderr.read()).decode()
    if stderr_output.strip():
        for err_line in stderr_output.strip().split("\n")[:20]:
            await _append_log(scan_id, f"[stderr] {err_line}")

    return "\n".join(output_lines)


async def _run_and_parse(scan_id: str, project_id: str, tool_name: str, target: str,
                         stdin_data: str | None = None) -> dict:
    """Run a tool and parse its output into the database."""
    status = await check_tool(tool_name)
    if not status["installed"]:
        raise RuntimeError(f"{tool_name} is not installed. Install it from the Scanner page first.")

    await _append_log(scan_id, f"[*] Starting {tool_name} against {target}")
    await _update_job(scan_id, current_step=f"Running {tool_name}...")

    # Update stats
    if scan_id in active_scans:
        active_scans[scan_id]["stats"]["current_tool"] = tool_name

    # Build command
    cmd = _build_command(tool_name, target)

    # Run subprocess
    output = await _run_tool_subprocess(scan_id, cmd, stdin_data=stdin_data)
    line_count = len(output.strip().splitlines()) if output.strip() else 0
    await _append_log(scan_id, f"[+] {tool_name} finished: {line_count} lines of output")

    # Update tool timing
    if scan_id in active_scans:
        active_scans[scan_id]["stats"]["tool_timings"][tool_name] = "completed"

    # Parse output into database
    if not output.strip():
        await _append_log(scan_id, f"[!] {tool_name} returned no output")
        return {"parsed_count": 0, "new_count": 0, "duplicate_count": 0}

    async with async_session() as db:
        if tool_name == "subfinder":
            result = await parse_subfinder(project_id, output, db)
        elif tool_name == "httpx":
            result = await parse_httpx(project_id, output, db)
        elif tool_name in ("waybackurls", "gau", "katana"):
            result = await parse_waybackurls(project_id, output, db)
        elif tool_name == "nuclei":
            result = await parse_nuclei(project_id, output, db)
        else:
            result = {"parsed_count": 0, "new_count": 0, "duplicate_count": 0}

    await _append_log(scan_id, f"[+] Parsed: {result.get('new_count', 0)} new, {result.get('duplicate_count', 0)} duplicates")
    return result


def _build_command(tool_name: str, target: str) -> list[str]:
    if tool_name == "subfinder":
        return ["subfinder", "-d", target, "-silent"]
    elif tool_name == "httpx":
        return ["httpx", "-silent", "-json", "-title", "-tech-detect", "-status-code"]
    elif tool_name == "waybackurls":
        return ["waybackurls", target]
    elif tool_name == "gau":
        return ["gau", target, "--threads", "5"]
    elif tool_name == "katana":
        return ["katana", "-u", f"https://{target}", "-silent", "-depth", "2"]
    elif tool_name == "nuclei":
        return ["nuclei", "-jsonl", "-silent", "-severity", "low,medium,high,critical"]
    return [tool_name]


async def run_scan(scan_id: str, project_id: str, scan_type: str, target: str):
    """Main scan orchestrator - runs as a background asyncio task."""
    pause_event = asyncio.Event()
    pause_event.set()  # start in "running" state

    active_scans[scan_id] = {
        "log_lines": [],
        "status": "running",
        "pause_event": pause_event,
        "subprocess": None,
        "stats": {
            "subdomains_found": 0,
            "urls_discovered": 0,
            "params_classified": 0,
            "findings_count": 0,
            "current_tool": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tool_timings": {},
        },
    }
    summary = {}

    try:
        await _update_job(scan_id, status="running", started_at=datetime.now(timezone.utc))
        await _append_log(scan_id, f"[*] Starting {scan_type} scan on {target}")

        if scan_type == "full_auto":
            # Step 1: subfinder
            await _check_pause(scan_id)
            if _is_stopped(scan_id):
                await _save_partial(scan_id, summary)
                return
            await _update_job(scan_id, progress=5)
            sub_result = await _run_and_parse(scan_id, project_id, "subfinder", target)
            summary["subfinder"] = sub_result
            if scan_id in active_scans:
                active_scans[scan_id]["stats"]["subdomains_found"] = sub_result.get("new_count", 0)

            # Collect subdomains for httpx input
            async with async_session() as db:
                from models import Subdomain
                subs = (await db.execute(
                    select(Subdomain.subdomain).where(Subdomain.project_id == project_id)
                )).scalars().all()
            subdomain_list = "\n".join(subs)

            # Step 2: httpx (pipe subdomains as stdin)
            await _check_pause(scan_id)
            if _is_stopped(scan_id):
                await _save_partial(scan_id, summary)
                return
            await _update_job(scan_id, progress=30)
            if subdomain_list.strip():
                httpx_result = await _run_and_parse(scan_id, project_id, "httpx", target, stdin_data=subdomain_list)
                summary["httpx"] = httpx_result
            else:
                await _append_log(scan_id, "[!] No subdomains found, skipping httpx")

            # Step 3: waybackurls
            await _check_pause(scan_id)
            if _is_stopped(scan_id):
                await _save_partial(scan_id, summary)
                return
            await _update_job(scan_id, progress=55)
            wb_result = await _run_and_parse(scan_id, project_id, "waybackurls", target)
            summary["waybackurls"] = wb_result
            if scan_id in active_scans:
                active_scans[scan_id]["stats"]["urls_discovered"] = wb_result.get("new_count", 0)
                active_scans[scan_id]["stats"]["params_classified"] = wb_result.get("param_count", 0)

            # Step 4: nuclei (pipe all subdomains as targets)
            await _check_pause(scan_id)
            if _is_stopped(scan_id):
                await _save_partial(scan_id, summary)
                return
            await _update_job(scan_id, progress=75)
            if subdomain_list.strip():
                nuclei_input = "\n".join([f"https://{s}" for s in subs if s])
                nuclei_result = await _run_and_parse(scan_id, project_id, "nuclei", target, stdin_data=nuclei_input)
                summary["nuclei"] = nuclei_result
                if scan_id in active_scans:
                    active_scans[scan_id]["stats"]["findings_count"] = nuclei_result.get("new_count", 0)
            else:
                await _append_log(scan_id, "[!] No targets for nuclei, skipping")

        else:
            # Single tool scan
            await _update_job(scan_id, progress=10)
            result = await _run_and_parse(scan_id, project_id, scan_type, target)
            summary[scan_type] = result

        await _update_job(
            scan_id,
            progress=100,
            status="completed",
            result_summary=summary,
            completed_at=datetime.now(timezone.utc),
        )
        await _append_log(scan_id, "[+] Scan completed successfully!")
        active_scans[scan_id]["status"] = "completed"

    except Exception as e:
        await _update_job(
            scan_id,
            status="failed",
            error=str(e),
            result_summary=summary,
            completed_at=datetime.now(timezone.utc),
        )
        await _append_log(scan_id, f"[!] SCAN FAILED: {str(e)}")
        if scan_id in active_scans:
            active_scans[scan_id]["status"] = "failed"


async def _save_partial(scan_id: str, summary: dict):
    """Save partial results when scan is stopped."""
    status = active_scans.get(scan_id, {}).get("status", "stopped")
    await _update_job(
        scan_id,
        status=status,
        result_summary=summary,
        completed_at=datetime.now(timezone.utc),
    )
    await _append_log(scan_id, f"[*] Scan {status}. Partial results saved.")
