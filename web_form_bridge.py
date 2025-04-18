#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
web_form_bridge.py - A specialized bridge script for handling web forms
"""

import sys
import json
import os
import subprocess
from pathlib import Path
import time
import re

# Set up paths
SCRIPT_DIR = Path(__file__).parent
PROFILES_DIR = SCRIPT_DIR / "profiles"
DEFAULT_PROFILE_PATH = PROFILES_DIR / "default.json"

def get_profile_data():
    """Load the profile data directly from the default.json file"""
    try:
        with open(DEFAULT_PROFILE_PATH, "r", encoding="utf-8") as f:
            profile_json = json.load(f)
            
        if "data" in profile_json and isinstance(profile_json["data"], dict):
            return profile_json["data"]
        else:
            return {}
    except Exception as e:
        print(f"Error loading profile data: {e}")
        return {}

def analyze_field_type(field_text, surrounding_text="", app_name="", window_title=""):
    """Advanced field type analysis based on the text and context"""
    field_text_lower = field_text.lower() if field_text else ""
    surrounding_text_lower = surrounding_text.lower() if surrounding_text else ""
    window_title_lower = window_title.lower() if window_title else ""
    
    # Check if we're in a job application context
    job_application_context = any(kw in window_title_lower or kw in surrounding_text_lower 
                                for kw in ["apply", "application", "job", "career", "resume", 
                                           "workday", "linkedin", "indeed"])
    
    # Special handling for Workday forms
    if "workday" in window_title_lower or "workday" in app_name.lower():
        # Common Workday form fields
        if any(kw in field_text_lower for kw in ["first name", "given name", "名字"]):
            return "First Name"
        elif any(kw in field_text_lower for kw in ["last name", "family name", "surname", "姓氏"]):
            return "Last Name"
        elif any(kw in field_text_lower for kw in ["email", "e-mail", "邮箱", "电子邮件"]):
            return "Email Address"
        elif any(kw in field_text_lower for kw in ["phone", "mobile", "telephone", "电话", "手机"]):
            return "Phone Number"
        elif any(kw in field_text_lower for kw in ["address", "street", "地址", "街道"]):
            return "Street Address"
        elif any(kw in field_text_lower for kw in ["city", "城市"]):
            return "City"
        elif any(kw in field_text_lower for kw in ["state", "province", "省", "州"]):
            return "State/Province"
        elif any(kw in field_text_lower for kw in ["zip", "postal", "邮编", "邮政编码"]):
            return "Zip/Postal Code"
        elif any(kw in field_text_lower for kw in ["country", "国家"]):
            return "Country"
        elif any(kw in field_text_lower for kw in ["linkedin", "领英"]):
            return "LinkedIn URL"
        elif any(kw in field_text_lower for kw in ["website", "portfolio", "网站", "作品集"]):
            return "Website"
        elif any(kw in field_text_lower for kw in ["education", "school", "university", "college", "学历", "教育", "学校", "大学"]):
            return "Education"
        elif any(kw in field_text_lower for kw in ["experience", "work", "employment", "工作经历", "工作经验", "职业经历"]):
            return "Work Experience"
        elif any(kw in field_text_lower for kw in ["skills", "abilities", "技能", "能力", "专长"]):
            return "Skills"
    
    # Basic mapping of field types
    if any(kw in field_text_lower for kw in ["email", "e-mail", "邮箱", "电子邮件"]):
        return "Email Address"
    elif any(kw in field_text_lower for kw in ["phone", "mobile", "telephone", "电话", "手机", "联系方式", "联系电话"]):
        return "Phone Number"
    elif any(kw in field_text_lower for kw in ["first name", "given name", "名字"]):
        return "First Name"
    elif any(kw in field_text_lower for kw in ["last name", "family name", "surname", "姓氏"]):
        return "Last Name"
    elif any(kw in field_text_lower for kw in ["full name", "name", "姓名", "全名"]) and not any(kw in field_text_lower for kw in ["first", "last", "family", "given"]):
        return "Full Name"
    elif any(kw in field_text_lower for kw in ["address", "street", "地址", "街道", "住址"]):
        return "Street Address"
    elif any(kw in field_text_lower for kw in ["city", "城市"]):
        return "City"
    elif any(kw in field_text_lower for kw in ["state", "province", "省", "州"]):
        return "State/Province"
    elif any(kw in field_text_lower for kw in ["zip", "postal", "邮编", "邮政编码"]):
        return "Zip/Postal Code"
    elif any(kw in field_text_lower for kw in ["country", "国家"]):
        return "Country"
    elif any(kw in field_text_lower for kw in ["linkedin", "领英"]):
        return "LinkedIn URL"
    elif any(kw in field_text_lower for kw in ["website", "portfolio", "网站", "作品集"]):
        return "Website"
    elif any(kw in field_text_lower for kw in ["education", "school", "university", "college", "学历", "教育", "学校", "大学"]):
        return "Education"
    elif any(kw in field_text_lower for kw in ["experience", "work", "employment", "工作经历", "工作经验", "职业经历"]):
        return "Work Experience"
    elif any(kw in field_text_lower for kw in ["skills", "abilities", "技能", "能力", "专长"]):
        return "Skills"
    elif any(kw in field_text_lower for kw in ["projects", "项目", "项目经验"]):
        return "Projects"
    elif any(kw in field_text_lower for kw in ["summary", "profile", "objective", "简介", "自我介绍", "个人简介", "求职目标"]):
        return "Profile Summary"
    else:
        return "Unknown"

def get_field_value(profile_data, field_type):
    """Get the appropriate value from the profile data based on the field type"""
    if field_type == "Email Address" and "basic" in profile_data:
        return profile_data["basic"].get("email", "")
    elif field_type == "Phone Number" and "basic" in profile_data:
        return profile_data["basic"].get("phone", "")
    elif field_type == "Full Name" and "basic" in profile_data:
        return profile_data["basic"].get("name", "")
    elif field_type == "First Name" and "basic" in profile_data:
        full_name = profile_data["basic"].get("name", "")
        # For Chinese names, last name is typically the first character
        if re.search(r'[\u4e00-\u9fff]', full_name):  # Contains Chinese characters
            return full_name[1:] if len(full_name) > 1 else full_name
        else:
            # For Western names, first name is before the first space
            return full_name.split(" ")[0] if " " in full_name else full_name
    elif field_type == "Last Name" and "basic" in profile_data:
        full_name = profile_data["basic"].get("name", "")
        # For Chinese names, last name is typically the first character
        if re.search(r'[\u4e00-\u9fff]', full_name):  # Contains Chinese characters
            return full_name[0:1]
        else:
            # For Western names, last name is after the last space
            return full_name.split(" ")[-1] if " " in full_name else ""
    elif field_type == "Street Address" and "basic" in profile_data:
        return profile_data["basic"].get("location", "")
    elif field_type == "City" and "basic" in profile_data:
        location = profile_data["basic"].get("location", "")
        # Try to extract city from location
        if "," in location:
            return location.split(",")[0].strip()
        else:
            return location
    elif field_type == "State/Province" and "basic" in profile_data:
        location = profile_data["basic"].get("location", "")
        # Try to extract state from location
        if "," in location and len(location.split(",")) > 1:
            return location.split(",")[1].strip()
        else:
            return ""
    elif field_type == "Country" and "basic" in profile_data:
        location = profile_data["basic"].get("location", "")
        # Try to extract country from location
        if "," in location and len(location.split(",")) > 2:
            return location.split(",")[2].strip()
        else:
            return "China"  # Default to China based on the profile
    elif field_type == "LinkedIn URL" and "portfolio" in profile_data:
        # Try to find LinkedIn URL in portfolio
        if "personal_website" in profile_data["portfolio"]:
            website = profile_data["portfolio"]["personal_website"]
            if "linkedin.com" in website:
                return website
        # Check projects for LinkedIn
        if "projects" in profile_data["portfolio"]:
            for project in profile_data["portfolio"]["projects"]:
                if "url" in project and "linkedin.com" in project["url"]:
                    return project["url"]
        return ""
    elif field_type == "Website" and "portfolio" in profile_data:
        return profile_data["portfolio"].get("personal_website", "")
    elif field_type == "Education" and "education" in profile_data:
        education_data = profile_data["education"]
        if education_data and isinstance(education_data, list):
            formatted_education = []
            for edu in education_data:
                entry = f"{edu.get('school', '')}, {edu.get('degree', '')} in {edu.get('major', '')} ({edu.get('period', '')})"
                formatted_education.append(entry)
            return "\n".join(formatted_education)
        return ""
    elif field_type == "Work Experience" and "work_experience" in profile_data:
        work_data = profile_data["work_experience"]
        if work_data and isinstance(work_data, list):
            formatted_work = []
            for job in work_data:
                entry = f"{job.get('title', '')} at {job.get('company', '')} ({job.get('period', '')})\n"
                highlights = job.get("highlights", [])
                if highlights:
                    entry += "\n".join([f"• {h}" for h in highlights])
                formatted_work.append(entry)
            return "\n\n".join(formatted_work)
        return ""
    elif field_type == "Skills" and "skills" in profile_data:
        skills_data = profile_data["skills"]
        if skills_data and isinstance(skills_data, dict):
            formatted_skills = []
            for category, skills_list in skills_data.items():
                if isinstance(skills_list, list) and skills_list:
                    formatted_skills.append(f"{category.replace('_', ' ').title()}: {', '.join(skills_list)}")
            return "\n".join(formatted_skills)
        return ""
    elif field_type == "Projects" and "projects" in profile_data:
        projects_data = profile_data["projects"]
        if projects_data and isinstance(projects_data, list):
            formatted_projects = []
            for project in projects_data:
                entry = f"{project.get('name', '')}\n"
                if "description" in project:
                    entry += f"{project.get('description', '')}\n"
                if "achievement" in project:
                    entry += f"Achievement: {project.get('achievement', '')}\n"
                highlights = project.get("highlights", [])
                if highlights:
                    entry += "\n".join([f"• {h}" for h in highlights])
                formatted_projects.append(entry)
            return "\n\n".join(formatted_projects)
        return ""
    elif field_type == "Profile Summary" and "basic" in profile_data:
        # Generate a profile summary from basic info and most recent experience
        basic_info = profile_data.get("basic", {})
        work_exp = profile_data.get("work_experience", [])
        skills_data = profile_data.get("skills", {})
        
        name = basic_info.get("name", "")
        location = basic_info.get("location", "")
        
        # Get most recent job title and company
        recent_title = ""
        recent_company = ""
        if work_exp and len(work_exp) > 0:
            recent_title = work_exp[0].get("title", "")
            recent_company = work_exp[0].get("company", "")
        
        # Get key skills
        key_skills = []
        for category, skills_list in skills_data.items():
            if isinstance(skills_list, list) and skills_list:
                key_skills.extend(skills_list[:3])  # Take up to 3 skills from each category
        
        # Format the summary
        summary_parts = []
        if name:
            summary_parts.append(name)
        if recent_title and recent_company:
            summary_parts.append(f"{recent_title} at {recent_company}")
        elif recent_title:
            summary_parts.append(recent_title)
        if location:
            summary_parts.append(f"Based in {location}")
        if key_skills:
            summary_parts.append(f"Skilled in {', '.join(key_skills[:5])}")
        
        return ". ".join(summary_parts)
    elif field_type == "Zip/Postal Code":
        # Default postal code for Shanghai
        return "200000"
    else:
        return ""

def insert_text_with_applescript(text):
    """Use AppleScript to insert text at the current cursor position"""
    # Escape double quotes in the text
    escaped_text = text.replace('"', '\\"')
    
    # Create AppleScript to insert text
    applescript = f'''
    tell application "System Events"
        set frontApp to name of first process whose frontmost is true
        
        # Different handling based on the application
        if frontApp is "Safari" or frontApp is "Google Chrome" or frontApp is "Firefox" then
            # For web browsers
            keystroke "a" using command down
            delay 0.1
            keystroke "{escaped_text}"
        else
            # For other applications
            keystroke "{escaped_text}"
        end if
    end tell
    '''
    
    # Run the AppleScript
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e}")
        return False

def process_context(context_data):
    """Process the context data and return appropriate text"""
    try:
        # Get the selected text and context from the context data
        selected_text = context_data.get("selectedText", "")
        surrounding_text = context_data.get("surroundingText", "")
        app_name = context_data.get("appName", "")
        window_title = context_data.get("windowTitle", "")
        
        print(f"Selected text: {selected_text}")
        print(f"App: {app_name}")
        print(f"Window: {window_title}")
        
        # Load the profile data
        profile_data = get_profile_data()
        
        # Analyze the field type
        field_type = analyze_field_type(selected_text, surrounding_text, app_name, window_title)
        print(f"Field type: {field_type}")
        
        # Get the appropriate value from the profile data
        result = get_field_value(profile_data, field_type)
        print(f"Result: {result[:50]}..." if len(result) > 50 else f"Result: {result}")
        
        # Insert the text using AppleScript
        if result:
            success = insert_text_with_applescript(result)
            if success:
                print("Text inserted successfully")
            else:
                print("Failed to insert text")
        
        return result
    except Exception as e:
        print(f"Error processing context: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_form_bridge.py <context_json_file>")
        sys.exit(1)
    
    # Get context JSON from file path
    context_file_path = sys.argv[1]
    
    try:
        # Read context data from file
        with open(context_file_path, "r") as f:
            context_data = json.load(f)
        
        # Process context and print result
        result = process_context(context_data)
        print(result)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in context file: {e}")
    except FileNotFoundError as e:
        print(f"Error: Context file not found: {e}")
    except Exception as e:
        print(f"Error: {str(e)}")
