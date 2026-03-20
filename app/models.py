from app.extensions import db
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON
# https://www.digitalocean.com/community/tutorials/how-to-use-one-to-many-database-relationships-with-flask-sqlalchemy




class User(db.Model):
    __tablename__ = 'users'

    email     = db.Column(db.String(255), primary_key=True)
    username  = db.Column(db.String(255), nullable=False)
    password  = db.Column(db.String(60),  nullable=True) # Bcrypt "blowfish algo" salted hash (by default it is 60 characters long)
    signed_up = db.Column(db.DateTime,    nullable=False, server_default=db.func.now())


    def __repr__(self):
        return f"User('{self.email}')"




class Usernames(db.Model):
    '''Exists only for O(1) lookup of usernames'''
    __tablename__ = 'usernames'

    username = db.Column(db.String(255), primary_key=True)
    email    = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"Usernames('{self.username}')"




class Installation(db.Model):
    __tablename__ = 'installations'

    installation_id   = db.Column(db.BigInteger, nullable=False, primary_key=True)
    issuer_username   = db.Column(db.String(255), nullable=False)
    issuer_pfp        = db.Column(db.String(512), nullable=True)
    repos             = db.Column(MutableList.as_mutable(JSON), nullable=True) # [repo-dicts]
    # last_repos_update = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    created_at        = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    is_active         = db.Column(db.Boolean, nullable=False, default=True)



class Finding(db.Model):
    __tablename__ = "findings"
    id           = db.Column(db.Integer, primary_key=True)
    commit       = db.Column(db.Integer, db.ForeignKey('commits.id'), nullable=False)
    tool         = db.Column(db.String(64))             # bandit | gosec | nodejsscan | cppcheck | semgrep
    rule_id      = db.Column(db.String(128), nullable=True)
    severity     = db.Column(db.String(32))         # CRITICAL | HIGH | MEDIUM | LOW | WARNING | INFO 
    confidence   = db.Column(db.String(32),  nullable=True) # For tools that provide confidence levels (like bandit)
    file_path    = db.Column(db.String(512))
    line_start   = db.Column(db.Integer,     nullable=True)
    line_end     = db.Column(db.Integer,     nullable=True)
    message      = db.Column(db.Text)
    code_snippet = db.Column(db.Text)
    cwe          = db.Column(db.String(64),  nullable=True)
    owasp        = db.Column(db.String(128), nullable=True)


class Commit(db.Model):
    __tablename__ = "commits"
    id              = db.Column(db.Integer, primary_key=True)
    repo_id         = db.Column(db.BigInteger, nullable=False)
    author_email    = db.Column(db.String(255), nullable=False)
    author_name     = db.Column(db.String(255), nullable=False)
    author_username = db.Column(db.String(255), nullable=True)
    message         = db.Column(db.Text, nullable=False)
    url             = db.Column(db.String(512), nullable=False)
    timestamp       = db.Column(db.DateTime, nullable=False)
    installation    = db.Column(db.BigInteger, db.ForeignKey('installations.installation_id'), nullable=False)
    findings        = db.relationship('Finding', backref='commit', cascade='all, delete-orphan')

    # scan_run = db.relationship("ScanRun", back_populates="findings")





