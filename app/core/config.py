"""
Application configuration using environment variables.
"""
import os
from pathlib import Path


class Settings:
    APP_NAME: str = "Instagram Reel Downloader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DOWNLOADS_DIR: Path = BASE_DIR / "downloads"

    # CORS
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "*"
    ).split(",")

    # Download settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
    DOWNLOAD_TIMEOUT_SECONDS: int = int(os.getenv("DOWNLOAD_TIMEOUT", "120"))

    # yt-dlp options
    YDL_FORMAT: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    YDL_QUIET: bool = True
    YDL_NO_WARNINGS: bool = True

    def __init__(self):
        # Ensure downloads directory exists
        self.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
