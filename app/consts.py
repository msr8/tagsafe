from os import environ
from dotenv import load_dotenv

load_dotenv()

LOGIN_FAIL_REDIRECT  = 'github.login'
POST_LOGIN_REDIRECT  = 'root.page_dashboard'
POST_LOGOUT_REDIRECT = 'root.page_index'
GITHUB_KEY_PATH      = 'github-private-key10-03-2026.pem'

# GOOGLE_CLIENT_ID     = environ.get('GOOGLE_CLIENT_ID')
# GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
GITHUB_CLIENT_ID     = environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = environ.get('GITHUB_CLIENT_SECRET')

MY_EMAIL             = environ.get('MY_EMAIL')
GITHUB_APP_NAME      = environ.get('GITHUB_APP_NAME')
GMAIL_APP_PASSWORD   = environ.get('GMAIL_APP_PASSWORD')

LLM_ENABLED          = environ.get('LLM_ENABLED', 'False').lower() in ['true', '1', 'yes']
LLM_MODEL            = environ.get('LLM_MODEL', 'phi3')
OLLAMA_PORT          = environ.get('OLLAMA_PORT', '11434')