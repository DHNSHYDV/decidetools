import io
import os
import shutil
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

from modules.file_converter import convert_file, ConversionError
from modules.qr_studio import generate_qr_base64, generate_qr_image, QRStudioError
from modules.media_converter import get_media_info, download_media, MediaConversionError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # Max 100 MB
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
ALLOWED_DOC_EXTS = {".docx", ".doc", ".pdf"}

# Configurable site base URL (defaults to production deployment domain)
SITE_URL = os.environ.get("SITE_URL", "https://decidetools-production.up.railway.app").rstrip("/")


@app.context_processor
def inject_global_context():
    # Construct self-referencing canonical URL
    canonical = f"{SITE_URL}{request.path}"
    return {
        "site_url": SITE_URL,
        "canonical_url": canonical,
        "current_year": 2026,
    }


# --- SEO-Friendly Page Routes ---

@app.route("/")
def index():
    return render_template("index.html")


# 1. YouTube Tools
@app.route("/tools/youtube-downloader")
def tool_youtube_downloader():
    return render_template("media_converter.html", sub_tool="downloader")


@app.route("/tools/youtube-to-mp3")
def tool_youtube_mp3():
    return render_template("media_converter.html", sub_tool="mp3")


@app.route("/tools/youtube-to-mp4")
def tool_youtube_mp4():
    return render_template("media_converter.html", sub_tool="mp4")


# 2. QR Code Generator
@app.route("/tools/qr-code-generator")
def tool_qr():
    return render_template("qr_studio.html")


# 3. Document Converters
@app.route("/tools/docx-to-pdf")
def tool_docx_to_pdf():
    return render_template("converter.html", mode="docx-to-pdf")


@app.route("/tools/pdf-to-docx")
def tool_pdf_to_docx():
    return render_template("converter.html", mode="pdf-to-docx")


# --- Legacy Route 301 Permanent Redirects ---

@app.route("/tools/media")
def legacy_media():
    return redirect(url_for("tool_youtube_downloader"), code=301)


@app.route("/tools/qr-code")
def legacy_qr():
    return redirect(url_for("tool_qr"), code=301)


@app.route("/tools/converter")
def legacy_converter():
    return redirect(url_for("tool_docx_to_pdf"), code=301)


# --- Trust & Information Pages ---

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


# --- SEO Infrastructure & Google Verification ---

@app.route("/google33d1629be034105c.html")
def google_verification():
    return "google-site-verification: google33d1629be034105c.html", 200, {"Content-Type": "text/html"}


@app.route("/robots.txt")
def robots_txt():
    content = f"""User-agent: *
Allow: /
Disallow: /api/

Sitemap: {SITE_URL}/sitemap.xml
"""
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        {"loc": f"{SITE_URL}/", "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/youtube-downloader", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/youtube-to-mp3", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/youtube-to-mp4", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/qr-code-generator", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/docx-to-pdf", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/tools/pdf-to-docx", "priority": "0.9", "changefreq": "weekly"},
        {"loc": f"{SITE_URL}/about", "priority": "0.5", "changefreq": "monthly"},
        {"loc": f"{SITE_URL}/privacy", "priority": "0.5", "changefreq": "monthly"},
        {"loc": f"{SITE_URL}/terms", "priority": "0.5", "changefreq": "monthly"},
    ]
    xml_items = "\n".join([
        f"""  <url>
    <loc>{p['loc']}</loc>
    <lastmod>2026-09-09</lastmod>
    <changefreq>{p['changefreq']}</changefreq>
    <priority>{p['priority']}</priority>
  </url>""" for p in pages
    ])
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_items}
</urlset>"""
    return xml_content, 200, {"Content-Type": "application/xml; charset=utf-8"}


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404



# --- API Routes ---

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "state": "healthy",
        "platform": "Decide Group Of Solutions",
        "version": "2.0.0",
        "services": {
            "document_converter": "operational",
            "qr_studio": "operational",
            "media_converter": "operational"
        }
    })


# 1. Document Converter API
@app.route("/api/convert", methods=["POST"])
def api_convert():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    original_filename = file.filename
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_DOC_EXTS:
        return jsonify({"error": f"Unsupported file extension '{ext}'. Please upload .docx, .doc, or .pdf."}), 400

    stem = Path(original_filename).stem
    target_ext = ".pdf" if ext in [".docx", ".doc"] else ".docx"
    output_download_name = f"{stem}{target_ext}"

    temp_dir = tempfile.mkdtemp(prefix="conv_")
    safe_name = secure_filename(original_filename) or f"input{ext}"
    input_path = os.path.join(temp_dir, safe_name)
    output_path = os.path.join(temp_dir, f"converted{target_ext}")

    try:
        file.save(input_path)
        convert_file(input_path, output_path)

        with open(output_path, "rb") as f:
            file_data = io.BytesIO(f.read())

        shutil.rmtree(temp_dir, ignore_errors=True)

        mimetype = "application/pdf" if target_ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return send_file(
            file_data,
            as_attachment=True,
            download_name=output_download_name,
            mimetype=mimetype
        )
    except ConversionError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": f"Internal document conversion error: {str(e)}"}), 500


# 2. QR Code Studio APIs
@app.route("/api/qr/preview", methods=["POST"])
def api_qr_preview():
    data = request.get_json() or {}
    text = data.get("data", "https://decidegroup.com")
    fill_color = data.get("fill_color", "#000000")
    back_color = data.get("back_color", "#ffffff")
    ec = data.get("error_correction", "M")

    try:
        data_url = generate_qr_base64(
            data=text,
            fill_color=fill_color,
            back_color=back_color,
            error_correction=ec
        )
        return jsonify({"status": "ok", "data_url": data_url})
    except QRStudioError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to render preview: {str(e)}"}), 500


@app.route("/api/qr/download", methods=["POST"])
def api_qr_download():
    data = request.get_json() or {}
    text = data.get("data", "https://decidegroup.com")
    fill_color = data.get("fill_color", "#000000")
    back_color = data.get("back_color", "#ffffff")
    ec = data.get("error_correction", "M")
    fmt = data.get("format", "png").lower()

    if fmt not in ["png", "svg"]:
        fmt = "png"

    try:
        raw_bytes = generate_qr_image(
            data=text,
            fill_color=fill_color,
            back_color=back_color,
            error_correction=ec,
            output_format=fmt
        )
        buf = io.BytesIO(raw_bytes)
        mimetype = "image/svg+xml" if fmt == "svg" else "image/png"
        return send_file(
            buf,
            as_attachment=True,
            download_name=f"decide_qr.{fmt}",
            mimetype=mimetype
        )
    except Exception as e:
        return jsonify({"error": f"Download error: {str(e)}"}), 500


# 3. Media Converter APIs
@app.route("/api/media/info", methods=["POST"])
def api_media_info():
    data = request.get_json() or {}
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        info = get_media_info(url)
        return jsonify(info)
    except MediaConversionError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Media inspection error: {str(e)}"}), 500


@app.route("/api/media/download", methods=["POST"])
def api_media_download():
    data = request.get_json() or {}
    url = data.get("url", "")
    target_format = data.get("format", "mp3")
    quality = data.get("quality", "192")
    resolution = data.get("resolution", "best")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    temp_dir = tempfile.mkdtemp(prefix="media_dl_")
    try:
        file_path, download_name = download_media(url, target_format, quality, resolution, temp_dir)
        with open(file_path, "rb") as f:
            file_data = io.BytesIO(f.read())

        shutil.rmtree(temp_dir, ignore_errors=True)

        mimetype = "audio/mpeg" if target_format == "mp3" else "video/mp4"
        return send_file(
            file_data,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    except MediaConversionError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": f"Media conversion error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f" 🚀 Decide Group Of Solutions - Multi-Tool Platform")
    print(f" Local URL: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
