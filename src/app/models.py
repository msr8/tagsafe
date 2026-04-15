from app.extensions import db
from sqlalchemy.ext.mutable import MutableList, MutableDict
from sqlalchemy.dialects.postgresql import JSON
# https://www.digitalocean.com/community/tutorials/how-to-use-one-to-many-database-relationships-with-flask-sqlalchemy




class User(db.Model):
    __tablename__ = 'users'
    user_id       = db.Column(db.Integer,     primary_key=True)
    user_email    = db.Column(db.String(255), nullable=True)
    username      = db.Column(db.String(255), nullable=False) # GitHub username
    pfp_url       = db.Column(db.String(512), nullable=True)  # GitHub profile picture URL
    signed_up     = db.Column(db.DateTime,    nullable=False, server_default=db.func.now())
    preference    = db.Column(MutableDict.as_mutable(JSON), nullable=True) # {'email': '...', 'severity_threshold': 2} # Basically when to send email. Always -> 0, >= Warning -> 1, >= Medium -> 2, >= High -> 3, Only Critical -> 4, Never -> 99
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
    # One Installation has Many Commits
    commits           = db.relationship('Commit', backref='installation', lazy=True, cascade='all, delete-orphan')



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
    timestamp    = db.Column(db.DateTime,    nullable=False, server_default=db.func.now())
    # Foreign Keys to link back to Commits and Pull Requests
    commit_sha   = db.Column(db.String(40), db.ForeignKey('commits.sha'),         nullable=True)
    pr_id        = db.Column(db.BigInteger, db.ForeignKey('pull_requests.pr_id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tool': self.tool,
            'rule_id': self.rule_id,
            'severity': self.severity,
            'confidence': self.confidence,
            'file_path': self.file_path,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'message': self.message,
            'code_snippet': self.code_snippet,
            'cwe': self.cwe,
            'owasp': self.owasp,
            'commit_sha': self.commit_sha,
            'pr_id': self.pr_id
        }



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
    findings        = db.relationship('Finding', backref='commit', lazy=True, cascade='all, delete-orphan')



class PullRequest(db.Model):
    __tablename__ = 'pull_requests'
    pr_id           = db.Column(db.BigInteger,   primary_key=True)
    repo_id         = db.Column(db.BigInteger,   nullable=False)
    author_email    = db.Column(db.String(255))
    author_name     = db.Column(db.String(255))
    author_username = db.Column(db.String(255))
    title           = db.Column(db.String(512),  nullable=False)
    description     = db.Column(db.Text)
    html_url        = db.Column(db.String(512),  nullable=False)
    api_url         = db.Column(db.String(512),  nullable=False)
    timestamp       = db.Column(db.DateTime,     nullable=False)
    installation_id = db.Column(db.BigInteger,   db.ForeignKey('installations.installation_id'), nullable=False)
    fully_scanned   = db.Column(db.Boolean,      nullable=False, default=False)
    # One PullRequest has Many Findings
    findings        = db.relationship('Finding', backref='pull_request', lazy=True, cascade='all, delete-orphan')


