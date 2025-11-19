"""
Company Context Handler
Simple module to manage company context for personalized agent responses.
"""

import os
import json
import time
from typing import Optional


def get_config_path() -> str:
    """Get the path to the company_context.json file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'company_context.json')


def get_company_context() -> Optional[str]:
    """
    Read company context from config file.
    
    Returns:
        String with company context or None if not set
    """
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('context', None)
    except Exception as e:
        print(f"Error reading company context: {e}")
        return None


def save_company_context(context: str) -> bool:
    """
    Save company context to config file.
    
    Args:
        context: Company context text
    
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()
    
    try:
        config = {
            'context': context.strip(),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving company context: {e}")
        return False


def clear_company_context() -> bool:
    """
    Clear/delete company context.
    
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            os.remove(config_path)
        return True
    except Exception as e:
        print(f"Error clearing company context: {e}")
        return False


def format_context_for_prompt() -> str:
    """
    Format company context for injection into system prompts.
    
    Returns:
        Formatted context string, or empty string if no context
    """
    context = get_company_context()
    
    if not context:
        return ""
    
    return f"""
COMPANY CONTEXT:
{context}

"""
