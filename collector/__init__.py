"""AI Radar Collector package."""

from pathlib import Path

from dotenv import load_dotenv

# The modules read the environment at import time, so .env has to be loaded here,
# before anything reads it. Variables already set in the shell always win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
