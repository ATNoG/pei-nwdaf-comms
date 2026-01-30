"""
API routes for status monitoring.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict
import asyncio

from ...models.schemas import StatusResponse
from ...core.state import state_manager
from ...core.logging import get_logger
from ...services.monitoring import monitoring_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/status/{box_id}", response_model=StatusResponse)
async def get_box_status(box_id: str):
    """
    Get the current status of a container box.

    Checks the status URL for each attribute and returns the results.
    Also maintains backward compatibility with legacy parameters.
    """
    # Find the box
    box = await state_manager.get_box(box_id)
    if not box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Box with ID {box_id} not found",
        )

    # If no status URL and no attributes, return unknown
    if not box.status_url and not box.attributes:
        return StatusResponse(status="unknown", value="No status URL configured")

    # Base status URL
    base_url = str(box.status_url) if box.status_url else None

    # Results dictionary to store all attribute/parameter statuses
    results: Dict[str, Dict] = {}

    # Check new-style attributes
    if box.attributes:
        for attr in box.attributes:
            # Use attribute URL if provided, otherwise fall back to base URL
            check_url = str(attr.url) if attr.url else base_url

            if not check_url:
                # No URL available for this attribute
                results[attr.name] = {
                    "status": "unknown",
                    "value": "No URL configured",
                    "type": attr.type,
                }
                continue

            param_config = {"type": attr.type.replace("_", "/")}  # ok_nok -> ok/nok
            result = await monitoring_service.check_url_status(check_url, param_config)
            results[attr.name] = {
                **result,
                "type": attr.type,
                "label": attr.label,
            }

    # Check legacy parameters (backward compatibility)
    for param_name, param_config in box.parameters.items():
        if param_config.get("type") in ["ok/nok", "text"]:
            if base_url:
                result = await monitoring_service.check_url_status(base_url, param_config)
                results[param_name] = result
            else:
                results[param_name] = {
                    "status": "unknown",
                    "value": "No URL configured",
                    "type": param_config.get("type", "unknown"),
                }

    # Determine overall status
    if results:
        overall_status = monitoring_service.determine_overall_status(results)
    else:
        # No parameters or attributes - check URL directly
        if base_url:
            url_result = await monitoring_service.check_url_status(base_url, {})
            overall_status = url_result.get("status", "unknown")
            results = {"_default": url_result}
        else:
            overall_status = "unknown"

    # Cache the results with timestamp
    status_data = {
        "status": overall_status,
        "value": results.get("_default", {}).get("value", overall_status),
        "parameters": results,
        "timestamp": asyncio.get_event_loop().time(),
    }

    state_manager.set_status(box_id, status_data)
    return StatusResponse(**status_data)


@router.get("/line-status/{line_id}")
async def get_line_status(line_id: str):
    """
    Get the current status of a connection line.

    Returns the line status and the source box status if available.
    """
    # Find the line
    line = await state_manager.get_line(line_id)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line with ID {line_id} not found",
        )

    # For free lines (not connected to boxes), just return the status
    if line.source_box_id == "free_start" and line.target_box_id == "free_end":
        return {"status": line.status, "source_status": "free"}

    # Get source box status for connected lines
    source_status = "unknown"
    box_status = state_manager.get_status(line.source_box_id)
    if box_status:
        source_status = box_status.get("status", "unknown")

    # Update line status if needed
    if line.change_on_response:
        if source_status == "ok":
            updated_status = "ok"
        elif source_status == "nok" and line.red_on_failure:
            updated_status = "nok"
        else:
            updated_status = "unknown"

        # Update line in state
        line.status = updated_status
        await state_manager.update_line(line_id, line)

    return {"status": line.status, "source_status": source_status}
