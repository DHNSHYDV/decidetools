import os
import re
import tempfile
from pathlib import Path
import yt_dlp


class MediaConversionError(Exception):
    """Raised when metadata extraction or media download fails."""
    pass


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unknown"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip()[:100]


def get_media_info(url: str) -> dict:
    """
    Fetch metadata for a given media URL without downloading.
    """
    if not url or not url.strip():
        raise MediaConversionError("URL cannot be empty.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
            if not info:
                raise MediaConversionError("Could not retrieve video information.")

            # If playlist, get first video
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            return {
                "title": info.get("title", "Untitled Video"),
                "uploader": info.get("uploader") or info.get("channel", "Unknown Uploader"),
                "duration": format_duration(info.get("duration", 0)),
                "duration_seconds": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "view_count": f"{info.get('view_count', 0):,}" if info.get("view_count") else "N/A",
                "webpage_url": info.get("webpage_url", url),
            }
    except yt_dlp.utils.DownloadError as e:
        raise MediaConversionError(f"YouTube error: {str(e)}")
    except Exception as e:
        raise MediaConversionError(f"Failed to fetch media details: {str(e)}")


def download_media(url: str, target_format: str = "mp3", quality: str = "320", resolution: str = "best", output_dir: str = None) -> tuple[str, str]:
    """
    Downloads and converts media into MP3 or MP4.
    :param url: Video URL to download.
    :param target_format: 'mp3' or 'mp4'.
    :param quality: Audio bitrate if mp3 (e.g. '320', '192', '128').
    :param resolution: Max video resolution if mp4 (e.g. '1080', '720', '480', '360', 'best').
    :param output_dir: Destination directory.
    :return: Tuple of (absolute_file_path, download_filename).
    """
    if not url or not url.strip():
        raise MediaConversionError("URL cannot be empty.")

    target_format = target_format.lower()
    if target_format not in ["mp3", "mp4"]:
        raise MediaConversionError("Supported target formats are 'mp3' or 'mp4'.")

    dest_dir = output_dir or tempfile.mkdtemp(prefix="media_conv_")
    outtmpl = os.path.join(dest_dir, "%(title).80s.%(ext)s")

    if target_format == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(quality),
                }
            ],
            "noplaylist": True,
        }
    else:  # mp4 video
        if resolution and resolution != "best":
            video_format = f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}][ext=mp4]/best"
        else:
            video_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"

        ydl_opts = {
            "format": video_format,
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
            "noplaylist": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url.strip(), download=True)
            if "entries" in meta and meta["entries"]:
                meta = meta["entries"][0]

            title = sanitize_filename(meta.get("title", "download"))
            expected_ext = target_format
            download_filename = f"{title}.{expected_ext}"

            # Locate converted file in dest_dir
            candidates = list(Path(dest_dir).glob(f"*.{expected_ext}"))
            if not candidates:
                # Fallback check any file generated
                all_files = list(Path(dest_dir).iterdir())
                if all_files:
                    return str(all_files[0]), download_filename
                raise MediaConversionError("Conversion completed but output file could not be located.")

            return str(candidates[0]), download_filename

    except yt_dlp.utils.DownloadError as e:
        raise MediaConversionError(f"Download/Conversion failed: {str(e)}")
    except Exception as e:
        raise MediaConversionError(f"Unexpected media conversion error: {str(e)}")
