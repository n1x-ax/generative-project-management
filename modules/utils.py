import json
import logging
import os
import pathlib
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generative_pm.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GenProjectManagement")

# Load environment variables from .env file if present
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Path to prompts directory
PROMPTS_DIR = pathlib.Path(__file__).parent.parent / "prompts"

def load_prompt(filename):
    """Load a prompt from a text file in the prompts directory."""
    logger.debug(f"Loading prompt from {filename}")
    with open(PROMPTS_DIR / filename, 'r') as f:
        return f.read()

def safe_format(template, replacement_dict):
    """
    Safely format a string template with replacement values.
    
    Args:
        template (str): Template string with {placeholders}
        replacement_dict (dict): Dictionary of replacements where keys are the placeholders
            and values are the replacement values
    
    Returns:
        str: Formatted string with replacements
    """
    if not isinstance(template, str):
        logger.warning("Template is not a string, returning as is")
        return template
        
    if not isinstance(replacement_dict, dict):
        logger.warning("Replacement dict is not a dictionary, returning template as is")
        return template
        
    result = template
    for placeholder, value in replacement_dict.items():
        if not isinstance(placeholder, str):
            logger.warning(f"Placeholder {placeholder} is not a string, skipping")
            continue
            
        if value is None:
            value = ""
        elif not isinstance(value, str):
            value = str(value)
            
        result = result.replace(placeholder, value)
    
    return result

def log_parsed_json(step_name, response_json, parsed_model=None):
    """Helper function to log parsed JSON for debugging"""
    try:
        if parsed_model:
            logger.info(f"JSON validation successful for {step_name}")
            logger.debug(f"{step_name} parsed model: {parsed_model.model_dump_json()}")
        else:
            # Truncate the response for logging but ensure it's valid JSON first
            try:
                if isinstance(response_json, str):
                    # Test if it's valid JSON
                    try:
                        json.loads(response_json)
                        is_valid = True
                    except json.JSONDecodeError:
                        is_valid = False
                        
                    if not is_valid:
                        logger.error(f"Invalid JSON in {step_name} response. First 100 chars: {response_json[:100]}...")
                        return
                        
                # Now that we know it's valid or already parsed, log it
                if isinstance(response_json, str):
                    truncated = response_json[:200] + "..." if len(response_json) > 200 else response_json
                else:
                    truncated_json = json.dumps(response_json)
                    truncated = truncated_json[:200] + "..." if len(truncated_json) > 200 else truncated_json
                    
                logger.info(f"JSON response for {step_name}: {truncated}")
            except Exception as e:
                logger.error(f"Error processing JSON in {step_name}: {str(e)}")
                logger.error(f"First 100 chars of response: {str(response_json)[:100]}...")
    except Exception as e:
        logger.error(f"Error logging JSON for {step_name}: {str(e)}")
        if isinstance(response_json, str):
            logger.error(f"Response content preview: {response_json[:100]}...") 