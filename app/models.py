from app.extensions import db
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON
# https://www.digitalocean.com/community/tutorials/how-to-use-one-to-many-database-relationships-with-flask-sqlalchemy




class User(db.Model):
    __tablename__ = 'users'
    user_id       = db.Column(db.Integer,     primary_key=True)
    user_email    = db.Column(db.String(255), nullable=True)
    username      = db.Column(db.String(255), nullable=False) # GitHub username
    pfp_url       = db.Column(db.String(512), nullable=True)  # GitHub profile picture URL
    signed_up     = db.Column(db.DateTime,    nullable=False, server_default=db.func.now())
    # One User has Many Installations
    installations = db.relationship('Installation', backref='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.user_id}')"




class Installation(db.Model):
    __tablename__ = 'installations'

    installation_id   = db.Column(db.BigInteger, nullable=False, primary_key=True)
    issuer_username   = db.Column(db.String(255), nullable=False)
    issuer_pfp_url    = db.Column(db.String(512), nullable=True)
    repos             = db.Column(MutableList.as_mutable(JSON), nullable=True) # [repo-dicts]
    # last_repos_update = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    created_at        = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    # Foreign Key linking back to User
    user_id           = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)



class Finding(db.Model):
    __tablename__ = 'findings'
    id           = db.Column(db.Integer, primary_key=True)
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
    # Foreign Keys to link back to Commits and Pull Requests
    commit_sha   = db.Column(db.String(40), db.ForeignKey('commits.sha'),         nullable=True)
    pr_id        = db.Column(db.BigInteger, db.ForeignKey('pull_requests.pr_id'), nullable=True)



class Commit(db.Model):
    __tablename__ = 'commits'
    sha             = db.Column(db.String(40),   primary_key=True)
    repo_id         = db.Column(db.BigInteger,   nullable=False)
    author_email    = db.Column(db.String(255),  nullable=False)
    author_name     = db.Column(db.String(255),  nullable=False)
    author_username = db.Column(db.String(255),  nullable=True)
    message         = db.Column(db.Text,         nullable=False)
    url             = db.Column(db.String(512),  nullable=False)
    timestamp       = db.Column(db.DateTime,     nullable=False)
    installation_id = db.Column(db.BigInteger,   db.ForeignKey('installations.installation_id'), nullable=False)
    to_scan         = db.Column(db.Boolean,      nullable=False, default=False)
    fully_scanned   = db.Column(db.Boolean,      nullable=False, default=False)
    # One Commit has Many Findings
    findings        = db.relationship('Finding', backref='commit', cascade='all, delete-orphan')



class PullRequest(db.Model):
    __tablename__ = 'pull_requests'
    pr_id           = db.Column(db.BigInteger,   primary_key=True)
    repo_id         = db.Column(db.BigInteger,   nullable=False)
    author_email    = db.Column(db.String(255),  nullable=False)
    author_name     = db.Column(db.String(255),  nullable=False)
    author_username = db.Column(db.String(255),  nullable=True)
    title           = db.Column(db.String(512),  nullable=False)
    description     = db.Column(db.Text,         nullable=True)
    url             = db.Column(db.String(512),  nullable=False)
    timestamp       = db.Column(db.DateTime,     nullable=False)
    installation_id = db.Column(db.BigInteger,   db.ForeignKey('installations.installation_id'), nullable=False)
    # One PullRequest has Many Findings
    findings        = db.relationship('Finding', backref='pull_request', cascade='all, delete-orphan')





