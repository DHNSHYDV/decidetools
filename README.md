# Decide Group Of Solutions - Multi-Tool SaaS Suite

A high-performance, privacy-first SaaS utility platform uniting document processing, custom QR vector generation, and multimedia extraction under a unified brand.

---

## 🛠️ Included Flagship Tools

### 1. Document Studio (`/tools/converter`)
- **DOCX ⇄ PDF**: Convert Word documents to PDF and vice versa with precision margins, fonts, tables, and images.
- **Engine**: Headless LibreOffice + `pdf2docx`.
- **Drag & Drop**: In-browser drag-and-drop with instant streaming downloads.

### 2. QR Code Studio (`/tools/qr-code`)
- **Modes**: Web URLs, plain text, and complete Wi-Fi network configurations (SSID, Password, Security).
- **Customization**: Custom foreground and background hex colors, adjustable error correction levels (L, M, Q, H).
- **Live Vector Preview**: Real-time canvas/data-URL rendering.
- **Export Formats**: Standard PNG raster or scalable vector SVG.

### 3. Media Converter (`/tools/media`)
- **YouTube to MP3**: Convert online videos to high-fidelity MP3 audio (320kbps Studio Quality, 192kbps Standard).
- **YouTube to MP4**: Download and merge video + audio into standard MP4 format.
- **Resolution Selector**: Choose from **Best Available (Auto Max)**, **1080p (Full HD)**, **720p (HD)**, **480p (Standard)**, or **360p (Data Saver)**.
- **Live Metadata Inspector**: Preview video title, thumbnail, channel, and duration before downloading.
- **Engine**: `yt-dlp` + `/usr/bin/ffmpeg`.

---

## 🚀 Getting Started

### Launch the Platform
From the repository directory:
```bash
./run.sh
```

Then open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Accessing Individual Tools
- **Main Portal**: `http://127.0.0.1:5000/`
- **Document Studio**: `http://127.0.0.1:5000/tools/converter`
- **QR Code Studio**: `http://127.0.0.1:5000/tools/qr-code`
- **Media Converter**: `http://127.0.0.1:5000/tools/media`

### Command Line Interface (CLI)
You can still use the document converter directly from your terminal:
```bash
# Word to PDF
./run.sh cli report.docx

# PDF to Word
./run.sh cli report.pdf -o converted.docx
```

---

## 🧪 Automated Testing

Run the full verification suite across all tools:
```bash
.venv/bin/python3 test_platform.py
.venv/bin/python3 test_converter.py
```

---

## 📂 Architecture

```
CONVERTFILE/
├── app.py                     # Main Flask web application & REST API
├── cli.py                     # CLI document converter
├── modules/
│   ├── file_converter.py      # DOCX ⇄ PDF engine
│   ├── qr_studio.py           # QR generator (PNG, SVG, Wi-Fi payloads)
│   └── media_converter.py     # yt-dlp & FFmpeg media pipeline
├── templates/
│   ├── base.html              # SaaS layout, header, navbar, footer
│   ├── index.html             # Decide Group Of Solutions dashboard
│   ├── converter.html         # Document Studio interface
│   ├── qr_studio.html         # QR Code Studio with live preview
│   └── media_converter.html   # Media Converter with metadata cards
├── static/
│   └── css/style.css          # Sleek SaaS dark slate theme
├── requirements.txt           # Python dependencies
├── run.sh                     # Platform launcher
├── test_platform.py           # Unified test suite
└── test_converter.py          # Document converter test suite
```
