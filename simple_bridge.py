#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
simple_bridge.py - A simplified bridge script that directly uses the profile data
"""

import sys
import json
import os
from pathlib import Path

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

def analyze_field_type(field_text):
    """Simple field type analysis based on the text"""
    field_text_lower = field_text.lower()
    
    # Basic mapping of field types
    if any(kw in field_text_lower for kw in ["email", "邮箱", "电子邮件", "邮件"]):
        return "Email Address"
    elif any(kw in field_text_lower for kw in ["phone", "电话", "手机", "联系方式", "联系电话"]):
        return "Phone Number"
    elif any(kw in field_text_lower for kw in ["name", "姓名", "全名"]):
        return "Full Name"
    elif any(kw in field_text_lower for kw in ["address", "地址", "住址"]):
        return "Street Address"
    elif any(kw in field_text_lower for kw in ["education", "学历", "教育", "学校", "大学"]):
        return "Education"
    elif any(kw in field_text_lower for kw in ["experience", "工作经历", "工作经验", "职业经历"]):
        return "Work Experience"
    elif any(kw in field_text_lower for kw in ["skills", "技能", "能力", "专长"]):
        return "Skills"
    elif any(kw in field_text_lower for kw in ["projects", "项目", "项目经验"]):
        return "Projects"
    elif any(kw in field_text_lower for kw in ["summary", "简介", "自我介绍", "个人简介"]):
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
    elif field_type == "Street Address" and "basic" in profile_data:
        return profile_data["basic"].get("location", "")
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
    else:
        return ""

def process_context(context_data):
    """Process the context data and return appropriate text"""
    try:
        # Get the selected text from the context data
        selected_text = context_data.get("selectedText", "")
        
        # Load the profile data
        profile_data = get_profile_data()
        
        # Analyze the field type
        field_type = analyze_field_type(selected_text)
        print(f"Field type: {field_type}")
        
        # Get the appropriate value from the profile data
        result = get_field_value(profile_data, field_type)
        
        return result
    except Exception as e:
        print(f"Error processing context: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_bridge.py <context_json_file>")
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
