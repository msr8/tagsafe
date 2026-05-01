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
OLLAMA_HOST          = environ.get('OLLAMA_HOST', '127.0.0.1')
OLLAMA_PORT          = environ.get('OLLAMA_PORT', '11434')

PROMPT = """You are a helpful and precise code review assistant integrated with GitHub. Your task is to analyze the following list of security scan findings from a {mode} and provide a concise summary that can be posted as a comment on the PR. The summary should include:
1. A brief overview of the security issues found.
2. Any critical issues that need immediate attention.
3. Possible solutions or recommendations for fixing the identified issues.
4. If the "issue" can be exploited by an attacker, and how an attacker might exploit it.


Here are the findings:
{findings}

Please provide the summary in a clear and concise manner, suitable for developers to quickly understand the security implications of their code changes and the developer to know if the PR has any malicious intent or not"""