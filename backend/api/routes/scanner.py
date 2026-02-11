import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ScanJob, Project
from schemas.scan import ScanRequest, ScanJobResponse, ToolStatus
from engine.tool_manager import check_all_tools, check_tool, install_tool, check_go_installed
from engine.scan_runner import run_scan, active_scans, get_scan_details

router = APIRouter()


# --- Tool Management ---

@router.get("/tools", response_model=list[ToolStatus])
async def get_tool_status():
    tools = await check_all_tools()
    return [ToolStatus(**t) for t in tools]


@router.get("/tools/go-status")
async def get_go_status():
    return await check_go_installed()


@router.post("/tools/{tool_name}/install")
async def install_recon_tool(tool_name: str):
    result = await install_tool(tool_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# --- Scan Management ---

@router.post("/start", response_model=ScanJobResponse)
async def start_scan_endpoint(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    if request.project_id:
        project = (await db.execute(
            select(Project).where(Project.id == request.project_id)
        )).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        project = Project(
            name=request.project_name or request.target_domain,
            root_domain=request.target_domain,
        )
        db.add(project)
        await db.flush()

    # Prevent concurrent scans on same project
    existing = (await db.execute(
        select(ScanJob).where(ScanJob.project_id == project.id, ScanJob.status.in_(["running", "paused"]))
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A scan is already active for this project")

    job = ScanJob(
        project_id=project.id,
        scan_type=request.scan_type,
        target=request.target_domain,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch scan as background task
    asyncio.create_task(run_scan(job.id, project.id, request.scan_type, request.target_domain))

    return job


@router.get("/jobs", response_model=list[ScanJobResponse])
async def list_scan_jobs(
    project_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ScanJob).order_by(ScanJob.created_at.desc())
    if project_id:
        query = query.where(ScanJob.project_id == project_id)
    result = await db.execute(query.limit(50))
    return result.scalars().all()


@router.get("/jobs/{scan_id}", response_model=ScanJobResponse)
async def get_scan_job(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return job


@router.get("/jobs/{scan_id}/details")
async def get_scan_details_endpoint(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")

    live_details = get_scan_details(scan_id)

    return {
        "id": job.id,
        "target": job.target,
        "scan_type": job.scan_type,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "result_summary": job.result_summary,
        "live": live_details,
    }


@router.post("/jobs/{scan_id}/cancel")
async def cancel_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    if job.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail="Scan is not active")

    job.status = "cancelled"
    await db.commit()

    if scan_id in active_scans:
        active_scans[scan_id]["status"] = "cancelled"
        # Kill subprocess if running
        proc = active_scans[scan_id].get("subprocess")
        if proc and proc.returncode is None:
            proc.kill()
        # Unblock if paused so it can exit
        event = active_scans[scan_id].get("pause_event")
        if event:
            event.set()

    return {"message": "Scan cancelled"}


@router.post("/jobs/{scan_id}/pause")
async def pause_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    if job.status != "running":
        raise HTTPException(status_code=400, detail="Scan is not running")

    job.status = "paused"
    await db.commit()

    if scan_id in active_scans:
        active_scans[scan_id]["status"] = "paused"
        event = active_scans[scan_id].get("pause_event")
        if event:
            event.clear()  # blocks the scan loop

    return {"message": "Scan paused"}


@router.post("/jobs/{scan_id}/resume")
async def resume_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    if job.status != "paused":
        raise HTTPException(status_code=400, detail="Scan is not paused")

    job.status = "running"
    await db.commit()

    if scan_id in active_scans:
        active_scans[scan_id]["status"] = "running"
        event = active_scans[scan_id].get("pause_event")
        if event:
            event.set()  # unblocks the scan loop

    return {"message": "Scan resumed"}


@router.post("/jobs/{scan_id}/stop")
async def stop_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanJob).where(ScanJob.id == scan_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    if job.status not in ("running", "paused"):
        raise HTTPException(status_code=400, detail="Scan is not active")

    job.status = "stopped"
    await db.commit()

    if scan_id in active_scans:
        active_scans[scan_id]["status"] = "stopped"
        # Kill current subprocess if running
        proc = active_scans[scan_id].get("subprocess")
        if proc and proc.returncode is None:
            proc.kill()
        # If paused, unblock so it can exit cleanly
        event = active_scans[scan_id].get("pause_event")
        if event:
            event.set()

    return {"message": "Scan stopped. Partial results saved."}


# --- SSE Log Streaming ---

@router.get("/jobs/{scan_id}/stream")
async def stream_scan_logs(scan_id: str):
    async def event_generator():
        last_index = 0
        while True:
            if scan_id not in active_scans:
                yield f"data: {json.dumps({'type': 'done', 'message': 'Scan not active'})}\n\n"
                break

            scan_data = active_scans[scan_id]
            log_lines = scan_data["log_lines"]

            while last_index < len(log_lines):
                line = log_lines[last_index]
                yield f"data: {json.dumps({'type': 'log', 'line': line})}\n\n"
                last_index += 1

            # Send stats update
            stats = scan_data.get("stats", {})
            yield f"data: {json.dumps({'type': 'stats', 'data': stats})}\n\n"

            # Send status update (useful for pause/resume)
            current_status = scan_data.get("status", "running")
            yield f"data: {json.dumps({'type': 'status', 'status': current_status})}\n\n"

            if current_status in ("completed", "failed", "cancelled", "stopped"):
                yield f"data: {json.dumps({'type': 'done', 'status': current_status})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
