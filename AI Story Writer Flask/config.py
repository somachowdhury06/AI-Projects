import os


class Config:
    # Prefer reading the OpenAI token from the environment for security.
    # You can set it in PowerShell using:
    #   setx OPENAI_TOKEN "your_openai_key"
    # or for the current session:
    #   $env:OPENAI_TOKEN = "your_openai_key"
    OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN') or ''  # fallback (remove this and set env var in production)
 
