"""Configuration settings for Propongo2."""

import os


class Config:
    """Application configuration."""
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Security
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
    
    # File paths
    DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Propongo2")
    PROPOSALS_DIR = os.path.join(DATA_DIR, 'proposals')
    EXPORTS_DIR = os.path.join(DATA_DIR, 'exports')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


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
}
