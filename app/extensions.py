from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sty import fg, bg, ef, rs


print(ef.bold + fg.green + 'Loading extensions...' + rs.all)

db   = SQLAlchemy()
sess = Session()
