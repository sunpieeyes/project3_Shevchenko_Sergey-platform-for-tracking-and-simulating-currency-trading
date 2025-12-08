import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_PATH = Path("logs/actions.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S'
)

handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
handler.setFormatter(formatter)

logger = logging.getLogger("valutrade_hub")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
