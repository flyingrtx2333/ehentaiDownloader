import tempfile
import unittest
import os
from pathlib import Path

from task_service import DownloadRequest, PdfRequest, TaskService


class TaskServiceValidationTests(unittest.TestCase):
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
