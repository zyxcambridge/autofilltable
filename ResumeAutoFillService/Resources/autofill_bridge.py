#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
autofill_bridge.py - Bridge between Swift service and Python LLM processing
This script receives context data from the Swift service, processes it using the LLM,
and returns the appropriate text to fill in the form field.
"""

import sys
import json
import os
import logging
from pathlib import Path

# Set up paths to find the main autofill module
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent.parent))  # Add parent directory to path

# Import from main autofill module
try:
    from autofill import LLMManager, UserProfile, ConfigManager, ContextAnalyzer
except ImportError:
    logging.error("Failed to import from autofill module")
    sys.exit(1)

def process_context(context_json):
    """
    Process the context data from Swift and return appropriate text
    
    Args:
        context_json: JSON string with context data
        
    Returns:
        String with text to insert
    """
    try:
        # Parse context data
        context = json.loads(context_json)
        
        # Initialize components
        config_manager = ConfigManager()
        llm_manager = LLMManager(config_manager)
        context_analyzer = ContextAnalyzer(llm_manager)
        
        # Get active profile
        active_profile_id = config_manager.get("active_profile")
        user_profile = UserProfile(profile_id=active_profile_id)
        
        # Prepare accessibility info for context analysis
        accessibility_info = {
            "app_name": context.get("appName", "Unknown"),
            "window_title": context.get("windowTitle", "Unknown"),
            "title": context.get("fieldLabel", "Unknown"),
            "role": context.get("fieldRole", "Unknown"),
            "surrounding_text": context.get("surroundingText", ""),
            "selected_text": context.get("selectedText", "")
        }
        
        # Analyze context to determine field type
        context_analysis = context_analyzer.analyze_context(accessibility_info)
        
        # Generate appropriate content based on context and user profile
        generated_content = context_analyzer.generate_content(
            context_analysis, 
            user_profile, 
            accessibility_info
        )
        
        return generated_content
        
    except Exception as e:
        logging.error(f"Error processing context: {e}", exc_info=True)
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing context data")
        sys.exit(1)
    
    # Get context JSON from command line argument
    context_json = sys.argv[1]
    
    # Process context and print result (will be captured by Swift)
    result = process_context(context_json)
    print(result)
