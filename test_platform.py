import os
import shutil
import tempfile
import unittest
from pathlib import Path
import docx

from app import app
from modules.file_converter import docx_to_pdf, pdf_to_docx
from modules.qr_studio import generate_qr_base64, generate_qr_image, build_wifi_payload
from modules.media_converter import format_duration, sanitize_filename


class TestDecidePlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="platform_test_")
        cls.sample_docx = os.path.join(cls.test_dir, "sample.docx")

        doc = docx.Document()
        doc.add_heading("Decide Platform Document", 0)
        doc.add_paragraph("Testing SaaS unified document conversion workflow.")
        doc.save(cls.sample_docx)

        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # 1. Page Routes
    def test_pages_render_successfully(self):
        pages = ["/", "/tools/converter", "/tools/qr-code", "/tools/media"]
        for page in pages:
            res = self.client.get(page)
            self.assertEqual(res.status_code, 200, f"Page {page} failed to load")
            self.assertIn(b"Decide", res.data)

    def test_api_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["platform"], "Decide Group Of Solutions")

    # 2. Document Studio
    def test_document_conversion(self):
        pdf_out = docx_to_pdf(self.sample_docx)
        self.assertTrue(os.path.isfile(pdf_out))

        docx_out = os.path.join(self.test_dir, "roundtrip.docx")
        pdf_to_docx(pdf_out, docx_out)
        self.assertTrue(os.path.isfile(docx_out))

    def test_api_convert_document(self):
        with open(self.sample_docx, "rb") as f:
            res = self.client.post("/api/convert", data={"file": (f, "test.docx")})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")

    # 3. QR Code Studio
    def test_wifi_payload_builder(self):
        payload = build_wifi_payload("OfficeWiFi", "SecretPass123", "WPA")
        self.assertEqual(payload, "WIFI:T:WPA;S:OfficeWiFi;P:SecretPass123;H:false;;")

    def test_qr_generation_png_and_svg(self):
        png_bytes = generate_qr_image("https://decidegroup.com", output_format="png")
        self.assertGreater(len(png_bytes), 0)
        self.assertTrue(png_bytes.startswith(b"\x89PNG"))

        svg_bytes = generate_qr_image("https://decidegroup.com", output_format="svg")
        self.assertGreater(len(svg_bytes), 0)
        self.assertIn(b"<svg", svg_bytes)

    def test_api_qr_preview(self):
        res = self.client.post("/api/qr/preview", json={
            "data": "https://decidegroup.com",
            "fill_color": "#112233",
            "back_color": "#ffffff"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["data_url"].startswith("data:image/png;base64,"))

    def test_api_qr_download(self):
        res = self.client.post("/api/qr/download", json={
            "data": "https://decidegroup.com",
            "format": "svg"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "image/svg+xml")

    # 4. Media Converter Helpers
    def test_media_utilities(self):
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3665), "01:01:05")
        self.assertEqual(sanitize_filename('Test/File:Name"<>|'), "TestFileName")

    def test_api_media_info_validation(self):
        # Empty URL should return 400
        res = self.client.post("/api/media/info", json={"url": ""})
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
