import sys
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sty import fg, bg, ef, rs

# Centralized loguru logger configuration
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    # format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG"
)

logger.info('Loading extensions...')

db   = SQLAlchemy()
sess = Session()
