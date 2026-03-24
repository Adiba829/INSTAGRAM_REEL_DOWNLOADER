"""
Route definitions for the Instagram Reel Downloader API.
"""
import re

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.exceptions import (
    DownloadError,
    FileSizeExceededError,
    InstagramDownloaderError,
    InvalidURLError,
    PrivateContentError,
)
from app.core.logging import logger
from app.models.schemas import DownloadRequest, HealthResponse
from app.services.downloader import cleanup_file, download_reel

router = APIRouter()

# Characters that are unsafe in Content-Disposition filenames
_UNSAFE_CHARS = re.compile(r'[^\w\-. ]')


def _safe_filename(title: str, suffix: str = ".mp4") -> str:
    """Convert a raw video title to a safe ASCII filename."""
    sanitized = _UNSAFE_CHARS.sub("_", title)
    sanitized = sanitized.strip("_. ")[:80] or "instagram_reel"
    return f"{sanitized}{suffix}"


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Liveness probe — confirms the service is running."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        service=settings.APP_NAME,
    )


@router.post("/download", tags=["Downloader"])
async def download_instagram_reel(
    payload: DownloadRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> FileResponse:
    """
    Download an Instagram Reel and return it as a streaming MP4 file.

    - **url**: Full Instagram Reel URL (e.g. `https://www.instagram.com/reel/XYZ/`)

    The file is automatically deleted from the server after it is sent to the client.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info("Download request | ip=%s url=%s", client_ip, payload.url)

    try:
        file_path, title = await download_reel(payload.url)
    except InvalidURLError as exc:
        raise exc.to_http_exception()
    except PrivateContentError as exc:
        raise exc.to_http_exception()
    except FileSizeExceededError as exc:
        raise exc.to_http_exception()
    except DownloadError as exc:
        raise exc.to_http_exception()
    except InstagramDownloaderError as exc:
        # Generic fallback for any other domain exception
        raise DownloadError(str(exc)).to_http_exception()

    filename = _safe_filename(title, suffix=file_path.suffix or ".mp4")

    # Schedule file deletion after response is fully sent
    background_tasks.add_task(cleanup_file, file_path)

    logger.info(
        "Serving file | ip=%s filename=%s size_bytes=%d",
        client_ip,
        filename,
        file_path.stat().st_size,
    )

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename,
        headers={
            # Inline playback hint; browser can override with download attr
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
