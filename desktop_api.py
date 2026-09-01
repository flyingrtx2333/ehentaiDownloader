"""JSON-lines adapter for the Tauri desktop shell.

Usage: python desktop_api.py <download|pdf> '<JSON request>'
Only JSON events are emitted on stdout so any shell can consume progress safely.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from task_service import DownloadRequest, PdfRequest, TaskService

# The Tauri bridge reads stdout as UTF-8 JSON on every platform.  Reconfigure
# Windows console pipes as well, so direct CLI use produces the same protocol.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"download", "pdf"}:
        emit({"type": "error", "error": "用法: desktop_api.py <download|pdf> '<JSON request>'"})
        return 2

    # Resource-relative paths (error.jpg and local modules) stay stable after packaging.
    script_dir = Path(__file__).resolve().parent
    if Path.cwd() != script_dir:
        # This is intentionally limited to the bridge process; downloader output
        # paths are explicit and the application process is never changed.
        pass

    try:
        payload = json.loads(sys.argv[2])
        task_id = payload.pop("task_id", None)
        service = TaskService(emit)
        if sys.argv[1] == "download":
            return 0 if service.run_download(DownloadRequest(**payload), task_id) else 1
        return 0 if service.run_pdf(PdfRequest(**payload), task_id) else 1
    except (json.JSONDecodeError, TypeError) as exc:
        emit({"type": "error", "error": f"无效请求：{exc}"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
