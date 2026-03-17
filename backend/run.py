"""
Backend startup script.
"""

import uvicorn

from app.config import settings
from app.logging_config import configure_logging


if __name__ == "__main__":
    configure_logging()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
        log_config=None,
    )