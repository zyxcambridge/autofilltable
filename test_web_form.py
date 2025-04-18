#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_web_form.py - Test the web_form_bridge.py script with web form field types
"""

import json
import os
import tempfile
import subprocess
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
WEB_FORM_BRIDGE_PATH = SCRIPT_DIR / "web_form_bridge.py"

def test_field(field_text, app_name="Safari", window_title="Workday - Job Application"):
    """Test the web_form_bridge.py script with a specific field text"""
    print(f"\n=== Testing field: '{field_text}' in {app_name} - {window_title} ===")
    
    # Create a temporary JSON file with context data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        context_data = {
            "selectedText": field_text,
            "appName": app_name,
            "windowTitle": window_title,
            "fieldLabel": field_text,
            "fieldRole": "textField",
            "surroundingText": f"Please enter your {field_text}"
        }
        json.dump(context_data, temp_file)
        temp_file_path = temp_file.name
    
    try:
        # Call the web_form_bridge.py script with the temporary file
        result = subprocess.run(
            ["python3", str(WEB_FORM_BRIDGE_PATH), temp_file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print the result
        print(f"Output:\n{result.stdout}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr}")
    
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def main():
    """Test the web_form_bridge.py script with different field types"""
    # Test Workday form fields
    test_field("First Name", "Safari", "Workday - Job Application")
    test_field("Last Name", "Safari", "Workday - Job Application")
    test_field("Email", "Safari", "Workday - Job Application")
    test_field("Phone", "Safari", "Workday - Job Application")
    test_field("Address", "Safari", "Workday - Job Application")
    test_field("City", "Safari", "Workday - Job Application")
    test_field("State/Province", "Safari", "Workday - Job Application")
    test_field("Postal Code", "Safari", "Workday - Job Application")
    test_field("Country", "Safari", "Workday - Job Application")
    test_field("LinkedIn Profile", "Safari", "Workday - Job Application")
    test_field("Website", "Safari", "Workday - Job Application")
    
    # Test in Chinese
    test_field("姓氏", "Safari", "Workday - 职位申请")
    test_field("名字", "Safari", "Workday - 职位申请")
    test_field("邮箱", "Safari", "Workday - 职位申请")
    test_field("电话", "Safari", "Workday - 职位申请")

if __name__ == "__main__":
    main()
