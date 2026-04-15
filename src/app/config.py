# from cachelib.file import FileSystemCache
from app.extensions import db


class Config:
    DEBUG = True
    THREADED = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    # Session Config
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY = db



