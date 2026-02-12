"""WebSocket room naming and payload helpers."""

from typing import Dict, Any


def analysis_room(analysis_id: str) -> str:
    """Return a stable Socket.IO room name for an analysis."""
    return f"analysis_{analysis_id}"


def progress_event(analysis_id: str, progress: int, status: str, error_message: str | None = None) -> Dict[str, Any]:
    """Normalize progress payload shape emitted to clients."""
    return {
        "analysis_id": analysis_id,
        "progress": progress,
        "status": status,
        "error_message": error_message,
    }
