#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
PROFILES_DIR = SCRIPT_DIR / "profiles"
DEFAULT_PROFILE_PATH = PROFILES_DIR / "default.json"

def main():
    """Test loading the profile data"""
    print(f"Loading profile from {DEFAULT_PROFILE_PATH}")
    
    try:
        # Load the default.json file
        with open(DEFAULT_PROFILE_PATH, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        
        # Print the profile data
        print("Profile data loaded successfully")
        print(f"Profile structure: {list(profile_data.keys())}")
        
        if "data" in profile_data:
            data = profile_data["data"]
            print(f"Data structure: {list(data.keys())}")
            
            # Print basic information
            if "basic" in data:
                print("\nBasic Information:")
                for key, value in data["basic"].items():
                    print(f"  {key}: {value}")
            
            # Print education
            if "education" in data and data["education"]:
                print("\nEducation:")
                for edu in data["education"]:
                    print(f"  {edu.get('school', '')} - {edu.get('degree', '')} in {edu.get('major', '')} ({edu.get('period', '')})")
            
            # Print work experience
            if "work_experience" in data and data["work_experience"]:
                print("\nWork Experience:")
                for job in data["work_experience"]:
                    print(f"  {job.get('title', '')} at {job.get('company', '')} ({job.get('period', '')})")
                    if job.get("highlights"):
                        for highlight in job["highlights"]:
                            print(f"    - {highlight}")
        
        return True
    
    except Exception as e:
        print(f"Error processing profile: {e}")
        return False

if __name__ == "__main__":
    main()
