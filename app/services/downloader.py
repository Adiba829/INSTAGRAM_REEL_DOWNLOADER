"""
Instagram Reel download service using yt-dlp.
Handles extraction, download, file management, and error mapping.
"""
import re
import uuid
import asyncio
from pathlib import Path
from typing import Tuple

import yt_dlp
from yt_dlp.utils import (
    DownloadError as YtdlpDownloadError,
    ExtractorError,
    GeoRestrictedError,
)

from app.core.config import settings
from app.core.exceptions import (
    InstagramDownloaderError,
    DownloadError,
    FileSizeExceededError,
    InvalidURLError,
    PrivateContentError,
)
from app.core.logging import logger


# Patterns that indicate a private/login-required error
_PRIVATE_PATTERNS = re.compile(
    r"login|private|not available|requires authentication|checkpoint",
    re.IGNORECASE,
)


def _build_ydl_opts(output_template: str) -> dict:
    """Build yt-dlp options dictionary."""
    return {
        "format": settings.YDL_FORMAT,
        "outtmpl": output_template,
        "quiet": settings.YDL_QUIET,
        "no_warnings": settings.YDL_NO_WARNINGS,
        "noplaylist": True,
        "noprogress": True,
        "socket_timeout": settings.DOWNLOAD_TIMEOUT_SECONDS,
        "retries": 3,
        "extractor_retries": 2,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
        # Merge video+audio into single mp4
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }


def _map_ydl_error(error: Exception, url: str) -> InstagramDownloaderError:
    """Map yt-dlp exceptions to our custom domain exceptions."""
    msg = str(error).lower()

    if _PRIVATE_PATTERNS.search(msg):
        return PrivateContentError(
            f"The reel at '{url}' is from a private account or requires login."
        )

    if isinstance(error, GeoRestrictedError):
        return DownloadError(
            "This reel is geo-restricted and cannot be downloaded from this server."
        )

    if isinstance(error, ExtractorError):
        return InvalidURLError(
            f"Could not extract reel info from '{url}'. The URL may be invalid or expired."
        )

    return DownloadError(f"Download failed: {str(error)}")


def _find_downloaded_file(download_dir: Path, session_id: str) -> Path:
    """Find the file that was downloaded for this session."""
    candidates = list(download_dir.glob(f"{session_id}*"))
    if not candidates:
        raise DownloadError("Download completed but output file was not found.")
    # Prefer mp4
    mp4_files = [f for f in candidates if f.suffix == ".mp4"]
    return mp4_files[0] if mp4_files else candidates[0]


def _check_file_size(file_path: Path) -> None:
    """Raise FileSizeExceededError if file exceeds configured limit."""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        file_path.unlink(missing_ok=True)
        raise FileSizeExceededError(
            f"File size ({size_mb:.1f} MB) exceeds the maximum allowed "
            f"size of {settings.MAX_FILE_SIZE_MB} MB."
        )


def _sync_download(url: str) -> Tuple[Path, str]:
    """
    Synchronous yt-dlp download. Intended to be run in a thread pool.

    Returns:
        Tuple of (file_path, original_title)
    """
    session_id = uuid.uuid4().hex
    output_template = str(settings.DOWNLOADS_DIR / f"{session_id}.%(ext)s")
    ydl_opts = _build_ydl_opts(output_template)

    logger.info("Starting download | session=%s url=%s", session_id, url)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title: str = info.get("title", "instagram_reel") if info else "instagram_reel"
    except (YtdlpDownloadError, ExtractorError, GeoRestrictedError) as exc:
        logger.warning("yt-dlp error | session=%s error=%s", session_id, exc)
        raise _map_ydl_error(exc, url) from exc
    except Exception as exc:
        logger.exception("Unexpected error during download | session=%s", session_id)
        raise DownloadError(f"Unexpected error: {exc}") from exc

    file_path = _find_downloaded_file(settings.DOWNLOADS_DIR, session_id)
    logger.info(
        "Download complete | session=%s file=%s size_bytes=%d",
        session_id,
        file_path.name,
        file_path.stat().st_size,
    )

    _check_file_size(file_path)

    return file_path, title


async def download_reel(url: str) -> Tuple[Path, str]:
    """
    Asynchronous entry point for downloading an Instagram reel.

    Runs the blocking yt-dlp call in a thread pool executor so the
    FastAPI event loop is not blocked.

    Args:
        url: Validated Instagram reel URL.

    Returns:
        Tuple of (Path to downloaded file, video title).

    Raises:
        InvalidURLError, PrivateContentError, DownloadError, FileSizeExceededError
    """
    loop = asyncio.get_running_loop()
    file_path, title = await loop.run_in_executor(None, _sync_download, url)
    return file_path, title


def cleanup_file(file_path: Path) -> None:
    """Delete a downloaded file after it has been served."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info("Cleaned up file | path=%s", file_path)
    except OSError as exc:
        logger.warning("Failed to clean up file | path=%s error=%s", file_path, exc)
