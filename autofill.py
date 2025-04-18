#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SmartFill.AI - AI驱动的全局智能填写助手
============================================
一个基于LLM的Mac系统助手，通过右键唤出或快捷键，在任意应用中自动识别内容语境并智能填充信息。

依赖:
pip install rumps pyobjc-framework-Quartz pyobjc-core openai requests cryptography keyring tk Pillow
"""

import sys
import os
import json
import time
import threading
import re
import argparse
import keyring  # 用于安全存储API密钥
import webbrowser
from typing import Dict, List, Optional, Union, Any
import base64
import hashlib
from cryptography.fernet import Fernet
import traceback  # 用于更详细的错误日志

# GUI相关库
import rumps  # macOS状态栏应用
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk  # 用于处理图标

# macOS系统集成
import AppKit
import Quartz  # pyobjc-framework-Quartz
import objc
from Foundation import NSObject, NSLog, NSRunLoop, NSDefaultRunLoopMode
import Cocoa

# LLM API集成
import openai
import requests

# 配置和常量
APP_NAME = "SmartFill.AI"
APP_VERSION = "0.1.0"
CONFIG_DIR = os.path.expanduser("~/Library/Application Support/SmartFill.AI")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PROFILES_DIR = os.path.join(CONFIG_DIR, "profiles")
TEMPLATES_DIR = os.path.join(CONFIG_DIR, "templates")
LOG_FILE = os.path.join(CONFIG_DIR, "smartfill.log")
ENCRYPTION_KEY_FILE = os.path.join(CONFIG_DIR, "enckey")
ICON_FILE = "icon.png"  # 需要一个icon.png文件在同目录下，或修改路径

# 确保目录存在
for directory in [CONFIG_DIR, PROFILES_DIR, TEMPLATES_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            print(f"Error creating directory {directory}: {e}", file=sys.stderr)
            sys.exit(1)

# 日志记录设置
import logging

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(APP_NAME)
# 添加StreamHandler以同时输出到控制台 (可选)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(console_handler)

logger.info("SmartFill.AI application starting...")


# --- 加密管理 ---
class EncryptionManager:
    """处理用户数据加密和解密"""

    def __init__(self):
        self.key = self._get_or_create_key()
        if self.key:
            self.cipher = Fernet(self.key)
        else:
            self.cipher = None
            logger.error("Failed to get or create encryption key.")

    def _get_or_create_key(self) -> Optional[bytes]:
        """获取或创建加密密钥"""
        try:
            if os.path.exists(ENCRYPTION_KEY_FILE):
                with open(ENCRYPTION_KEY_FILE, "rb") as f:
                    key = f.read()
                    if len(key) == 44 and key.endswith(
                        b"="
                    ):  # Basic check for Fernet key format
                        return base64.urlsafe_b64decode(key)
                    else:
                        logger.warning(
                            "Existing encryption key file is invalid. Regenerating."
                        )
                        os.remove(ENCRYPTION_KEY_FILE)  # Remove invalid key
                        return self._generate_new_key()
            else:
                return self._generate_new_key()
        except Exception as e:
            logger.error(
                f"Error getting or creating encryption key: {e}", exc_info=True
            )
            return None

    def _generate_new_key(self) -> Optional[bytes]:
        """生成新密钥并保存"""
        try:
            key = Fernet.generate_key()
            with open(ENCRYPTION_KEY_FILE, "wb") as f:
                # Store the base64 encoded key for easier inspection if needed
                f.write(base64.urlsafe_b64encode(key))
            logger.info("Generated new encryption key.")
            return key
        except Exception as e:
            logger.error(f"Error generating new encryption key: {e}", exc_info=True)
            return None

    def encrypt(self, data: str) -> Optional[str]:
        """加密字符串数据"""
        if not self.cipher:
            logger.error("Encryption cipher not available.")
            return None
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """解密加密的字符串数据"""
        if not self.cipher:
            logger.error("Decryption cipher not available.")
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            # This can happen if the key changes or data is corrupt
            logger.error(
                f"Decryption failed: {e}. Data might be corrupt or key changed.",
                exc_info=True,
            )
            return None


# --- 用户档案管理 ---
class UserProfile:
    """用户信息档案管理"""

    def __init__(self, profile_id: str = "default"):
        self.profile_id = profile_id
        self.encryption_mgr = EncryptionManager()

        # For testing purposes, directly load the default profile if it's the default profile
        if profile_id == "default":
            try:
                profile_path = self._get_profile_path()
                logger.info(
                    f"Attempting to load default profile directly from {profile_path}"
                )
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_json = json.load(f)
                    if "data" in profile_json and isinstance(
                        profile_json["data"], dict
                    ):
                        logger.info("Successfully loaded default profile data")
                        self.data = profile_json["data"]
                        return
            except Exception as e:
                logger.error(f"Error directly loading default profile: {e}")

        # If direct loading fails or it's not the default profile, use the standard method
        self.data = self._load_profile()

    def _get_profile_path(self) -> str:
        """获取配置文件路径"""
        return os.path.join(PROFILES_DIR, f"{self.profile_id}.json")

    def _load_profile(self) -> Dict:
        """加载用户档案"""
        profile_path = self._get_profile_path()
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_json = json.load(f)

                    # Check if this is a plain JSON format (unencrypted)
                    if (
                        "version" in profile_json
                        and "data" in profile_json
                        and isinstance(profile_json["data"], dict)
                    ):
                        logger.info(f"Loading unencrypted profile from {profile_path}")
                        return profile_json["data"]

                    # Otherwise, try to handle as encrypted format
                    encrypted_data = profile_json.get("data")
                    if not encrypted_data:
                        logger.warning(
                            f"Profile file {profile_path} is missing 'data' field. Creating default profile."
                        )
                        return self._create_default_profile()

                    # Try to decrypt if it's encrypted
                    try:
                        decrypted_json = self.encryption_mgr.decrypt(encrypted_data)
                        if decrypted_json:
                            return json.loads(decrypted_json)
                    except Exception as decrypt_error:
                        logger.warning(
                            f"Could not decrypt profile data: {decrypt_error}. Assuming unencrypted format."
                        )
                        # If decryption fails but data exists, it might be already in plain text
                        if isinstance(encrypted_data, dict):
                            logger.info("Using plain text data from profile")
                            return encrypted_data

                    # If we reach here, we couldn't handle the data format
                    logger.error(
                        f"Failed to process profile {self.profile_id}. Using default profile."
                    )
                    return self._create_default_profile()

            except json.JSONDecodeError as e:
                logger.error(
                    f"Error decoding JSON from profile file {profile_path}: {e}. Creating default profile."
                )
                return self._create_default_profile()
            except Exception as e:
                logger.error(
                    f"Error loading profile {self.profile_id}: {e}", exc_info=True
                )
                return self._create_default_profile()
        else:
            logger.info(
                f"Profile {self.profile_id} not found. Creating default profile."
            )
            return self._create_default_profile()

    def _create_default_profile(self) -> Dict:
        """创建默认用户档案"""
        profile_data = {
            "basic": {
                "name": "",
                "gender": "",
                "birth_year": "",
                "email": "",
                "phone": "",
                "location": "",
            },
            "education": [{"period": "", "school": "", "degree": "", "major": ""}],
            "work_experience": [
                {"company": "", "period": "", "title": "", "highlights": []}
            ],
            "projects": [{"name": "", "description": "", "highlights": []}],
            "skills": {
                "ai_frameworks": [],
                "hardware": [],
                "certifications": [],
                "achievements": [],
            },
            "portfolio": {"personal_website": "", "projects": []},
        }
        # Immediately save the newly created default profile
        self.data = profile_data  # Set self.data before saving
        self.save()
        return profile_data

    def save(self) -> bool:
        """保存用户档案"""
        if not self.data:
            logger.error("Attempted to save empty profile data.")
            return False
        if not self.encryption_mgr.cipher:
            logger.error("Cannot save profile, encryption cipher not available.")
            return False

        profile_path = self._get_profile_path()
        try:
            json_data = json.dumps(self.data, ensure_ascii=False, indent=2)
            encrypted_data_str = self.encryption_mgr.encrypt(json_data)

            if not encrypted_data_str:
                logger.error(
                    f"Encryption failed for profile {self.profile_id}. Save aborted."
                )
                return False

            encrypted_container = {
                "profile_id": self.profile_id,
                "data": encrypted_data_str,
                "updated_at": time.time(),
            }
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(encrypted_container, f, indent=2)
            logger.info(f"Profile '{self.profile_id}' saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving profile {self.profile_id}: {e}", exc_info=True)
            return False

    def update(self, section: str, key: str, value: Any) -> bool:
        """更新用户档案中的特定字段"""
        if section not in self.data:
            self.data[section] = {}  # Create section if it doesn't exist

        # Special handling for list types (skills, experience, education)
        if isinstance(self.data.get(section, {}).get(key), list) and isinstance(
            value, str
        ):
            # Assume comma-separated string for skills list update
            if key == "skills":
                self.data[section][key] = [
                    s.strip() for s in value.split(",") if s.strip()
                ]
            else:
                # For experience/education, replacing the whole list might be complex via simple update
                # This might need a more structured UI approach
                logger.warning(
                    f"Updating list field '{key}' via simple update is not fully supported. Assigning value directly."
                )
                self.data[section][key] = value  # Or handle more specifically if needed
        else:
            self.data[section][key] = value

        return self.save()

    def get_value(self, section: str, key: str) -> Any:
        """获取用户档案中的特定字段值"""
        return self.data.get(section, {}).get(key, None)

    def get_profile_summary(self) -> str:
        """生成包含所有个人和职业信息的摘要文本"""
        summary = "User Profile Summary:\n"

        # Basic information
        if "basic" in self.data:
            summary += "\nBasic Information:\n"
            for key, value in self.data["basic"].items():
                if value:  # Only include non-empty values
                    summary += f"  {key.replace('_', ' ').capitalize()}: {value}\n"

        # Education
        if "education" in self.data and self.data["education"]:
            summary += "\nEducation:\n"
            for edu in self.data["education"]:
                if any(edu.values()):
                    edu_str = f"  {edu.get('school', '')} - {edu.get('degree', '')} in {edu.get('major', '')}"
                    if edu.get("period"):
                        edu_str += f" ({edu.get('period', '')})"
                    summary += edu_str + "\n"

        # Work Experience
        if "work_experience" in self.data and self.data["work_experience"]:
            summary += "\nWork Experience:\n"
            for job in self.data["work_experience"]:
                if any(v for v in job.values() if v and not isinstance(v, list)):
                    job_str = f"  {job.get('title', '')} at {job.get('company', '')}"
                    if job.get("period"):
                        job_str += f" ({job.get('period', '')})"
                    summary += job_str + "\n"

                    # Add highlights if any
                    if job.get("highlights"):
                        for highlight in job["highlights"]:
                            summary += f"    - {highlight}\n"

        # Skills
        if "skills" in self.data and self.data["skills"]:
            summary += "\nSkills:\n"
            for skill_type, skills in self.data["skills"].items():
                if skills:  # Only include non-empty values
                    if isinstance(skills, list):
                        summary += f"  {skill_type.replace('_', ' ').capitalize()}: {', '.join(skills)}\n"
                    else:
                        summary += (
                            f"  {skill_type.replace('_', ' ').capitalize()}: {skills}\n"
                        )

        # Projects
        if "projects" in self.data and self.data["projects"]:
            summary += "\nProjects:\n"
            for project in self.data["projects"]:
                if any(v for v in project.values() if v and not isinstance(v, list)):
                    summary += f"  {project.get('name', '')}\n"
                    if project.get("description"):
                        summary += f"    {project.get('description')}\n"
                    if project.get("achievement"):
                        summary += f"    Achievement: {project.get('achievement')}\n"

                    # Add highlights if any
                    if project.get("highlights"):
                        for highlight in project["highlights"]:
                            summary += f"    - {highlight}\n"

        # Portfolio
        if "portfolio" in self.data and self.data["portfolio"]:
            summary += "\nPortfolio:\n"
            if self.data["portfolio"].get("personal_website"):
                summary += f"  Website: {self.data['portfolio']['personal_website']}\n"

            if self.data["portfolio"].get("projects"):
                for proj in self.data["portfolio"]["projects"]:
                    if proj.get("name") and proj.get("url"):
                        summary += f"  {proj.get('name')}: {proj.get('url')}\n"
                        if proj.get("description"):
                            summary += f"    {proj.get('description')}\n"

        return summary.strip()


# --- 配置管理 ---
class ConfigManager:
    """应用配置管理"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载应用配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # Ensure default keys exist after loading
                    return self._ensure_defaults(config)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Error decoding config file {CONFIG_FILE}: {e}. Creating default config."
                )
                return self._create_default_config()
            except Exception as e:
                logger.error(f"Error loading config file: {e}", exc_info=True)
                return self._create_default_config()
        else:
            logger.info("Config file not found. Creating default config.")
            return self._create_default_config()

    def _ensure_defaults(self, loaded_config):
        """Ensure all default keys exist in the loaded config."""
        default_config = self._get_default_structure()
        updated = False
        for section, defaults in default_config.items():
            if section not in loaded_config:
                loaded_config[section] = defaults
                updated = True
            elif isinstance(defaults, dict):
                for key, default_value in defaults.items():
                    if key not in loaded_config[section]:
                        loaded_config[section][key] = default_value
                        updated = True
        # Update version if necessary
        if loaded_config.get("app_version") != APP_VERSION:
            loaded_config["app_version"] = APP_VERSION
            updated = True

        if updated:
            logger.info("Config updated with default values for missing keys.")
            self.save_config(loaded_config)  # Save immediately if defaults were added
        return loaded_config

    def _get_default_structure(self) -> Dict:
        """Returns the structure of the default config."""
        return {
            "app_version": APP_VERSION,
            "llm": {
                "provider": "openai",  # Supported: "openai", "ollama" (future), "none"
                "api_key_stored": False,  # Flag indicating if key is in keyring
                "model": "gpt-4o",  # Default OpenAI model
                "ollama_base_url": "http://localhost:11434",  # For local Ollama
                "ollama_model": "llama3",  # Default Ollama model
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            "ui": {
                "theme": "system",
                "shortcut": "Cmd+Shift+F",  # Use format recognizable by shortcut libraries
                "show_animations": True,
            },
            "active_profile": "default",
            "templates": {  # Example template structure (can be expanded)
                "default_reply": "Thank you for your message. I will get back to you soon."
            },
            "privacy": {
                "local_processing_preferred": False,  # Prefer local (Ollama) if available and configured
                "anonymize_sensitive_data": True,  # Attempt to redact sensitive info before sending to LLM (future)
            },
            "accessibility": {
                "permissions_granted": False  # Automatically updated by check
            },
        }

    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        default_config = self._get_default_structure()
        self.save_config(default_config)  # Use save_config to write file
        return default_config

    def save_config(self, config_data=None) -> bool:
        """保存配置到文件"""
        config_to_save = config_data if config_data else self.config
        # Never save the actual API key in the config file
        if "llm" in config_to_save and "api_key" in config_to_save["llm"]:
            del config_to_save["llm"]["api_key"]  # Ensure it's not saved

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved successfully.")
            # Update the in-memory config if saved successfully
            if config_data:
                self.config = config_data
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {e}", exc_info=True)
            return False

    def get(self, section: str, key: str = None) -> Any:
        """获取配置值"""
        if key is None:
            return self.config.get(section)

        section_data = self.config.get(section)
        if isinstance(section_data, dict):
            return section_data.get(key)
        return None

    def set(self, section: str, key: str, value: Any, save: bool = True) -> bool:
        """设置配置值并可选择是否立即保存"""
        if section not in self.config:
            self.config[section] = {}

        # Special handling for API Key - store in keyring, update flag in config
        if section == "llm" and key == "api_key":
            if value:
                try:
                    keyring.set_password(
                        APP_NAME, f"{self.get('llm', 'provider')}_api_key", value
                    )
                    self.config["llm"]["api_key_stored"] = True
                    logger.info(
                        f"API key for {self.get('llm', 'provider')} stored securely."
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to store API key securely: {e}", exc_info=True
                    )
                    messagebox.showerror(
                        "Error", f"Failed to store API key securely:\n{e}"
                    )
                    return False  # Indicate failure
            else:  # Clear the key
                try:
                    keyring.delete_password(
                        APP_NAME, f"{self.get('llm', 'provider')}_api_key"
                    )
                    self.config["llm"]["api_key_stored"] = False
                    logger.info(f"API key for {self.get('llm', 'provider')} cleared.")
                except keyring.errors.PasswordDeleteError:
                    logger.info(
                        f"No API key found for {self.get('llm', 'provider')} to clear."
                    )
                    self.config["llm"]["api_key_stored"] = False  # Ensure flag is false
                except Exception as e:
                    logger.error(f"Failed to clear API key: {e}", exc_info=True)
                    # Don't block saving config if clearing fails, just log it.
            # Do not store the actual key in self.config dict
            if save:
                return self.save_config()
            else:
                return True  # Config updated in memory, not saved yet

        # Standard key setting
        self.config[section][key] = value
        if save:
            return self.save_config()
        else:
            return True  # Config updated in memory, not saved yet

    def get_api_key(self) -> Optional[str]:
        """Retrieve API key securely from keyring."""
        provider = self.get("llm", "provider")
        if self.get("llm", "api_key_stored"):
            try:
                key = keyring.get_password(APP_NAME, f"{provider}_api_key")
                if key:
                    return key
                else:
                    # Key was marked as stored, but not found in keyring (edge case)
                    logger.warning(
                        f"API key for {provider} marked as stored but not found in keyring."
                    )
                    self.set("llm", "api_key_stored", False)  # Correct the flag
                    return None
            except Exception as e:
                logger.error(
                    f"Failed to retrieve API key from keyring: {e}", exc_info=True
                )
                return None
        return None


# --- LLM 管理器 ---
class LLMManager:
    """LLM API 管理器"""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.client = None
        self._setup_client()

    def _setup_client(self):
        """设置API客户端"""
        provider = self.config.get("llm", "provider")
        api_key = self.config.get_api_key()

        if provider == "openai":
            if api_key:
                try:
                    self.client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized.")
                except Exception as e:
                    self.client = None
                    logger.error(
                        f"Failed to initialize OpenAI client: {e}", exc_info=True
                    )
            else:
                self.client = None
                logger.warning("OpenAI provider selected but API key is missing.")
        elif provider == "ollama":
            # Ollama doesn't typically use an API key, it relies on the base URL
            base_url = self.config.get("llm", "ollama_base_url")
            # We will use requests directly for Ollama for simplicity here
            self.client = None  # Mark client as None, handle via requests
            logger.info(f"Ollama provider selected. Using base URL: {base_url}")
            # Test connection to Ollama endpoint maybe?
            try:
                response = requests.get(base_url)
                if response.status_code == 200:
                    logger.info("Successfully connected to Ollama base URL.")
                else:
                    logger.warning(
                        f"Could not connect to Ollama base URL {base_url}. Status code: {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to Ollama base URL {base_url}: {e}")

        elif provider == "none":
            self.client = None
            logger.info("LLM provider set to 'none'. Smart features disabled.")
        else:
            self.client = None
            logger.error(f"Unsupported LLM provider: {provider}")

    def test_connection(self) -> (bool, str):
        """测试LLM API连接"""
        provider = self.config.get("llm", "provider")
        logger.info(f"Testing LLM connection for provider: {provider}")
        self._setup_client()  # Ensure client is up-to-date

        if provider == "openai":
            if not self.client:
                return False, "OpenAI client not initialized. Check API key."
            try:
                # Use a less resource-intensive model for testing if possible
                test_model = "gpt-3.5-turbo"  # Cheaper/faster model for testing
                self.client.models.retrieve(
                    test_model
                )  # Check if model exists/API key is valid
                logger.info("OpenAI connection test successful.")
                return True, "OpenAI connection successful!"
            except openai.AuthenticationError:
                logger.error("OpenAI Authentication Error: Invalid API Key.")
                return False, "Authentication Error: Invalid OpenAI API Key."
            except openai.RateLimitError:
                logger.warning("OpenAI Rate Limit Error during test.")
                return False, "Rate limit exceeded. Please try again later."
            except Exception as e:
                logger.error(f"Error testing OpenAI connection: {e}", exc_info=True)
                return False, f"Error: {str(e)}"

        elif provider == "ollama":
            base_url = self.config.get("llm", "ollama_base_url")
            try:
                # Check base URL connectivity
                response = requests.get(base_url, timeout=5)
                if response.status_code != 200:
                    return (
                        False,
                        f"Ollama server at {base_url} not responding correctly (Status: {response.status_code}).",
                    )

                # Check if the specified model is available
                model_name = self.config.get("llm", "ollama_model")
                if not model_name:
                    return False, "No Ollama model specified in settings."

                api_url = f"{base_url.rstrip('/')}/api/tags"
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                models = response.json().get("models", [])
                if any(m["name"].startswith(model_name) for m in models):
                    logger.info(
                        f"Ollama connection test successful. Model '{model_name}' found."
                    )
                    return (
                        True,
                        f"Ollama connection successful! Model '{model_name}' found.",
                    )
                else:
                    logger.warning(
                        f"Ollama model '{model_name}' not found on server {base_url}."
                    )
                    available_models = [m["name"] for m in models]
                    return (
                        False,
                        f"Ollama model '{model_name}' not found. Available: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}",
                    )

            except requests.exceptions.RequestException as e:
                logger.error(f"Error testing Ollama connection to {base_url}: {e}")
                return False, f"Error connecting to Ollama at {base_url}:\n{e}"
            except Exception as e:
                logger.error(f"Unexpected error testing Ollama: {e}", exc_info=True)
                return False, f"Unexpected error: {e}"

        elif provider == "none":
            return True, "LLM is disabled."
        else:
            return False, f"Unsupported provider: {provider}"

    def generate_text(self, prompt: str, context: Dict = None) -> str:
        """根据提示和上下文生成文本"""
        provider = self.config.get("llm", "provider")
        model = self.config.get(
            "llm", model
        )  # Use specific model key based on provider
        temperature = self.config.get("llm", "temperature")
        max_tokens = self.config.get("llm", "max_tokens")

        if provider == "none":
            return "LLM is disabled."

        if not prompt:
            logger.warning("generate_text called with empty prompt.")
            return ""

        # Refresh client/settings in case they changed
        self._setup_client()

        system_prompt = f"""
        You are {APP_NAME}, an intelligent form-filling assistant. Your goal is to generate concise, relevant, and context-aware content for the requested field based on the provided context and user profile information.
        Adhere to the specified style and length constraints if provided. If generating personal information, be mindful of privacy.
        Focus on fulfilling the request for the specific field mentioned in the prompt.
        """

        context_str = "Context Information:\n"
        if context:
            profile_summary = context.get("profile_summary", "Not available.")
            app_context = context.get("app_context", {})
            context_str += f"- User Profile Summary: {profile_summary}\n"
            context_str += f"- Application: {app_context.get('app_name', 'Unknown')}\n"
            context_str += f"- Window: {app_context.get('window_title', 'Unknown')}\n"
            context_str += f"- Field Role: {app_context.get('role_description', app_context.get('role', 'Unknown'))}\n"
            context_str += f"- Field Label/Placeholder: {app_context.get('title', app_context.get('placeholder', 'Unknown'))}\n"
            context_str += f"- Surrounding Text (Excerpt): {app_context.get('surrounding_text', 'None')[:200]}...\n"  # Limit surrounding text in prompt
        else:
            context_str += "No context provided.\n"

        full_user_prompt = f"{context_str}\n\nTask: Fill the field described below.\nField Details: {prompt}"

        logger.debug(
            f"Generating text with provider '{provider}', model '{model}'. Prompt: {prompt}"
        )

        try:
            if provider == "openai":
                if not self.client:
                    return "Error: OpenAI client not initialized. Check API key."
                openai_model = self.config.get("llm", "model")
                response = self.client.chat.completions.create(
                    model=openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                generated_text = response.choices[0].message.content.strip()
                logger.info(f"OpenAI generated text length: {len(generated_text)}")
                return generated_text

            elif provider == "ollama":
                base_url = self.config.get("llm", "ollama_base_url")
                ollama_model = self.config.get("llm", "ollama_model")
                if not ollama_model:
                    return "Error: Ollama model not specified in settings."

                api_url = f"{base_url.rstrip('/')}/api/generate"
                payload = {
                    "model": ollama_model,
                    "prompt": full_user_prompt,  # Ollama often works better with just the prompt
                    "system": system_prompt,
                    "stream": False,  # Get the full response at once
                    "options": {
                        "temperature": temperature,
                        # Ollama might not support max_tokens directly in options for all models
                        # "num_predict": max_tokens # Some models use num_predict
                    },
                }
                headers = {"Content-Type": "application/json"}

                response = requests.post(
                    api_url, headers=headers, json=payload, timeout=60
                )  # Increased timeout
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                response_data = response.json()
                generated_text = response_data.get("response", "").strip()
                logger.info(f"Ollama generated text length: {len(generated_text)}")
                return generated_text

            else:
                return f"Error: Unsupported LLM provider '{provider}'"

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}", exc_info=True)
            return "Error: Invalid OpenAI API Key."
        except openai.RateLimitError as e:
            logger.error(f"OpenAI Rate Limit Error: {e}", exc_info=True)
            return "Error: OpenAI rate limit exceeded. Please try again later."
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}", exc_info=True)
            return f"Error connecting to Ollama: {e}"
        except Exception as e:
            logger.error(f"Error generating text with {provider}: {e}", exc_info=True)
            return f"Error generating text: {str(e)}"


# --- 上下文分析器 ---
class ContextAnalyzer:
    """上下文和内容分析器"""

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager

    def analyze_context(self, accessibility_info: Dict) -> Dict:
        """分析当前上下文，确定内容类型和所需信息"""
        app_name = accessibility_info.get("app_name", "Unknown")
        window_title = accessibility_info.get("window_title", "Unknown")
        field_label = (
            accessibility_info.get("title")
            or accessibility_info.get("placeholder")
            or "Unknown"
        )
        field_role = (
            accessibility_info.get("role_description")
            or accessibility_info.get("role")
            or "Unknown"
        )
        surrounding_text = accessibility_info.get("surrounding_text", "")[
            :500
        ]  # Limit context size

        # Basic keyword matching for common field types (faster than LLM)
        simple_analysis = self._simple_field_analysis(
            field_label, field_role, surrounding_text
        )
        if simple_analysis:
            logger.info(
                f"Simple analysis identified field type: {simple_analysis['field_type']}"
            )
            return simple_analysis

        # If simple analysis fails, use LLM for more complex cases
        logger.info("Performing LLM-based context analysis.")
        prompt = f"""
        Analyze the context of the currently focused UI element to understand what kind of information is required.

        Application: {app_name}
        Window Title: {window_title}
        Field Role: {field_role}
        Field Label/Placeholder: {field_label}
        Surrounding Text (Excerpt):
        {surrounding_text}

        Based *only* on the information above, determine the most likely type of information needed for the focused field.
        Respond in JSON format with the following keys:
        {{
            "content_type": "Determine the broader context (e.g., 'Job Application Form', 'Email Composition', 'Social Media Post', 'Website Login', 'Code Editor', 'General Text Field', 'Unknown'). Prioritize specific types if clear.",
            "field_type": "Identify the specific *type* of data needed for the field (e.g., 'Email Address', 'Password', 'Full Name', 'Phone Number', 'Street Address', 'City', 'Country', 'Job Title', 'Company Name', 'Skill List', 'Short Bio', 'Code Snippet', 'Generic Text', 'Search Query'). Be as specific as possible based on the labels and role.",
            "recommended_style": "Suggest a style based on context ('Professional', 'Casual', 'Technical', 'Formal', 'Friendly', 'Concise'). Default to 'Professional' if unsure.",
            "recommended_length": "Suggest a length ('Short', 'Medium', 'Long', 'Very Short' (e.g., single word), 'Variable'). Default to 'Medium'."
        }}
        Focus on the 'field_type' as the most crucial piece of information. Be precise. If it looks like a standard field (email, phone, name), identify it as such.
        """

        try:
            result_str = self.llm.generate_text(prompt)
            logger.debug(f"LLM analysis result string: {result_str}")
            # Try to extract JSON from the result (LLMs sometimes add extra text)
            match = re.search(r"\{.*\}", result_str, re.DOTALL)
            if match:
                json_str = match.group(0)
                analysis = json.loads(json_str)
                # Basic validation
                if all(
                    k in analysis
                    for k in [
                        "content_type",
                        "field_type",
                        "recommended_style",
                        "recommended_length",
                    ]
                ):
                    logger.info(f"LLM analysis successful: {analysis}")
                    return analysis
                else:
                    logger.warning(
                        "LLM analysis result missing required keys. Falling back."
                    )
                    return self._default_analysis(field_label)
            else:
                logger.warning(
                    "LLM analysis result did not contain valid JSON. Falling back."
                )
                return self._default_analysis(field_label)

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM analysis JSON: {e}. Result was: {result_str}",
                exc_info=True,
            )
            return self._default_analysis(field_label)
        except Exception as e:
            logger.error(f"Error during LLM context analysis: {e}", exc_info=True)
            return self._default_analysis(field_label)

    def _simple_field_analysis(
        self, label: str, role: str, text: str
    ) -> Optional[Dict]:
        """Fast check for common, easily identifiable fields."""
        label_lower = label.lower() if label else ""
        role_lower = role.lower() if role else ""
        text_lower = text.lower() if text else ""

        # Check surrounding text for resume-specific context clues
        resume_context = False
        if any(
            kw in text_lower
            for kw in [
                "resume",
                "cv",
                "curriculum vitae",
                "job application",
                "职位",
                "简历",
                "求职",
                "应聘",
            ]
        ):
            resume_context = True
            logger.info("Resume context detected in surrounding text")

        # Prioritize label/placeholder
        if any(
            kw in label_lower
            for kw in [
                "email",
                "e-mail",
                "mail address",
                "邮箱",
                "电子邮件",
                "联系邮箱",
            ]
        ):
            return {
                "field_type": "Email Address",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(
            kw in label_lower
            for kw in [
                "phone",
                "mobile",
                "contact number",
                "电话",
                "手机",
                "联系电话",
                "联系方式",
            ]
        ):
            return {
                "field_type": "Phone Number",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(
            kw in label_lower
            for kw in ["name", "full name", "your name", "姓名", "全名"]
        ):
            return {
                "field_type": "Full Name",
                "content_type": (
                    "Resume Form" if resume_context else "Personal Information"
                ),
                **self._default_analysis(label),
            }
        if any(
            kw in label_lower for kw in ["address", "street", "地址", "街道", "住址"]
        ):
            return {
                "field_type": "Street Address",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(kw in label_lower for kw in ["city", "城市"]):
            return {
                "field_type": "City",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(kw in label_lower for kw in ["state", "province", "省份", "州"]):
            return {
                "field_type": "State/Province",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(kw in label_lower for kw in ["zip", "postal code", "邮编", "邮政编码"]):
            return {
                "field_type": "Zip/Postal Code",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }
        if any(kw in label_lower for kw in ["country", "国家"]):
            return {
                "field_type": "Country",
                "content_type": (
                    "Resume Form" if resume_context else "Contact Information"
                ),
                **self._default_analysis(label),
            }

        # Resume-specific fields
        if any(
            kw in label_lower
            for kw in [
                "education",
                "school",
                "university",
                "college",
                "degree",
                "学历",
                "教育",
                "学校",
                "大学",
            ]
        ):
            return {
                "field_type": "Education",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower
            for kw in [
                "experience",
                "work history",
                "employment",
                "工作经历",
                "工作经验",
                "职业经历",
            ]
        ):
            return {
                "field_type": "Work Experience",
                "content_type": "Resume Form",
                "recommended_length": "Long",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower for kw in ["skills", "abilities", "技能", "能力", "专长"]
        ):
            return {
                "field_type": "Skills",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower
            for kw in [
                "summary",
                "profile",
                "objective",
                "个人简介",
                "自我介绍",
                "求职目标",
            ]
        ):
            return {
                "field_type": "Profile Summary",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower for kw in ["projects", "portfolio", "项目经验", "作品集"]
        ):
            return {
                "field_type": "Projects",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower
            for kw in ["achievements", "awards", "honors", "成就", "奖项", "荣誉"]
        ):
            return {
                "field_type": "Achievements",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(kw in label_lower for kw in ["languages", "语言", "外语"]):
            return {
                "field_type": "Languages",
                "content_type": "Resume Form",
                "recommended_length": "Short",
                "recommended_style": "Professional",
            }
        if any(
            kw in label_lower
            for kw in ["certifications", "licenses", "证书", "认证", "执照"]
        ):
            return {
                "field_type": "Certifications",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }
        if any(kw in label_lower for kw in ["references", "推荐人", "推荐信"]):
            return {
                "field_type": "References",
                "content_type": "Resume Form",
                "recommended_length": "Medium",
                "recommended_style": "Professional",
            }

        # Standard fields
        if any(kw in label_lower for kw in ["password", "secret", "密码"]):
            return {"field_type": "Password", **self._default_analysis(label)}
        if any(kw in label_lower for kw in ["search", "find", "搜索", "查找"]):
            return {"field_type": "Search Query", **self._default_analysis(label)}
        if any(kw in label_lower for kw in ["subject", "主题"]):
            return {
                "field_type": "Email Subject",
                "content_type": "Email Composition",
                **self._default_analysis(label),
            }
        if any(kw in label_lower for kw in ["company", "organization", "公司", "组织"]):
            return {
                "field_type": "Company Name",
                "content_type": (
                    "Resume Form" if resume_context else "Professional Information"
                ),
                **self._default_analysis(label),
            }
        if any(
            kw in label_lower
            for kw in ["job title", "position", "role", "职位", "职称", "角色"]
        ):
            return {
                "field_type": "Job Title",
                "content_type": (
                    "Resume Form" if resume_context else "Professional Information"
                ),
                **self._default_analysis(label),
            }
        if "text area" in role_lower and any(
            kw in label_lower
            for kw in ["comment", "message", "body", "评论", "留言", "正文"]
        ):
            return {"field_type": "Message Body", **self._default_analysis(label)}

        # Consider role
        if "password" in role_lower:
            return {"field_type": "Password", **self._default_analysis(label)}
        if "search" in role_lower:
            return {"field_type": "Search Query", **self._default_analysis(label)}

        # If we have resume context but couldn't identify the field specifically
        if resume_context:
            return {
                "field_type": "Resume Field",
                "content_type": "Resume Form",
                **self._default_analysis(label),
            }

        return None  # No simple match

    def _default_analysis(self, field_label="Unknown") -> Dict:
        """Fallback analysis if LLM fails or simple checks don't match."""
        return {
            "content_type": "Unknown",
            "field_type": field_label if field_label != "Unknown" else "Generic Text",
            "recommended_style": "Professional",
            "recommended_length": "Medium",
        }

    def generate_content(
        self, context_analysis: Dict, user_profile: UserProfile, app_context: Dict
    ) -> str:
        """基于上下文分析和用户资料生成内容"""
        field_type = context_analysis.get("field_type", "Generic Text")
        content_type = context_analysis.get("content_type", "Unknown")
        style = context_analysis.get("recommended_style", "Professional")
        length = context_analysis.get("recommended_length", "Medium")

        logger.info(
            f"Generating content for field type: '{field_type}', content type: '{content_type}', style: '{style}', length: '{length}'"
        )

        # 1. Direct Profile Mapping (Highest Priority for standard fields)
        # Map field types to profile data structure
        profile_map = {
            # Basic contact info
            "Email Address": ("basic", "email"),
            "Phone Number": ("basic", "phone"),
            "Full Name": ("basic", "name"),
            "Street Address": ("basic", "location"),
            "City": ("basic", "location"),
            "State/Province": ("basic", "location"),
            "Country": ("basic", "location"),
            "Website": ("portfolio", "personal_website"),
            # Professional info
            "Job Title": ("work_experience", "title"),  # Will use most recent
            "Company Name": ("work_experience", "company"),  # Will use most recent
            # Resume-specific fields
            "Education": ("education", None),  # Special handling for complex fields
            "Work Experience": ("work_experience", None),
            "Skills": ("skills", None),
            "Projects": ("projects", None),
            "Profile Summary": ("basic", None),  # Generate from multiple fields
            "Achievements": ("skills", "achievements"),
            "Languages": ("skills", None),
            "Certifications": ("skills", "certifications"),
        }
        if field_type in profile_map:
            section, key = profile_map[field_type]

            # Special handling for complex resume fields
            if key is None:
                # Handle complex fields that need special formatting
                if field_type == "Education":
                    education_data = user_profile.get_value(section, None)
                    if (
                        education_data
                        and isinstance(education_data, list)
                        and len(education_data) > 0
                    ):
                        # Format education entries
                        formatted_education = []
                        for edu in education_data:
                            entry = f"{edu.get('school', '')}, {edu.get('degree', '')} in {edu.get('major', '')} ({edu.get('period', '')})"
                            formatted_education.append(entry)
                        value = "\n".join(formatted_education)
                        logger.info(f"Formatted education data: '{value[:50]}...'")
                        return value

                elif field_type == "Work Experience":
                    work_data = user_profile.get_value(section, None)
                    if work_data and isinstance(work_data, list) and len(work_data) > 0:
                        # Format work experience entries
                        formatted_work = []
                        for job in work_data:
                            entry = f"{job.get('title', '')} at {job.get('company', '')} ({job.get('period', '')})\n"
                            highlights = job.get("highlights", [])
                            if highlights:
                                entry += "\n".join([f"• {h}" for h in highlights])
                            formatted_work.append(entry)
                        value = "\n\n".join(formatted_work)
                        logger.info(
                            f"Formatted work experience data: '{value[:50]}...'"
                        )
                        return value

                elif field_type == "Skills":
                    skills_data = user_profile.get_value(section, None)
                    if skills_data and isinstance(skills_data, dict):
                        # Format skills from different categories
                        formatted_skills = []
                        for category, skills_list in skills_data.items():
                            if isinstance(skills_list, list) and skills_list:
                                formatted_skills.append(
                                    f"{category.replace('_', ' ').title()}: {', '.join(skills_list)}"
                                )
                        value = "\n".join(formatted_skills)
                        logger.info(f"Formatted skills data: '{value[:50]}...'")
                        return value

                elif field_type == "Projects":
                    projects_data = user_profile.get_value(section, None)
                    if (
                        projects_data
                        and isinstance(projects_data, list)
                        and len(projects_data) > 0
                    ):
                        # Format project entries
                        formatted_projects = []
                        for project in projects_data:
                            entry = f"{project.get('name', '')}\n"
                            if "description" in project:
                                entry += f"{project.get('description', '')}\n"
                            if "achievement" in project:
                                entry += (
                                    f"Achievement: {project.get('achievement', '')}\n"
                                )
                            highlights = project.get("highlights", [])
                            if highlights:
                                entry += "\n".join([f"• {h}" for h in highlights])
                            formatted_projects.append(entry)
                        value = "\n\n".join(formatted_projects)
                        logger.info(f"Formatted projects data: '{value[:50]}...'")
                        return value

                elif field_type == "Profile Summary":
                    # Generate a profile summary from basic info and most recent experience
                    basic_info = user_profile.get_value("basic", None) or {}
                    work_exp = user_profile.get_value("work_experience", None) or []
                    skills_data = user_profile.get_value("skills", None) or {}

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
                            key_skills.extend(
                                skills_list[:3]
                            )  # Take up to 3 skills from each category

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

                    value = ". ".join(summary_parts)
                    if value:
                        logger.info(f"Generated profile summary: '{value}'")
                        return value

                # If we reach here, we couldn't format the complex field
                logger.warning(
                    f"Could not format complex field '{field_type}' from section '{section}'"
                )
                # Fall through to LLM generation
            else:
                # Handle simple direct mapping fields
                value = user_profile.get_value(section, key)
                if value:
                    # Special handling for work experience fields (use most recent)
                    if (
                        section == "work_experience"
                        and isinstance(value, list)
                        and len(value) > 0
                    ):
                        if key in value[0]:  # Most recent job is first in the list
                            value = value[0][key]
                        else:
                            value = None

                    if value:
                        logger.info(
                            f"Found direct profile match for '{field_type}': '{str(value)[:50]}...'"
                        )
                        return str(value)

                logger.warning(
                    f"Direct profile field '{section}.{key}' requested but is empty or invalid."
                )
                # Fall through to LLM generation if profile data is missing

        # 2. Password field - Never auto-fill directly for security
        if field_type == "Password":
            logger.info("Password field detected. Auto-fill skipped for security.")
            return "******"  # Placeholder or empty, do not generate

        # 3. LLM Generation for complex or missing fields
        profile_summary = (
            user_profile.get_profile_summary()
        )  # Get comprehensive summary

        # Construct a more targeted prompt for the LLM
        prompt = f"""
        Generate appropriate text to fill a field of type "{field_type}".
        The broader context is: "{content_type}".
        The desired style is "{style}" and the approximate length should be "{length}".

        Use the following user profile information if relevant, but prioritize filling the *specific field* requested:
        --- User Profile ---
        {profile_summary}
        --- End User Profile ---

        Application Context (for awareness):
        App: {app_context.get('app_name', 'Unknown')}
        Window: {app_context.get('window_title', 'Unknown')}
        Field Label: {app_context.get('title', app_context.get('placeholder', 'Unknown'))}

        Generate *only* the text content suitable for the "{field_type}" field. Do not add explanations or labels.
        """

        # Special handling for certain field types to guide the LLM
        if field_type in [
            "Short Bio",
            "About Me",
            "Self Introduction",
            "Profile Summary",
        ]:
            prompt += (
                "\nFocus on creating a concise and relevant biography or introduction."
            )
        elif field_type in ["Skill List", "Skills"]:
            prompt += "\nList relevant skills, potentially comma-separated or bulleted based on context."
        elif field_type in ["Work Experience Summary", "Experience"]:
            prompt += "\nSummarize key work experiences or provide details for one relevant role."
        elif field_type in ["Education Summary", "Education"]:
            prompt += "\nSummarize key educational achievements."
        elif field_type == "Message Body" and content_type == "Email Composition":
            prompt += "\nCompose a relevant email body based on the subject (if available) or general context."
        elif field_type == "Cover Letter Snippet":
            prompt += "\nGenerate a paragraph suitable for a cover letter, tailored to the job context if possible."

        # Add context for the LLM generation call
        llm_context = {"profile_summary": profile_summary, "app_context": app_context}

        generated_content = self.llm.generate_text(prompt, context=llm_context)

        # Basic post-processing (optional)
        # Remove potential markdown list markers if the field is likely plain text
        if field_type not in ["Skill List", "Message Body"] and length != "Long":
            generated_content = re.sub(r"^\s*[\*\-]\s+", "", generated_content)

        logger.info(
            f"LLM generated content for '{field_type}': '{generated_content[:50]}...'"
        )
        return generated_content


# --- 辅助功能管理器 ---
class AccessibilityManager(NSObject):
    """管理macOS辅助功能权限和交互"""

    # Class variable to store the singleton instance
    _instance = None

    @classmethod
    def sharedManager(cls):
        """Singleton access method."""
        if cls._instance is None:
            cls._instance = cls.alloc().init()
        return cls._instance

    def init(self):
        """Initializer"""
        self = objc.super(AccessibilityManager, self).init()
        if self is None:
            return None
        logger.info("AccessibilityManager initialized.")
        self._init_keycodes()
        return self

    def check_permissions(self, notify: bool = False) -> bool:
        """检查是否有辅助功能权限, 可选择是否弹窗提示"""
        options = (
            {objc.objc_bool(True): objc.kAXTrustedCheckOptionPrompt} if notify else None
        )
        trusted = Quartz.AXIsProcessTrustedWithOptions(options)
        if trusted:
            logger.debug("Accessibility permissions are granted.")
        else:
            logger.warning("Accessibility permissions are NOT granted.")
        return trusted

    def request_permissions(self) -> bool:
        """请求辅助功能权限（打开系统设置面板）"""
        logger.info("Requesting accessibility permissions by opening System Settings.")
        # This just opens the panel, user interaction is required.
        # It's better to use check_permissions(notify=True) first.
        NSWorkspace = AppKit.NSWorkspace.sharedWorkspace()
        url = AppKit.NSURL.URLWithString_(
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        )
        opened = NSWorkspace.openURL_(url)
        if not opened:
            logger.error("Failed to open System Settings for Accessibility.")
            # Fallback message if opening fails
            messagebox.showwarning(
                "Permission Request Failed",
                "Could not automatically open System Settings.\n\nPlease go to System Settings -> Privacy & Security -> Accessibility and enable SmartFill.AI.",
            )
        return opened

    def get_frontmost_app_info(self) -> Optional[Dict]:
        """获取前台应用信息"""
        try:
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            if not frontmost_app:
                logger.warning("Could not get frontmost application.")
                return None

            return {
                "name": frontmost_app.localizedName(),
                "bundle_id": frontmost_app.bundleIdentifier(),
                "process_id": frontmost_app.processIdentifier(),
            }
        except Exception as e:
            logger.error(f"Error getting frontmost app info: {e}", exc_info=True)
            return None

    def get_focused_element_info(self) -> Dict:
        """获取当前焦点元素的信息"""
        if not self.check_permissions():
            return {"error": "Accessibility permissions required."}

        app_info = self.get_frontmost_app_info()
        if not app_info:
            return {"error": "Could not get frontmost application info."}

        try:
            # Get AXUIElementRef for the frontmost application
            pid = app_info["process_id"]
            app_ref = Quartz.AXUIElementCreateApplication(pid)
            if not app_ref:
                return {"error": f"Could not create AXUIElement for PID {pid}."}

            # Get the focused UI element
            result, focused_element = Quartz.AXUIElementCopyAttributeValue(
                app_ref, Quartz.kAXFocusedUIElementAttribute, None
            )
            if result != 0 or not focused_element:
                # Fallback: try getting focused window first, then its focused element (useful for some apps)
                result_win, window_ref = Quartz.AXUIElementCopyAttributeValue(
                    app_ref, Quartz.kAXFocusedWindowAttribute, None
                )
                if result_win == 0 and window_ref:
                    result_focused, focused_element = (
                        Quartz.AXUIElementCopyAttributeValue(
                            window_ref, Quartz.kAXFocusedUIElementAttribute, None
                        )
                    )
                    if result_focused != 0 or not focused_element:
                        logger.warning(
                            "Could not get focused UI element via app or window."
                        )
                        return {
                            "app_name": app_info["name"],
                            "bundle_id": app_info["bundle_id"],
                            "error": "No focused element found.",
                        }
                else:
                    logger.warning("Could not get focused UI element via app.")
                    return {
                        "app_name": app_info["name"],
                        "bundle_id": app_info["bundle_id"],
                        "error": "No focused element found.",
                    }

            element_info = {
                "app_name": app_info["name"],
                "bundle_id": app_info["bundle_id"],
            }

            # Helper to safely get attributes
            def get_ax_attribute(element, attribute):
                res, val = Quartz.AXUIElementCopyAttributeValue(
                    element, attribute, None
                )
                if res == 0:
                    return val
                # Log only if attribute is expected to exist commonly
                # if attribute not in [Quartz.kAXPlaceholderValueAttribute]: # Example: Don't warn if placeholder missing
                #      logger.debug(f"Attribute {attribute} not found for element (Error code: {res})")
                return None

            # Get common attributes
            element_info["role"] = get_ax_attribute(
                focused_element, Quartz.kAXRoleAttribute
            )
            element_info["role_description"] = get_ax_attribute(
                focused_element, Quartz.kAXRoleDescriptionAttribute
            )
            element_info["title"] = get_ax_attribute(
                focused_element, Quartz.kAXTitleAttribute
            )  # Often the label
            element_info["value"] = get_ax_attribute(
                focused_element, Quartz.kAXValueAttribute
            )  # Current content
            element_info["placeholder"] = get_ax_attribute(
                focused_element, Quartz.kAXPlaceholderValueAttribute
            )  # Placeholder text
            element_info["help"] = get_ax_attribute(
                focused_element, Quartz.kAXHelpTagAttribute
            )  # Tooltip/help text
            element_info["editable"] = get_ax_attribute(
                focused_element, Quartz.kAXEnabledAttribute
            )  # Check if enabled first

            # Try to get window title
            window = get_ax_attribute(focused_element, Quartz.kAXWindowAttribute)
            if window:
                element_info["window_title"] = get_ax_attribute(
                    window, Quartz.kAXTitleAttribute
                )

            # Get surrounding text (more complex, attempt simple parent value)
            # A robust solution would involve traversing siblings or using AX APIs for text ranges
            surrounding_text = ""
            parent = get_ax_attribute(focused_element, Quartz.kAXParentAttribute)
            if parent:
                # Check if parent has a value (might be a container with text)
                parent_value = get_ax_attribute(parent, Quartz.kAXValueAttribute)
                if parent_value and isinstance(parent_value, str):
                    surrounding_text = parent_value
                # Could also try getting children and their values, but can be slow/complex
                # res, children = Quartz.AXUIElementCopyAttributeValues(parent, Quartz.kAXChildrenAttribute, 0, 10, None) # Limit children check
                # if res == 0 and children:
                #    # Process children values...

            element_info["surrounding_text"] = surrounding_text[:1000]  # Limit length

            # Clean up None values before returning
            return {k: v for k, v in element_info.items() if v is not None}

        except Exception as e:
            logger.error(f"Error getting focused element info: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def insert_text(self, text: str) -> bool:
        """向当前焦点元素插入文本"""
        if not self.check_permissions():
            logger.error("Cannot insert text: Accessibility permissions required.")
            return False

        app_info = self.get_frontmost_app_info()
        if not app_info:
            logger.error("Cannot insert text: Could not get frontmost application.")
            return False

        try:
            pid = app_info["process_id"]
            app_ref = Quartz.AXUIElementCreateApplication(pid)
            if not app_ref:
                return False

            res_focused, focused_element = Quartz.AXUIElementCopyAttributeValue(
                app_ref, Quartz.kAXFocusedUIElementAttribute, None
            )
            if res_focused != 0 or not focused_element:
                logger.warning("Insert text: No focused element found.")
                # Try pasting as a fallback? Requires clipboard manipulation.
                # Or simulate typing?
                return self._simulate_keyboard_input(
                    text
                )  # Attempt simulation as fallback

            # Check if the element is settable (more reliable than just 'editable')
            is_settable = objc.objc_bool(False)
            res_settable, is_settable = Quartz.AXUIElementIsAttributeSettable(
                focused_element, Quartz.kAXValueAttribute, objc.byref(is_settable)
            )

            if res_settable == 0 and is_settable:
                # Preferred method: Set the value directly
                res_setval = Quartz.AXUIElementSetAttributeValue(
                    focused_element, Quartz.kAXValueAttribute, text
                )
                if res_setval == 0:
                    logger.info(
                        f"Successfully inserted text using AX Set Value into {app_info['name']}."
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to set AXValue (Error: {res_setval}). Falling back to keyboard simulation."
                    )
                    return self._simulate_keyboard_input(text)
            else:
                # Element value not settable, try keyboard simulation
                logger.info(
                    "Focused element value not settable via AX API. Attempting keyboard simulation."
                )
                return self._simulate_keyboard_input(text)

        except Exception as e:
            logger.error(f"Error inserting text: {e}", exc_info=True)
            # Try simulation as last resort on error
            try:
                logger.info(
                    "Error occurred during insertion attempt. Falling back to keyboard simulation."
                )
                return self._simulate_keyboard_input(text)
            except Exception as sim_e:
                logger.error(f"Keyboard simulation also failed: {sim_e}", exc_info=True)
                return False

    def _simulate_keyboard_input(self, text: str) -> bool:
        """Simulate keyboard input using CoreGraphics Events."""
        logger.debug(f"Simulating keyboard input for text: {text[:30]}...")
        try:
            # Ensure the target application is still frontmost before typing
            # (There might be a slight delay, check again)
            current_app_info = self.get_frontmost_app_info()
            # Add a check here if necessary, though usually the focus remains

            # Create an event source
            event_source = Quartz.CGEventSourceCreate(
                Quartz.kCGEventSourceStateCombinedSessionState
            )
            if not event_source:
                logger.error("Failed to create CGEventSource.")
                return False

            # Loop through each character in the text
            for char in text:
                # Use CGEventKeyboardSetUnicodeString for reliable character input
                # Need to handle length > 1 ? No, process char by char
                # Need keycode? No, kCGEventKeyboardSetUnicodeString handles layout etc.

                # Create key down and key up events for the character
                # Using keycode 0 seems okay when using SetUnicodeString
                event_down = Quartz.CGEventCreateKeyboardEvent(event_source, 0, True)
                event_up = Quartz.CGEventCreateKeyboardEvent(event_source, 0, False)

                if not event_down or not event_up:
                    logger.error(f"Failed to create keyboard event for char '{char}'")
                    continue  # Skip this char

                # Set the Unicode string for the event
                # PyObjC needs explicit encoding to bytes and length calculation
                char_bytes = char.encode("utf-16le")  # utf-16 or utf-16le often works
                Quartz.CGEventKeyboardSetUnicodeString(
                    event_down, len(char_bytes) // 2, char_bytes
                )

                # Post the events to the system event stream
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

                # Short delay between characters to mimic human typing & prevent issues
                time.sleep(0.01)

            logger.info("Keyboard simulation completed.")
            return True
        except Exception as e:
            logger.error(f"Error during keyboard simulation: {e}", exc_info=True)
            return False

    # --- Keycode mapping (Simplified - CGEventKeyboardSetUnicodeString is preferred) ---
    # The following methods are generally NOT needed if using CGEventKeyboardSetUnicodeString,
    # but are kept here for reference or potential fallback scenarios.

    def _init_keycodes(self):
        """Initialize a basic mapping from char to keycode + modifiers."""
        # This is complex due to keyboard layouts. This is a VERY simplified US layout approximation.
        # For robust simulation involving modifiers (Shift, Cmd, etc.), a dedicated library or
        # more complex mapping based on current keyboard layout is needed.
        self.keycodes = {
            "a": 0,
            "s": 1,
            "d": 2,
            "f": 3,
            "h": 4,
            "g": 5,
            "z": 6,
            "x": 7,
            "c": 8,
            "v": 9,
            "b": 11,
            "q": 12,
            "w": 13,
            "e": 14,
            "r": 15,
            "y": 16,
            "t": 17,
            "1": 18,
            "2": 19,
            "3": 20,
            "4": 21,
            "6": 22,
            "5": 23,
            "=": 24,
            "9": 25,
            "7": 26,
            "-": 27,
            "8": 28,
            "0": 29,
            "]": 30,
            "o": 31,
            "u": 32,
            "[": 33,
            "i": 34,
            "p": 35,
            "l": 37,
            "j": 38,
            "'": 39,
            "k": 40,
            ";": 41,
            "\\": 42,
            ",": 43,
            "/": 44,
            "n": 45,
            "m": 46,
            ".": 47,
            "`": 50,
            " ": 49,
            "\r": 36,
            "\t": 48,
            "\x1b": 53,  # Space, Enter, Tab, Escape
        }
        self.shift_map = {  # Map characters requiring Shift key
            "A": 0,
            "S": 1,
            "D": 2,
            "F": 3,
            "H": 4,  # ... add all uppercase
            "!": 18,
            "@": 19,
            "#": 20,
            "$": 21,
            "^": 22,
            "%": 23,
            "+": 24,
            "(": 25,
            "&": 26,
            "_": 27,
            "*": 28,
            ")": 29,
            "}": 30,
            "O": 31,  # ... add all shifted symbols
            '"': 39,
            ":": 41,
            "|": 42,
            "<": 43,
            "?": 44,
            ">": 47,
            "~": 50,
        }
        # Modifiers
        self.kVK_Shift = 56
        self.kVK_Command = 55
        self.kVK_Option = 58
        self.kVK_Control = 59

    def _get_keycode_and_flags(self, char: str) -> (Optional[int], int):
        """Get keycode and modifier flags for a character (Simplified US layout)."""
        flags = 0
        keycode = None

        if char in self.keycodes:
            keycode = self.keycodes[char]
        elif char in self.shift_map:
            keycode = self.shift_map[char]
            flags |= Quartz.kCGEventFlagMaskShift  # Add Shift flag
        else:
            # Character not in simple map (e.g., accented chars, complex symbols)
            # CGEventKeyboardSetUnicodeString is better for these.
            logger.warning(
                f"No simple keycode mapping for character: '{char}'. Simulation might be inaccurate."
            )
            return None, 0  # Indicate failure for this char if using keycode method

        return keycode, flags

    def _simulate_keypress(self, keycode: int, flags: int = 0):
        """Simulate a single key press and release with modifiers."""
        event_source = Quartz.CGEventSourceCreate(
            Quartz.kCGEventSourceStateCombinedSessionState
        )
        if not event_source:
            return

        # Press modifiers if any
        if flags & Quartz.kCGEventFlagMaskShift:
            Quartz.CGEventPost(
                Quartz.kCGHIDEventTap,
                Quartz.CGEventCreateKeyboardEvent(event_source, self.kVK_Shift, True),
            )
        # Add other modifiers (Cmd, Option, Ctrl) if needed based on flags

        # Press and release the main key
        Quartz.CGEventPost(
            Quartz.kCGHIDEventTap,
            Quartz.CGEventCreateKeyboardEvent(event_source, keycode, True),
        )
        Quartz.CGEventPost(
            Quartz.kCGHIDEventTap,
            Quartz.CGEventCreateKeyboardEvent(event_source, keycode, False),
        )

        # Release modifiers
        if flags & Quartz.kCGEventFlagMaskShift:
            Quartz.CGEventPost(
                Quartz.kCGHIDEventTap,
                Quartz.CGEventCreateKeyboardEvent(event_source, self.kVK_Shift, False),
            )
        # Release other modifiers

        time.sleep(0.01)  # Small delay


# --- Tkinter Settings Windows ---


class SettingsWindowBase(tk.Toplevel):
    """Base class for settings windows"""

    def __init__(self, app_instance, title):
        super().__init__()
        self.app = app_instance  # Reference to the main SmartFillApp instance
        self.config_manager = app_instance.config_manager
        self.withdraw()  # Hide window initially
        self.title(f"{APP_NAME} - {title}")
        # Ensure window appears on top
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Center the window
        self.update_idletasks()  # Ensure dimensions are calculated
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.load_settings()

        self.deiconify()  # Show window
        self.grab_set()  # Make modal
        self.focus_set()  # Grab focus

    def create_widgets(self):
        # To be implemented by subclasses
        pass

    def load_settings(self):
        # To be implemented by subclasses
        pass

    def save_settings(self):
        # To be implemented by subclasses
        pass

    def on_close(self):
        # Optionally ask to save changes or just close
        self.destroy()

    def run_on_main_thread(self, func, *args):
        """Helper to run GUI updates on the main thread if needed"""
        # In this setup, Tkinter runs synchronously with rumps callbacks,
        # so direct calls are usually fine. This is a placeholder.
        self.app.call_later(0, func, *args)


class ProfileSettingsWindow(SettingsWindowBase):
    """Window for managing User Profile settings"""

    def __init__(self, app_instance):
        self.user_profile = app_instance.user_profile  # Get current profile
        self.vars = {}  # Dictionary to hold Tkinter variables
        super().__init__(app_instance, "Personal Profile")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Personal Section ---
        personal_frame = ttk.LabelFrame(
            frame, text="Personal Information", padding="10"
        )
        personal_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        personal_frame.columnconfigure(1, weight=1)

        row = 0
        for key, label in [
            ("name", "Full Name:"),
            ("email", "Email:"),
            ("phone", "Phone:"),
            ("address", "Address:"),
            ("birthday", "Birthday:"),
            ("website", "Website:"),
        ]:
            ttk.Label(personal_frame, text=label).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            self.vars[("personal", key)] = tk.StringVar()
            ttk.Entry(
                personal_frame, textvariable=self.vars[("personal", key)], width=40
            ).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            row += 1

        # --- Professional Section ---
        prof_frame = ttk.LabelFrame(
            frame, text="Professional Information", padding="10"
        )
        prof_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        prof_frame.columnconfigure(1, weight=1)

        row = 0
        for key, label in [
            ("title", "Job Title:"),
            ("company", "Company:"),
            ("industry", "Industry:"),
        ]:
            ttk.Label(prof_frame, text=label).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            self.vars[("professional", key)] = tk.StringVar()
            ttk.Entry(
                prof_frame, textvariable=self.vars[("professional", key)], width=40
            ).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            row += 1

        # Skills (comma-separated list)
        ttk.Label(prof_frame, text="Skills (comma-sep):").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.vars[("professional", "skills")] = tk.StringVar()
        ttk.Entry(
            prof_frame, textvariable=self.vars[("professional", "skills")], width=40
        ).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # Experience & Education (simplified view - display first item or message)
        # TODO: Add buttons to manage these lists in more detail (separate window?)
        ttk.Label(prof_frame, text="Experience:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        exp_text = self.user_profile.get_value("professional", "experience")
        exp_display = (
            f"{len(exp_text)} entries (Edit not available here)"
            if exp_text
            else "No entries"
        )
        ttk.Label(prof_frame, text=exp_display).grid(
            row=row, column=1, sticky=tk.W, pady=2
        )
        row += 1

        ttk.Label(prof_frame, text="Education:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        edu_text = self.user_profile.get_value("professional", "education")
        edu_display = (
            f"{len(edu_text)} entries (Edit not available here)"
            if edu_text
            else "No entries"
        )
        ttk.Label(prof_frame, text=edu_display).grid(
            row=row, column=1, sticky=tk.W, pady=2
        )
        row += 1

        # --- Buttons ---
        button_frame = ttk.Frame(frame, padding="10")
        button_frame.grid(row=3, column=0, sticky=tk.E)

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_close)
        cancel_button.pack(side=tk.RIGHT)

    def load_settings(self):
        logger.debug("Loading profile settings into window.")
        for (section, key), var in self.vars.items():
            value = self.user_profile.get_value(section, key)
            if isinstance(value, list):
                # Join list items (like skills) into a comma-separated string for the Entry
                var.set(", ".join(map(str, value)))
            elif value is not None:
                var.set(str(value))
            else:
                var.set("")  # Ensure empty string if None

    def save_settings(self):
        logger.info("Saving profile settings from window.")
        changed = False
        for (section, key), var in self.vars.items():
            new_value_str = var.get()
            current_value = self.user_profile.get_value(section, key)

            # Handle list conversion for skills
            if key == "skills":
                new_value_list = [
                    s.strip() for s in new_value_str.split(",") if s.strip()
                ]
                if current_value != new_value_list:
                    if self.user_profile.update(section, key, new_value_list):
                        changed = True
                    else:
                        logger.error(f"Failed to update profile field {section}.{key}")
                        messagebox.showerror("Error", f"Failed to save {key}.")
                        return  # Stop saving on error
            # Handle other fields (convert back if necessary, though profile stores as is)
            else:
                # Check if value actually changed (comparing string representation for simplicity)
                current_value_str = ""
                if isinstance(current_value, list):
                    current_value_str = ", ".join(map(str, current_value))
                elif current_value is not None:
                    current_value_str = str(current_value)

                if new_value_str != current_value_str:
                    if self.user_profile.update(
                        section, key, new_value_str
                    ):  # Save string value directly
                        changed = True
                    else:
                        logger.error(f"Failed to update profile field {section}.{key}")
                        messagebox.showerror("Error", f"Failed to save {key}.")
                        return  # Stop saving on error

        if changed:
            messagebox.showinfo("Success", "Profile updated successfully.", parent=self)
            logger.info("Profile successfully updated via settings window.")
        else:
            messagebox.showinfo(
                "No Changes", "No changes detected in the profile.", parent=self
            )

        self.on_close()  # Close after saving


class LLMSettingsWindow(SettingsWindowBase):
    """Window for managing LLM settings"""

    def __init__(self, app_instance):
        self.llm_manager = app_instance.llm_manager
        self.vars = {}
        super().__init__(app_instance, "LLM Settings")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Provider Selection ---
        provider_frame = ttk.LabelFrame(frame, text="LLM Provider", padding="10")
        provider_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        provider_frame.columnconfigure(1, weight=1)

        ttk.Label(provider_frame, text="Provider:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.vars["provider"] = tk.StringVar()
        provider_options = ["openai", "ollama", "none"]
        provider_menu = ttk.OptionMenu(
            provider_frame,
            self.vars["provider"],
            "",
            *provider_options,
            command=self._provider_changed,
        )
        provider_menu.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        # --- OpenAI Specific Settings ---
        self.openai_frame = ttk.Frame(provider_frame)  # Hidden by default
        self.openai_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.openai_frame.columnconfigure(1, weight=1)

        ttk.Label(self.openai_frame, text="API Key:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.vars["api_key"] = tk.StringVar()
        api_key_entry = ttk.Entry(
            self.openai_frame, textvariable=self.vars["api_key"], show="*", width=40
        )
        api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(self.openai_frame, text="Model:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.vars["openai_model"] = tk.StringVar()
        openai_model_entry = ttk.Entry(
            self.openai_frame, textvariable=self.vars["openai_model"], width=40
        )
        openai_model_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        # Could use OptionMenu with common models: gpt-4o, gpt-4-turbo, gpt-3.5-turbo

        # --- Ollama Specific Settings ---
        self.ollama_frame = ttk.Frame(provider_frame)  # Hidden by default
        self.ollama_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.ollama_frame.columnconfigure(1, weight=1)

        ttk.Label(self.ollama_frame, text="Base URL:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.vars["ollama_base_url"] = tk.StringVar()
        ollama_url_entry = ttk.Entry(
            self.ollama_frame, textvariable=self.vars["ollama_base_url"], width=40
        )
        ollama_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(self.ollama_frame, text="Model:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.vars["ollama_model"] = tk.StringVar()
        ollama_model_entry = ttk.Entry(
            self.ollama_frame, textvariable=self.vars["ollama_model"], width=40
        )
        ollama_model_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        # TODO: Add button to fetch available models from Ollama?

        # --- Common Settings ---
        common_frame = ttk.LabelFrame(frame, text="Common Settings", padding="10")
        common_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        common_frame.columnconfigure(1, weight=1)

        ttk.Label(common_frame, text="Temperature:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.vars["temperature"] = tk.DoubleVar()
        temp_scale = ttk.Scale(
            common_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.vars["temperature"],
        )
        temp_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        temp_label = ttk.Label(common_frame, text="")  # Label to show current value
        temp_label.grid(row=0, column=2, padx=5)
        # Update label when scale changes
        self.vars["temperature"].trace_add(
            "write",
            lambda *args: temp_label.config(
                text=f"{self.vars['temperature'].get():.2f}"
            ),
        )

        ttk.Label(common_frame, text="Max Tokens:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.vars["max_tokens"] = tk.IntVar()
        max_tokens_spinbox = ttk.Spinbox(
            common_frame,
            from_=50,
            to=4000,
            increment=50,
            textvariable=self.vars["max_tokens"],
            width=10,
        )
        max_tokens_spinbox.grid(row=1, column=1, sticky=tk.W, pady=2)

        # --- Buttons ---
        button_frame = ttk.Frame(frame, padding="10")
        button_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.E, tk.W)
        )  # Span and stick E+W
        button_frame.columnconfigure(0, weight=1)  # Make test button push left

        self.test_button = ttk.Button(
            button_frame, text="Test Connection", command=self.test_connection
        )
        self.test_button.grid(row=0, column=0, sticky=tk.W, padx=5)  # Align left

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_button.grid(row=0, column=2, sticky=tk.E, padx=5)  # Align right
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_close)
        cancel_button.grid(row=0, column=1, sticky=tk.E, padx=5)  # Align right

    def load_settings(self):
        logger.debug("Loading LLM settings into window.")
        llm_config = self.config_manager.get("llm")
        if not llm_config:
            logger.error("LLM config section not found!")
            return

        self.vars["provider"].set(llm_config.get("provider", "none"))
        # Load API key placeholder - never load the real key into the UI directly
        self.vars["api_key"].set("********" if llm_config.get("api_key_stored") else "")
        self.vars["openai_model"].set(
            llm_config.get("model", "gpt-4o")
        )  # 'model' is openai specific one now
        self.vars["ollama_base_url"].set(
            llm_config.get("ollama_base_url", "http://localhost:11434")
        )
        self.vars["ollama_model"].set(llm_config.get("ollama_model", "llama3"))
        self.vars["temperature"].set(llm_config.get("temperature", 0.7))
        self.vars["max_tokens"].set(llm_config.get("max_tokens", 1500))

        # Show/hide provider specific frames
        self._provider_changed()

    def _provider_changed(self, *args):
        """Show/hide provider specific settings"""
        provider = self.vars["provider"].get()
        if provider == "openai":
            self.openai_frame.grid()
            self.ollama_frame.grid_remove()
            self.test_button.config(state=tk.NORMAL)
        elif provider == "ollama":
            self.openai_frame.grid_remove()
            self.ollama_frame.grid()
            self.test_button.config(state=tk.NORMAL)
        elif provider == "none":
            self.openai_frame.grid_remove()
            self.ollama_frame.grid_remove()
            self.test_button.config(state=tk.DISABLED)
        else:
            self.openai_frame.grid_remove()
            self.ollama_frame.grid_remove()
            self.test_button.config(state=tk.DISABLED)

    def save_settings(self):
        logger.info("Saving LLM settings from window.")
        provider = self.vars["provider"].get()
        api_key = self.vars["api_key"].get()
        openai_model = self.vars["openai_model"].get()
        ollama_base_url = self.vars["ollama_base_url"].get()
        ollama_model = self.vars["ollama_model"].get()
        temperature = self.vars["temperature"].get()
        max_tokens = self.vars["max_tokens"].get()

        # Update config, don't save file immediately
        self.config_manager.set("llm", "provider", provider, save=False)
        self.config_manager.set(
            "llm", "model", openai_model, save=False
        )  # OpenAI model key
        self.config_manager.set("llm", "ollama_base_url", ollama_base_url, save=False)
        self.config_manager.set("llm", "ollama_model", ollama_model, save=False)
        self.config_manager.set("llm", "temperature", temperature, save=False)
        self.config_manager.set("llm", "max_tokens", max_tokens, save=False)

        # Handle API key separately using keyring
        # Only save if the key looks like it was changed (not the placeholder)
        if provider == "openai" and api_key and api_key != "********":
            success = self.config_manager.set("llm", "api_key", api_key, save=False)
            if not success:
                messagebox.showerror(
                    "Error", "Failed to save API key securely.", parent=self
                )
                # Don't close window if key saving failed
                return
        elif provider == "openai" and not api_key:  # User cleared the key
            success = self.config_manager.set(
                "llm", "api_key", None, save=False
            )  # Pass None to clear

        # Now save the entire config file
        if self.config_manager.save_config():
            messagebox.showinfo("Success", "LLM settings saved.", parent=self)
            # Reload LLM manager with new settings
            self.llm_manager._setup_client()
            self.on_close()
        else:
            messagebox.showerror(
                "Error", "Failed to save configuration file.", parent=self
            )

    def test_connection(self):
        """Test the LLM connection based on current UI settings."""
        logger.info("Test Connection button clicked.")
        # Temporarily apply UI settings to config for testing
        # This is slightly risky if the user cancels later, but necessary for test
        provider = self.vars["provider"].get()
        api_key = self.vars["api_key"].get()
        openai_model = self.vars["openai_model"].get()
        ollama_base_url = self.vars["ollama_base_url"].get()
        ollama_model = self.vars["ollama_model"].get()

        # Create a temporary config state for testing
        original_config = (
            self.config_manager.config.copy()
        )  # Shallow copy might be enough
        original_api_key_stored = self.config_manager.get("llm", "api_key_stored")

        try:
            # Apply UI settings temporarily
            self.config_manager.set("llm", "provider", provider, save=False)
            self.config_manager.set("llm", "model", openai_model, save=False)
            self.config_manager.set(
                "llm", "ollama_base_url", ollama_base_url, save=False
            )
            self.config_manager.set("llm", "ollama_model", ollama_model, save=False)

            # Handle temporary API key setting for test
            temp_key_to_test = None
            if provider == "openai":
                if api_key and api_key != "********":
                    temp_key_to_test = api_key
                    # Temporarily pretend the key is stored for the test logic
                    self.config_manager.set("llm", "api_key_stored", True, save=False)
                    # Hack: Temporarily store in keyring ONLY FOR THE TEST? Risky.
                    # Better: Pass the key directly to the test function or LLMManager?
                    # Let's modify LLMManager test to accept an optional key override
                    keyring.set_password(
                        APP_NAME, f"{provider}_api_key_test", temp_key_to_test
                    )  # Use temp name

                elif not api_key:  # Key cleared in UI
                    self.config_manager.set("llm", "api_key_stored", False, save=False)
                # else: key is placeholder, test using potentially existing stored key

            # Test connection using the (potentially modified) config
            self.test_button.config(text="Testing...", state=tk.DISABLED)
            self.update_idletasks()

            # Need to run the test in a thread? No, test_connection handles network internally
            success, message = self.llm_manager.test_connection()

            if success:
                messagebox.showinfo("Connection Test", message, parent=self)
            else:
                messagebox.showerror("Connection Test Failed", message, parent=self)

        except Exception as e:
            logger.error(
                f"Unexpected error during connection test setup: {e}", exc_info=True
            )
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred during the test:\n{e}",
                parent=self,
            )
        finally:
            # Restore original config state regardless of test outcome
            self.config_manager.config = original_config
            # Specifically restore the api_key_stored flag
            self.config_manager.set(
                "llm", "api_key_stored", original_api_key_stored, save=False
            )
            # Clean up temporary test key if created
            if provider == "openai" and temp_key_to_test:
                try:
                    keyring.delete_password(APP_NAME, f"{provider}_api_key_test")
                except:
                    pass  # Ignore if deletion fails

            self.test_button.config(text="Test Connection", state=tk.NORMAL)


class TemplateManagerWindow(SettingsWindowBase):
    """Window for managing simple text templates (Basic Implementation)"""

    def __init__(self, app_instance):
        self.vars = {}
        super().__init__(app_instance, "Template Manager")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(frame, text="Manage simple text templates:").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        self.template_listbox = tk.Listbox(frame, height=10, width=50)
        self.template_listbox.grid(
            row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E)
        )
        self.template_listbox.bind("<<ListboxSelect>>", self.on_template_select)

        scrollbar = ttk.Scrollbar(
            frame, orient=tk.VERTICAL, command=self.template_listbox.yview
        )
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.template_listbox.config(yscrollcommand=scrollbar.set)

        # Entry fields for editing/adding
        ttk.Label(frame, text="Template Name:").grid(row=2, column=0, sticky=tk.W)
        self.vars["template_name"] = tk.StringVar()
        self.name_entry = ttk.Entry(
            frame, textvariable=self.vars["template_name"], width=40
        )
        self.name_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(frame, text="Template Content:").grid(
            row=3, column=0, sticky=(tk.W, tk.N)
        )
        self.vars["template_content"] = tk.StringVar()
        self.content_text = tk.Text(frame, height=5, width=40, wrap=tk.WORD)
        self.content_text.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

        # Buttons for Add/Update/Delete
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.add_button = ttk.Button(
            button_frame, text="Add New", command=self.add_template
        )
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.update_button = ttk.Button(
            button_frame,
            text="Update Selected",
            command=self.update_template,
            state=tk.DISABLED,
        )
        self.update_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_template,
            state=tk.DISABLED,
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # --- Close Button ---
        close_button_frame = ttk.Frame(frame, padding="10")
        close_button_frame.grid(row=5, column=0, columnspan=2, sticky=tk.E)
        close_button = ttk.Button(
            close_button_frame, text="Close", command=self.on_close
        )
        close_button.pack()

    def load_settings(self):
        """Load templates from config into listbox"""
        logger.debug("Loading templates into window.")
        self.template_listbox.delete(0, tk.END)  # Clear existing list
        templates = self.config_manager.get("templates", {})
        if isinstance(templates, dict):
            for name in sorted(templates.keys()):
                self.template_listbox.insert(tk.END, name)
        else:
            logger.error("Templates in config are not a dictionary. Resetting.")
            self.config_manager.set("templates", {})  # Reset if structure is wrong
            self.config_manager.save_config()

    def on_template_select(self, event):
        """Handle selection change in the listbox"""
        selection = self.template_listbox.curselection()
        if selection:
            index = selection[0]
            name = self.template_listbox.get(index)
            content = self.config_manager.get("templates", name)

            self.vars["template_name"].set(name)
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", content if content else "")
            self.name_entry.config(
                state=tk.DISABLED
            )  # Don't allow editing name directly
            self.update_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            self.add_button.config(text="Clear / New")
        else:
            self.clear_fields()

    def clear_fields(self):
        """Clear input fields and reset button states"""
        self.vars["template_name"].set("")
        self.content_text.delete("1.0", tk.END)
        self.name_entry.config(state=tk.NORMAL)
        self.update_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.add_button.config(text="Add New")
        self.template_listbox.selection_clear(0, tk.END)

    def add_template(self):
        """Add a new template or clear fields if in edit mode"""
        if self.add_button.cget("text") == "Clear / New":
            self.clear_fields()
            return

        name = self.vars["template_name"].get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not name or not content:
            messagebox.showwarning(
                "Missing Info",
                "Template name and content cannot be empty.",
                parent=self,
            )
            return

        templates = self.config_manager.get("templates", {})
        if name in templates:
            messagebox.showerror(
                "Error", f"Template name '{name}' already exists.", parent=self
            )
            return

        templates[name] = content
        if self.config_manager.set("templates", name, content):  # Saves implicitly
            logger.info(f"Added new template: '{name}'")
            self.load_settings()  # Refresh list
            self.clear_fields()
            # Select the newly added item?
            # try:
            #     idx = list(self.template_listbox.get(0, tk.END)).index(name)
            #     self.template_listbox.select_set(idx)
            #     self.on_template_select(None) # Update fields
            # except ValueError: pass
        else:
            messagebox.showerror(
                "Error", "Failed to save the new template.", parent=self
            )

    def update_template(self):
        """Update the content of the selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        name = self.vars["template_name"].get()  # Get name from (disabled) entry
        new_content = self.content_text.get("1.0", tk.END).strip()

        if not new_content:
            messagebox.showwarning(
                "Missing Info", "Template content cannot be empty.", parent=self
            )
            return

        if self.config_manager.set("templates", name, new_content):  # Saves implicitly
            logger.info(f"Updated template: '{name}'")
            messagebox.showinfo("Success", f"Template '{name}' updated.", parent=self)
            # No need to reload list, content just changed
        else:
            messagebox.showerror("Error", "Failed to update the template.", parent=self)

    def delete_template(self):
        """Delete the selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        name = self.vars["template_name"].get()
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the template '{name}'?",
            parent=self,
        ):
            return

        templates = self.config_manager.get("templates", {})
        if name in templates:
            del templates[name]
            # Need to save the whole templates dict back
            if self.config_manager.save_config(
                {"templates": templates}
            ):  # Pass the modified dict
                logger.info(f"Deleted template: '{name}'")
                self.load_settings()  # Refresh list
                self.clear_fields()
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to save changes after deleting template.",
                    parent=self,
                )
                # Might need to reload original config if save failed
                self.config_manager._load_config()  # Reload config from file
                self.load_settings()  # Refresh list again
        else:
            messagebox.showerror(
                "Error", "Template not found in configuration.", parent=self
            )
            self.load_settings()  # Refresh list in case of inconsistency


# --- 主应用类 ---
class SmartFillApp(rumps.App):
    """SmartFill.AI主应用类"""

    def __init__(self):
        super(SmartFillApp, self).__init__(
            APP_NAME, icon=ICON_FILE, quit_button=None
        )  # Use None for custom quit later
        logger.info(f"Initializing {APP_NAME} v{APP_VERSION}")

        # Check for icon file
        if not os.path.exists(ICON_FILE):
            logger.warning(f"Icon file '{ICON_FILE}' not found. Using default icon.")
            # rumps might show a default icon or error; consider creating a fallback icon if needed.
            self.icon = None  # Let rumps handle default
        else:
            self.icon = ICON_FILE

        # Initialize core components
        try:
            self.config_manager = ConfigManager()
            self.llm_manager = LLMManager(self.config_manager)
            self.context_analyzer = ContextAnalyzer(self.llm_manager)
            self.accessibility_manager = AccessibilityManager.sharedManager()

            # Load current user profile based on config
            active_profile_id = self.config_manager.get("active_profile", "default")
            self.user_profile = UserProfile(active_profile_id)
            logger.info(f"Loaded active profile: '{active_profile_id}'")

        except Exception as e:
            logger.critical(f"Failed to initialize core components: {e}", exc_info=True)
            rumps.alert(
                title=f"{APP_NAME} Error",
                message=f"Initialization failed:\n{e}\n\nCheck logs at {LOG_FILE}",
            )
            # Decide whether to exit or continue in a degraded state
            # For now, exit might be safer if core components failed
            sys.exit(1)

        # State variable for Tkinter windows
        self.settings_windows = {}  # Keep track of open windows

        # Set up menu
        self._build_menu()

        # Initial permission check (non-blocking)
        self.check_accessibility(None, notify_if_missing=True)

        # Set up global shortcut (placeholder)
        self._setup_global_shortcut()

        # Timer for periodic checks/updates if needed (e.g., re-check permissions)
        self.timer = rumps.Timer(self.periodic_check, 300)  # Check every 5 minutes
        self.timer.start()

        logger.info("SmartFill.AI initialized successfully.")

    def _build_menu(self):
        """Builds or rebuilds the status bar menu."""
        self.menu.clear()  # Clear existing items
        self.menu = [
            rumps.MenuItem(f"Smart Fill Here", callback=self.trigger_smart_fill),
            None,
            {
                "Profile": [
                    rumps.MenuItem(
                        f"Active: {self.user_profile.profile_id}", callback=None
                    ),  # Display active
                    rumps.MenuItem(
                        "Edit Profile...", callback=self.open_profile_settings
                    ),
                    # TODO: Add profile switching functionality if needed
                ]
            },
            {
                "Settings": [
                    rumps.MenuItem("LLM Settings...", callback=self.open_llm_settings),
                    rumps.MenuItem(
                        "Template Manager...", callback=self.open_template_manager
                    ),
                    # Add other settings like UI, shortcuts later
                ]
            },
            {
                "Help & Info": [
                    rumps.MenuItem(
                        "Check Accessibility Permissions",
                        callback=lambda _: self.check_accessibility(
                            _, notify_if_missing=True, show_success=True
                        ),
                    ),
                    rumps.MenuItem("View Logs", callback=self.view_logs),
                    rumps.MenuItem(f"About {APP_NAME}...", callback=self.show_about),
                    rumps.MenuItem(
                        "Visit Website...", callback=self.open_website
                    ),  # Add website URL
                ]
            },
            None,
            rumps.MenuItem(f"Quit {APP_NAME}", callback=self.quit_app),
        ]

    def periodic_check(self, sender):
        """Timer callback for periodic tasks."""
        logger.debug("Performing periodic check...")
        # Example: Re-check permissions silently and update config if changed
        current_perms = self.accessibility_manager.check_permissions(notify=False)
        stored_perms = self.config_manager.get("accessibility", "permissions_granted")
        if current_perms != stored_perms:
            logger.info(
                f"Accessibility permissions changed. Updating config to: {current_perms}"
            )
            self.config_manager.set(
                "accessibility", "permissions_granted", current_perms
            )

    def check_accessibility(self, _, notify_if_missing=True, show_success=False):
        """Check accessibility permissions and update config."""
        logger.info("Checking accessibility permissions...")
        has_perms = self.accessibility_manager.check_permissions(
            notify=False
        )  # Check without prompt first
        self.config_manager.set(
            "accessibility", "permissions_granted", has_perms
        )  # Update config

        if not has_perms and notify_if_missing:
            logger.warning("Accessibility permissions missing. Prompting user.")
            response = rumps.alert(
                title=f"{APP_NAME} - Permissions Required",
                message=f"{APP_NAME} requires Accessibility permissions to read context and fill fields.\n\nPlease grant access in System Settings -> Privacy & Security -> Accessibility.",
                ok="Open Settings",
                cancel="Later",
            )
            if response == 1:  # OK button clicked
                self.accessibility_manager.request_permissions()
        elif has_perms and show_success:
            rumps.notification(
                title=APP_NAME,
                subtitle="Permissions OK",
                message="Accessibility access is enabled.",
            )
            logger.info("Accessibility permissions OK.")
        elif (
            not has_perms and show_success
        ):  # If requested to show status even if missing
            rumps.notification(
                title=APP_NAME,
                subtitle="Permissions Missing",
                message="Accessibility access is required.",
            )

        return has_perms

    def _setup_global_shortcut(self):
        """Placeholder for setting up a global shortcut."""
        shortcut = self.config_manager.get("ui", "shortcut")
        logger.info(f"Global shortcut configured as: {shortcut}")
        logger.warning(
            "Actual global shortcut registration is not implemented in this version."
        )
        logger.warning("Use the status bar menu ('Smart Fill Here') to trigger.")
        # --- Implementation Notes ---
        # Reliable global shortcuts in Python on macOS require libraries like:
        # 1. pynput: Cross-platform, might have issues with macOS permissions/event taps.
        # 2. PyObjC + Carbon Event Manager (older) or NSEvent monitoring (newer): More native but complex.
        # Example using NSEvent (Conceptual - requires proper setup):
        # NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        #     AppKit.NSKeyDownMask, # Or KeyUpMask
        #     self.handle_shortcut_event_ # Needs to be an @objc.IBAction decorated method
        # )
        # Need to parse modifier flags and key codes within the handler.
        # This is non-trivial and needs careful integration with the run loop.

    # --- Menu Callbacks ---

    def trigger_smart_fill(self, sender):
        """Trigger the smart fill process."""
        logger.info("Smart Fill triggered from menu.")

        # 1. Check Permissions first
        if not self.check_accessibility(None, notify_if_missing=True):
            logger.warning("Smart Fill aborted: Accessibility permissions missing.")
            return

        # 2. Get Focused Element Info
        logger.debug("Getting focused element info...")
        element_info = self.accessibility_manager.get_focused_element_info()
        logger.debug(f"Focused element info: {element_info}")

        if not element_info or "error" in element_info:
            error_msg = (
                element_info.get("error", "Unknown error")
                if element_info
                else "Could not get element info"
            )
            logger.error(f"Smart Fill failed: Cannot get context. Error: {error_msg}")
            rumps.notification(
                title=APP_NAME,
                subtitle="Context Error",
                message=f"Could not get information about the focused field.\nError: {error_msg}",
            )
            return

        # Check if element is usable (enabled/editable)
        if not element_info.get(
            "editable", True
        ):  # Assume editable if key missing, but check if False
            logger.warning("Smart Fill target element is not enabled/editable.")
            rumps.notification(
                title=APP_NAME,
                subtitle="Fill Error",
                message="The target field is not editable.",
            )
            return

        # 3. Analyze Context (Potentially show "Analyzing..." state?)
        rumps.notification(
            title=APP_NAME, subtitle="Analyzing context...", message="Please wait."
        )
        context_analysis = self.context_analyzer.analyze_context(element_info)
        logger.info(f"Context analysis result: {context_analysis}")

        # 4. Generate Content (Requires LLM call - can take time)
        rumps.notification(
            title=APP_NAME,
            subtitle="Generating content...",
            message=f"Detected field: {context_analysis.get('field_type', 'Unknown')}",
        )
        # Run generation in a separate thread to avoid blocking the UI thread
        # However, rumps might handle this okay? Let's try direct first. If it hangs, use thread.
        try:
            content = self.context_analyzer.generate_content(
                context_analysis, self.user_profile, element_info
            )
        except Exception as e:
            logger.error(f"Error during content generation: {e}", exc_info=True)
            rumps.notification(
                title=APP_NAME,
                subtitle="Generation Error",
                message=f"Failed to generate content: {e}",
            )
            return

        # 5. Insert Content
        if content:
            if context_analysis.get("field_type") == "Password":
                # Special handling for passwords - maybe show confirmation?
                logger.info("Password field detected. Skipping automatic insertion.")
                rumps.alert(
                    title=APP_NAME,
                    message="Password field detected. For security, please paste manually or use a password manager.",
                )
                # Optionally copy to clipboard? Be careful with security.
                # import pyperclip
                # pyperclip.copy(content)
                # rumps.notification(title=APP_NAME, subtitle="Password Ready", message="Password copied to clipboard (use with caution).")
                return

            logger.info(
                f"Attempting to insert content (first 30 chars): {content[:30]}..."
            )
            success = self.accessibility_manager.insert_text(content)
            if success:
                logger.info("Smart Fill successful.")
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Fill Successful",
                    message=f"Filled '{context_analysis.get('field_type', 'field')}'.",
                )
            else:
                logger.error("Smart Fill failed: Could not insert text.")
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Fill Failed",
                    message="Could not insert the generated text into the field.",
                )
        else:
            logger.warning("Smart Fill failed: Generated content was empty.")
            rumps.notification(
                title=APP_NAME,
                subtitle="Fill Failed",
                message="Could not generate suitable content for this field.",
            )

    def _open_settings_window(self, window_class, window_key):
        """Helper to open and manage singleton settings windows."""
        if (
            self.settings_windows.get(window_key)
            and self.settings_windows[window_key].winfo_exists()
        ):
            logger.debug(f"{window_key} window already open. Bringing to front.")
            self.settings_windows[window_key].lift()
            self.settings_windows[window_key].focus_set()
        else:
            logger.debug(f"Creating new {window_key} window.")
            # Tkinter setup might need to run on main thread implicitly
            # rumps callbacks run on the main thread, so this should be okay.
            try:
                # Create Tk root temporarily if none exists (for standalone Tk windows)
                # root = tk.Tk()
                # root.withdraw() # Hide the main root window

                new_window = window_class(self)
                self.settings_windows[window_key] = new_window
                # Ensure the window closes properly and updates state
                new_window.protocol(
                    "WM_DELETE_WINDOW",
                    lambda: self._on_settings_window_close(window_key),
                )
                # new_window.mainloop() # DON'T call mainloop here - rumps handles the event loop
            except Exception as e:
                logger.error(f"Failed to open {window_key} window: {e}", exc_info=True)
                messagebox.showerror("Error", f"Could not open settings window:\n{e}")

    def _on_settings_window_close(self, window_key):
        """Callback when a settings window is closed."""
        logger.debug(f"{window_key} window closed.")
        if window_key in self.settings_windows:
            if self.settings_windows[window_key].winfo_exists():
                self.settings_windows[window_key].destroy()
            del self.settings_windows[window_key]

    def open_profile_settings(self, sender):
        """Open the profile settings window."""
        logger.info("Menu: Open Profile Settings clicked.")
        self._open_settings_window(ProfileSettingsWindow, "profile")

    def open_llm_settings(self, sender):
        """Open the LLM settings window."""
        logger.info("Menu: Open LLM Settings clicked.")
        self._open_settings_window(LLMSettingsWindow, "llm")

    def open_template_manager(self, sender):
        """Open the Template Manager window."""
        logger.info("Menu: Open Template Manager clicked.")
        self._open_settings_window(TemplateManagerWindow, "template")

    def view_logs(self, sender):
        """Open the log file in the default text editor."""
        logger.info("Menu: View Logs clicked.")
        try:
            if os.path.exists(LOG_FILE):
                # Use NSWorkspace to open the file, more native than webbrowser
                workspace = AppKit.NSWorkspace.sharedWorkspace()
                url = AppKit.NSURL.fileURLWithPath_(LOG_FILE)
                workspace.openURL_(url)
            else:
                messagebox.showinfo(
                    "Log File", "Log file does not exist yet.", parent=None
                )  # No parent for simple info box
        except Exception as e:
            logger.error(f"Failed to open log file {LOG_FILE}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Could not open log file:\n{e}", parent=None)

    def show_about(self, sender):
        """Show the about dialog."""
        logger.info("Menu: About clicked.")
        rumps.alert(
            title=f"About {APP_NAME}",
            message=f"{APP_NAME} v{APP_VERSION}\n\nAI-Powered Intelligent Filling Assistant\n\n(c) 2024 Your Name/Company\n\nConfiguration Path:\n{CONFIG_DIR}",
            ok="OK",
        )

    def open_website(self, sender):
        """Open the application's website."""
        logger.info("Menu: Visit Website clicked.")
        # Replace with your actual URL
        website_url = "https://github.com/your-repo/SmartFill.AI"  # Example URL
        try:
            webbrowser.open(website_url)
        except Exception as e:
            logger.error(f"Failed to open website {website_url}: {e}")
            messagebox.showerror("Error", f"Could not open website:\n{e}", parent=None)

    def quit_app(self, sender):
        """Cleanly quit the application."""
        logger.info("Quit command received.")
        # Perform any cleanup here if needed (e.g., stop threads)
        self.timer.stop()  # Stop periodic timer
        logger.info("SmartFill.AI application stopping.")
        rumps.quit_application(sender)


# --- Main Execution ---

if __name__ == "__main__":
    # Ensure PyObjC resources are initialized properly for background app
    # This helps with GUI elements and event handling in some cases
    # AppKit.NSApplication.sharedApplication() # Initialize shared application if needed

    # Argument Parsing (Optional)
    parser = argparse.ArgumentParser(description=f"{APP_NAME} - AI Filling Assistant")
    # Add arguments if needed, e.g., --debug
    # parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # if args.debug:
    #     logger.setLevel(logging.DEBUG)
    #     for handler in logger.handlers:
    #         handler.setLevel(logging.DEBUG)
    #     logger.debug("Debug logging enabled.")

    # Check for essential dependencies early
    missing_deps = []
    try:
        import AppKit
    except ImportError:
        missing_deps.append("pyobjc-core / pyobjc-framework-Cocoa")
    try:
        import Quartz
    except ImportError:
        missing_deps.append("pyobjc-framework-Quartz")
    try:
        import rumps
    except ImportError:
        missing_deps.append("rumps")
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")
    try:
        import keyring
    except ImportError:
        missing_deps.append("keyring")
    try:
        import cryptography
    except ImportError:
        missing_deps.append("cryptography")
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (usually included with Python)")

    if missing_deps:
        dep_str = "\n - ".join(missing_deps)
        error_msg = f"Critical dependencies missing:\n - {dep_str}\n\nPlease install them (e.g., using pip) and restart the application."
        print(error_msg, file=sys.stderr)
        # Try to show a GUI alert if possible, otherwise just print
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(f"{APP_NAME} Dependency Error", error_msg)
        except Exception as e:
            print(f"(Could not show GUI error message: {e})", file=sys.stderr)
        sys.exit(1)

    # Create and run the app
    try:
        app = SmartFillApp()
        app.run()
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
        # Attempt to show a final error message
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                f"{APP_NAME} Critical Error",
                f"A critical error occurred:\n{e}\n\nCheck logs for details:\n{LOG_FILE}",
            )
        except Exception as alert_e:
            print(
                f"Critical error: {e}\n(Could not show GUI alert: {alert_e})",
                file=sys.stderr,
            )
        sys.exit(1)
