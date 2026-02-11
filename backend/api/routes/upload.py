from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.upload import UploadResponse, AutoUploadResponse
from parsers.subfinder import parse_subfinder
from parsers.waybackurls import parse_waybackurls
from parsers.httpx_parser import parse_httpx
from parsers.nuclei import parse_nuclei
from parsers.auto_detect import parse_auto_detect

router = APIRouter()

TOOL_PARSERS = {
    "subfinder": parse_subfinder,
    "amass": parse_subfinder,
    "waybackurls": parse_waybackurls,
    "gau": parse_waybackurls,
    "katana": parse_waybackurls,
    "httpx": parse_httpx,
    "nuclei": parse_nuclei,
}


@router.post("/{project_id}/upload", response_model=UploadResponse)
async def upload_recon_file(
    project_id: str,
    tool_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if tool_type not in TOOL_PARSERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported tool type: {tool_type}. Supported: {list(TOOL_PARSERS.keys())}",
        )

    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    parser = TOOL_PARSERS[tool_type]
    result = await parser(project_id, text, db)

    return UploadResponse(
        tool_type=tool_type,
        parsed_count=result["parsed_count"],
        new_count=result["new_count"],
        duplicate_count=result["duplicate_count"],
        message=f"Parsed {result['new_count']} new entries from {tool_type} output",
    )


@router.post("/{project_id}/upload-auto", response_model=AutoUploadResponse)
async def upload_auto_detect(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a combined recon file - auto-detects subdomains, URLs, httpx JSON, nuclei JSON."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    result = await parse_auto_detect(project_id, text, db)

    breakdown = result["breakdown"]
    parts = []
    if breakdown["subdomains"]:
        parts.append(f"{breakdown['subdomains']} subdomains")
    if breakdown["urls_with_params"]:
        parts.append(f"{breakdown['urls_with_params']} URLs with params")
    if breakdown["urls_no_params"]:
        parts.append(f"{breakdown['urls_no_params']} URLs")
    if breakdown["httpx_entries"]:
        parts.append(f"{breakdown['httpx_entries']} httpx entries")
    if breakdown["nuclei_findings"]:
        parts.append(f"{breakdown['nuclei_findings']} nuclei findings")
    if breakdown["skipped"]:
        parts.append(f"{breakdown['skipped']} skipped")

    msg = f"Auto-detected: {', '.join(parts)}" if parts else "No data detected"

    return AutoUploadResponse(
        tool_type="auto",
        parsed_count=result["parsed_count"],
        new_count=result["new_count"],
        duplicate_count=result["duplicate_count"],
        message=msg,
        breakdown=breakdown,
    )
