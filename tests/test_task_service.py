import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from task_service import DownloadRequest, PdfRequest, TaskService


class TaskServiceValidationTests(unittest.TestCase):
    def test_download_emits_recognized_title_before_completion(self):
        events = []

        class FakeDownloader:
            failed_urls = []

            def __init__(self, **_options):
                self.last_download_dir = None

            def download_manga_from_url(self, _url, **options):
                self.last_download_dir = Path(options["output_dir"]) / "Recognized Title"
                options["title_callback"]("Recognized Title")
                return True

        with tempfile.TemporaryDirectory() as temp_dir, patch("task_service.MangaDownloader", FakeDownloader):
            result = TaskService(events.append).run_download(
                DownloadRequest(url="https://example.invalid/s/example/1-1", save_path=temp_dir),
                task_id="title-task",
            )

        self.assertTrue(result)
        self.assertEqual(next(event for event in events if event["type"] == "metadata")["title"], "Recognized Title")
        self.assertEqual(events[-1]["status"], "completed")

    def test_download_requires_url_and_never_changes_process_directory(self):
        events = []
        service = TaskService(events.append)
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = service.run_download(DownloadRequest(url="", save_path=temp_dir), task_id="test-task")
        self.assertFalse(result)
        self.assertEqual(os.getcwd(), original_cwd)
        self.assertEqual(events[-1]["type"], "completed")
        self.assertEqual(events[-1]["error"], "请先填写下载地址。")

    def test_pdf_rejects_missing_folder(self):
        events = []
        result = TaskService(events.append).run_pdf(PdfRequest(folder_path="missing-folder"), task_id="pdf-task")
        self.assertFalse(result)
        self.assertEqual(events[-1]["status"], "failed")

    def test_download_rejects_non_numeric_proxy_port(self):
        events = []
        with tempfile.TemporaryDirectory() as temp_dir:
            result = TaskService(events.append).run_download(
                DownloadRequest(url="https://example.invalid/page", save_path=temp_dir, proxy_port="not-a-port"),
                task_id="port-task",
            )
        self.assertFalse(result)
        self.assertEqual(events[-1]["error"], "代理端口必须是数字。")
