#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
autofill_bridge.py - Bridge between macOS services and Python LLM processing
This script receives context data from the Automator service, processes it using the LLM,
and returns the appropriate text to fill in the form field.
"""

import sys
import json
import os
import logging
from pathlib import Path
import traceback

# Set up logging
logging.basicConfig(
    filename=os.path.expanduser("~/Library/Logs/SmartFill.AI/bridge.log"),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SmartFill.AI Bridge")

# Ensure log directory exists
os.makedirs(os.path.dirname(os.path.expanduser("~/Library/Logs/SmartFill.AI/bridge.log")), exist_ok=True)

# Import from main autofill module
try:
    from autofill import LLMManager, UserProfile, ConfigManager, ContextAnalyzer
    logger.info("Successfully imported autofill modules")
except ImportError as e:
    logger.error(f"Failed to import from autofill module: {e}")
    print(f"Error: Failed to import required modules. See log for details.")
    sys.exit(1)

def process_context(context_data):
    """
    Process the context data and return appropriate text
    
    Args:
        context_data: Dict with context data
        
    Returns:
        String with text to insert
    """
    try:
        logger.info(f"Processing context: {json.dumps(context_data)[:200]}...")
        
        # Initialize components
        config_manager = ConfigManager()
        llm_manager = LLMManager(config_manager)
        context_analyzer = ContextAnalyzer(llm_manager)
        
        # Get active profile
        active_profile_id = config_manager.get("active_profile")
        user_profile = UserProfile(profile_id=active_profile_id)
        
        # Prepare accessibility info for context analysis
        accessibility_info = {
            "app_name": context_data.get("appName", "Unknown"),
            "window_title": context_data.get("windowTitle", "Unknown"),
            "title": context_data.get("fieldLabel", "Unknown"),
            "role": context_data.get("fieldRole", "Unknown"),
            "surrounding_text": context_data.get("surroundingText", ""),
            "selected_text": context_data.get("selectedText", "")
        }
        
        # Analyze context to determine field type
        context_analysis = context_analyzer.analyze_context(accessibility_info)
        logger.info(f"Context analysis result: {context_analysis}")
        
        # Generate appropriate content based on context and user profile
        generated_content = context_analyzer.generate_content(
            context_analysis, 
            user_profile, 
            accessibility_info
        )
        
        logger.info(f"Generated content: {generated_content[:100]}...")
        return generated_content
        
    except Exception as e:
        logger.error(f"Error processing context: {e}", exc_info=True)
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Missing context data file path")
        print("Error: Missing context data file path")
        sys.exit(1)
    
    # Get context JSON from file path
    context_file_path = sys.argv[1]
    
    try:
        # Read context data from file
        with open(context_file_path, 'r') as f:
            context_data = json.load(f)
        
        # Process context and print result (will be captured by Automator)
        result = process_context(context_data)
        print(result)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in context file: {e}")
        print(f"Error: Invalid JSON in context file: {e}")
    except FileNotFoundError as e:
        logger.error(f"Context file not found: {e}")
        print(f"Error: Context file not found: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {str(e)}")
