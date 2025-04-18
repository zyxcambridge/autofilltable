#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_service.py - Test the simple_bridge.py script with different field types
"""

import json
import os
import tempfile
import subprocess
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
SIMPLE_BRIDGE_PATH = SCRIPT_DIR / "simple_bridge.py"

def test_field(field_text):
    """Test the simple_bridge.py script with a specific field text"""
    print(f"\n=== Testing field: '{field_text}' ===")
    
    # Create a temporary JSON file with context data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        context_data = {
            "selectedText": field_text,
            "appName": "Test App",
            "windowTitle": "Test Window",
            "fieldLabel": field_text,
            "fieldRole": "textField",
            "surroundingText": field_text
        }
        json.dump(context_data, temp_file)
        temp_file_path = temp_file.name
    
    try:
        # Call the simple_bridge.py script with the temporary file
        result = subprocess.run(
            ["python3", str(SIMPLE_BRIDGE_PATH), temp_file_path],
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
    """Test the simple_bridge.py script with different field types"""
    # Test different field types
    test_field("Email")
    test_field("Phone")
    test_field("Name")
    test_field("Address")
    test_field("Education")
    test_field("Work Experience")
    test_field("Skills")
    test_field("Projects")
    test_field("Profile Summary")
    
    # Test in Chinese
    test_field("邮箱")
    test_field("电话")
    test_field("姓名")
    test_field("地址")
    test_field("教育经历")
    test_field("工作经验")
    test_field("技能")
    test_field("项目经验")
    test_field("个人简介")

if __name__ == "__main__":
    main()
