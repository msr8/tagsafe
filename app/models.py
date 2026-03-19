from app.extensions import db
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




class Finding(db.Model):
    __tablename__ = "findings"
<<<<<<< Updated upstream
    id = db.Column(db.Integer, primary_key=True)
    # scan_run_id = db.Column(db.Integer, db.ForeignKey("scan_runs.id"), nullable=False)
    tool = db.Column(db.String(64))             # bandit | gosec | nodejsscan | cppcheck | semgrep
    rule_id = db.Column(db.String(128))
    severity = db.Column(db.String(32))         # CRITICAL | HIGH | MEDIUM | LOW | INFO
    confidence = db.Column(db.String(32))
    file_path = db.Column(db.String(512))
    line_start = db.Column(db.Integer)
    line_end = db.Column(db.Integer)
    message = db.Column(db.Text)
=======
    id           = db.Column(db.Integer, primary_key=True)
    scan_run_id  = db.Column(db.Integer, db.ForeignKey("scan_runs.id"), nullable=False)
    tool         = db.Column(db.String(64))             # bandit | gosec | nodejsscan | cppcheck | semgrep
    rule_id      = db.Column(db.String(128), nullable=True)
    severity     = db.Column(db.String(32))         # CRITICAL | HIGH | MEDIUM | LOW | WARNING | INFO 
    confidence   = db.Column(db.String(32),  nullable=True) # For tools that provide confidence levels (like bandit)
    file_path    = db.Column(db.String(512))
    line_start   = db.Column(db.Integer,     nullable=True)
    line_end     = db.Column(db.Integer,     nullable=True)
    message      = db.Column(db.Text)
>>>>>>> Stashed changes
    code_snippet = db.Column(db.Text)
    cwe          = db.Column(db.String(64),  nullable=True)
    owasp        = db.Column(db.String(128), nullable=True)

    # scan_run = db.relationship("ScanRun", back_populates="findings")


