#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
load_profile.py - Load profile data from default.json and save it in the format expected by the application
"""

import os
import json
import sys
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
PROFILES_DIR = SCRIPT_DIR / "profiles"
DEFAULT_PROFILE_PATH = PROFILES_DIR / "default.json"

def main():
    """Load profile data from default.json and save it directly to the application's data structure"""
    print(f"Loading profile from {DEFAULT_PROFILE_PATH}")
    
    try:
        # Load the default.json file
        with open(DEFAULT_PROFILE_PATH, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        
        # Check if it has the expected structure
        if "version" in profile_data and "data" in profile_data and isinstance(profile_data["data"], dict):
            print("Profile has the expected structure with version and data fields")
            # The data is already in the correct format, no need to modify it
        else:
            print("Profile does not have the expected structure, creating a new one")
            # Create a new profile with the expected structure
            profile_data = {
                "version": "1.0",
                "data": profile_data  # Assume the entire JSON is the data
            }
        
        # Save the profile back to the file
        with open(DEFAULT_PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"Profile saved successfully to {DEFAULT_PROFILE_PATH}")
        return True
    
    except Exception as e:
        print(f"Error processing profile: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
