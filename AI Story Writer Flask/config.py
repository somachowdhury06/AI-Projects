import os


class Config:
    # Prefer reading the OpenAI token from the environment for security.
    # You can set it in PowerShell using:
    #   setx OPENAI_TOKEN "your_openai_key"
    # or for the current session:
    #   $env:OPENAI_TOKEN = "your_openai_key"
    OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN') or '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'  # fallback (remove this and set env var in production)
