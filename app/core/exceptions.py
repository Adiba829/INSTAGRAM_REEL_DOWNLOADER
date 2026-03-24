"""
Custom application exceptions for structured error handling.
"""
from fastapi import HTTPException, status


class InstagramDownloaderError(Exception):
    """Base exception for all downloader errors."""
    pass


class InvalidURLError(InstagramDownloaderError):
    """Raised when the provided URL is not a valid Instagram reel URL."""

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INVALID_URL",
                "message": str(self),
                "hint": "Provide a valid Instagram Reel URL (e.g. https://www.instagram.com/reel/XXXX/)",
            },
        )


class PrivateContentError(InstagramDownloaderError):
    """Raised when the reel is from a private account."""

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PRIVATE_CONTENT",
                "message": str(self),
                "hint": "This reel belongs to a private account and cannot be downloaded.",
            },
        )


class DownloadError(InstagramDownloaderError):
    """Raised when the download fails due to network or yt-dlp issues."""

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "DOWNLOAD_FAILED",
                "message": str(self),
                "hint": "Check your network connection or try again later.",
            },
        )


class FileSizeExceededError(InstagramDownloaderError):
    """Raised when the downloaded file exceeds the allowed size limit."""

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "FILE_TOO_LARGE",
                "message": str(self),
                "hint": "The reel file size exceeds the maximum allowed limit.",
            },
        )
