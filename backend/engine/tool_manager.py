import asyncio
import os
import shutil
from dataclasses import dataclass


@dataclass
class ToolInfo:
    name: str
    binary_name: str
    go_install_path: str
    version_flag: str


TOOLS = {
    "subfinder": ToolInfo("subfinder", "subfinder", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest", "-version"),
    "httpx": ToolInfo("httpx", "httpx", "github.com/projectdiscovery/httpx/cmd/httpx@latest", "-version"),
    "nuclei": ToolInfo("nuclei", "nuclei", "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest", "-version"),
    "waybackurls": ToolInfo("waybackurls", "waybackurls", "github.com/tomnomnom/waybackurls@latest", ""),
    "gau": ToolInfo("gau", "gau", "github.com/lc/gau/v2/cmd/gau@latest", "-version"),
    "katana": ToolInfo("katana", "katana", "github.com/projectdiscovery/katana/cmd/katana@latest", "-version"),
}


def _get_go_env():
    """Build env dict that includes GOPATH/GOBIN so installed binaries are findable."""
    env = os.environ.copy()
    gopath = env.get("GOPATH", os.path.expanduser("~/go"))
    gobin = os.path.join(gopath, "bin")
    path = env.get("PATH", "")
    if gobin not in path:
        env["PATH"] = gobin + ":" + path
    return env


async def check_tool(name: str) -> dict:
    tool = TOOLS.get(name)
    if not tool:
        return {"name": name, "installed": False, "path": None, "version": None}

    env = _get_go_env()
    # Prioritize Go bin path to avoid picking up wrong binaries (e.g. Python httpx)
    gopath = env.get("GOPATH", os.path.expanduser("~/go"))
    gobin_path = os.path.join(gopath, "bin", tool.binary_name)
    if os.path.isfile(gobin_path) and os.access(gobin_path, os.X_OK):
        path = gobin_path
    else:
        path = shutil.which(tool.binary_name, path=env.get("PATH"))
    if not path:
        return {"name": name, "installed": False, "path": None, "version": None}

    version = None
    if tool.version_flag:
        try:
            proc = await asyncio.create_subprocess_exec(
                path, tool.version_flag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            version = (stdout.decode() + stderr.decode()).strip().split("\n")[0][:100]
        except Exception:
            version = "installed"

    return {"name": name, "installed": True, "path": path, "version": version}


async def check_all_tools() -> list[dict]:
    results = await asyncio.gather(*[check_tool(name) for name in TOOLS])
    return list(results)


async def check_go_installed() -> dict:
    env = _get_go_env()
    go_path = shutil.which("go", path=env.get("PATH"))
    if not go_path:
        return {"installed": False, "path": None, "version": None}
    try:
        proc = await asyncio.create_subprocess_exec(
            "go", "version",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        return {"installed": True, "path": go_path, "version": stdout.decode().strip()}
    except Exception:
        return {"installed": True, "path": go_path, "version": "unknown"}


async def install_tool(name: str) -> dict:
    tool = TOOLS.get(name)
    if not tool:
        return {"success": False, "error": f"Unknown tool: {name}"}

    go_status = await check_go_installed()
    if not go_status["installed"]:
        return {"success": False, "error": "Go is not installed. Install Go first: https://go.dev/dl/"}

    env = _get_go_env()

    try:
        proc = await asyncio.create_subprocess_exec(
            "go", "install", "-v", tool.go_install_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode == 0:
            status = await check_tool(name)
            return {"success": True, "tool": status}
        else:
            return {"success": False, "error": stderr.decode()[:500]}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Installation timed out (5 minutes)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
