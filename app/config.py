"""Configuration settings for Propongo."""

import os

from .models import DATA_ROOT


def _load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (no overwrite).

    Dependency-free alternative to python-dotenv. Missing files are ignored.
    """
    if not os.path.exists(path):
        return
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


_load_dotenv()


class Config:
    """Application configuration."""
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Security
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
    
    # File paths
    DATA_DIR = DATA_ROOT
    PROPOSALS_DIR = os.path.join(DATA_DIR, 'proposals')
    EXPORTS_DIR = os.path.join(DATA_DIR, 'exports')
    MAPS_DIR = os.path.join(DATA_DIR, 'maps')
    MAP_CACHE_DIR = os.path.join(DATA_DIR, 'map_cache')

    # GeoLibre embed base URL. Points at the hosted app by default; set to a
    # self-hosted instance (e.g. http://localhost:8080) when running one.
    GEOLIBRE_EMBED_URL = os.environ.get('GEOLIBRE_EMBED_URL', 'https://web.geolibre.app')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Outbound email (SMTP) for password reset
    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASS = os.environ.get('SMTP_PASS', '')
    SMTP_FROM = os.environ.get('SMTP_FROM', '') or os.environ.get('SMTP_USER', '')

    # LLM-as-judge section scoring (see app/judge.py). The free default model
    # runs against a local Ollama server - no key needed, nothing leaves the
    # machine. ANTHROPIC_API_KEY only gates the paid Sonnet/Opus options.
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1')


# Error messages
ERROR_MESSAGES = {
    'PROPOSAL_NOT_FOUND': {'error': 'Proposal not found'},
    'SECTION_NOT_FOUND': {'error': 'Section not found'},
    'TASK_NOT_FOUND': {'error': 'Task not found'},
    'BUDGET_ITEM_NOT_FOUND': {'error': 'Budget item not found'},
    'NO_DATA': {'error': 'No data provided'},
    'NO_FILE': {'error': 'No file provided'},
    'INVALID_FILE_TYPE': {'error': 'Invalid file type'},
    'INVALID_NUMERIC': {'error': 'Invalid numeric value'},
    'EXCEL_NOT_INSTALLED': {'error': 'Excel support not installed. Install pandas and openpyxl.'},
    'EXCEL_INVALID_FILE': {'error': 'Invalid Excel file'},
    'EXCEL_PROCESSING_ERROR': {'error': 'Failed to process Excel file'},
    'SECTION_KEY_NOT_FOUND': {'error': 'Section not found'},
}
