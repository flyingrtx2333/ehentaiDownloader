"""Task-oriented application service shared by desktop frontends.

The service contains no GUI imports.  A frontend supplies an event sink and
receives structured status, progress, log, and completion events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from manga_downloader import MangaDownloader
from pdf_generator import PDFGenerator

EventSink = Callable[[dict], None]


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    save_path: str
    folder_name: str = ""
    proxy_host: str = "127.0.0.1"
    proxy_port: str = "7890"
    generate_pdf: bool = False
    pdf_author: str = ""


@dataclass(frozen=True)
class PdfRequest:
    folder_path: str
    output_name: str = ""
    author: str = ""


class TaskService:
    """Runs one download or PDF task and reports its lifecycle through events."""

    def __init__(self, emit: EventSink):
        self.emit = emit

    def _event(self, event_type: str, task_id: str, **payload: object) -> None:
        self.emit({"type": event_type, "taskId": task_id, **payload})

    def run_download(self, request: DownloadRequest, task_id: Optional[str] = None) -> bool:
        task_id = task_id or str(uuid4())
        if not request.url.strip():
            self._event("completed", task_id, status="failed", error="请先填写下载地址。")
            return False
        if not request.save_path.strip():
            self._event("completed", task_id, status="failed", error="请先选择保存路径。")
            return False

        save_path = Path(request.save_path).expanduser()
        if not save_path.exists() or not save_path.is_dir():
            self._event("completed", task_id, status="failed", error="保存路径不存在或不是文件夹。")
            return False

        try:
            proxy_port = int(request.proxy_port.strip() or "7890")
        except ValueError:
            self._event("completed", task_id, status="failed", error="代理端口必须是数字。")
            return False
        downloader = MangaDownloader(
            proxy_host=request.proxy_host.strip() or "127.0.0.1",
            proxy_port=proxy_port,
        )

        def on_progress(progress: float, status: str, success: int = 0,
                        failed: int = 0, total: int = 0) -> None:
            self._event(
                "progress", task_id, progress=round(progress, 1), status=status,
                success=success, failed=failed, total=total,
            )

        self._event("started", task_id, kind="download", request=asdict(request))
        self._event("log", task_id, message=f"开始下载：{request.url.strip()}")
        try:
            success = downloader.download_manga_from_url(
                request.url.strip(),
                custom_folder_name=request.folder_name.strip() or None,
                progress_callback=on_progress,
                output_dir=str(save_path),
                title_callback=lambda title: self._event("metadata", task_id, title=title),
            )
            failures = getattr(downloader, "failed_urls", [])
            if not success:
                self._event("completed", task_id, status="failed", failedUrls=failures)
                return False

            download_dir = downloader.last_download_dir
            self._event("log", task_id, message="图片下载完成。")
            if request.generate_pdf and download_dir:
                self._event("log", task_id, message="正在生成 PDF…")
                pdf_ok = PDFGenerator().generate_pdf_from_folder(
                    str(download_dir), author=request.pdf_author.strip() or None,
                    progress_callback=on_progress,
                )
                if not pdf_ok:
                    self._event("completed", task_id, status="failed", error="PDF 生成失败。", failedUrls=failures)
                    return False

            self._event(
                "completed", task_id, status="completed", outputPath=str(download_dir or save_path),
                failedUrls=failures,
            )
            return True
        except Exception as exc:  # Boundary for a desktop-process failure.
            self._event("completed", task_id, status="failed", error=str(exc))
            return False

    def run_pdf(self, request: PdfRequest, task_id: Optional[str] = None) -> bool:
        task_id = task_id or str(uuid4())
        folder = Path(request.folder_path).expanduser()
        self._event("started", task_id, kind="pdf", request=asdict(request))
        if not folder.exists() or not folder.is_dir():
            self._event("completed", task_id, status="failed", error="图片文件夹不存在。")
            return False

        output_path = folder / f"{request.output_name.strip() or folder.name}.pdf"

        def on_progress(progress: float, status: str, *_: object) -> None:
            self._event("progress", task_id, progress=round(progress, 1), status=status)

        try:
            success = PDFGenerator().generate_pdf_from_folder(
                str(folder), output_path=str(output_path), author=request.author.strip() or None,
                progress_callback=on_progress,
            )
            self._event(
                "completed", task_id, status="completed" if success else "failed",
                outputPath=str(output_path) if success else None,
                error=None if success else "PDF 生成失败。",
            )
            return success
        except Exception as exc:
            self._event("completed", task_id, status="failed", error=str(exc))
            return False
