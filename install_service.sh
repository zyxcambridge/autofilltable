#!/bin/bash

# SmartFill.AI Resume Auto-Fill Service Installer
# This script installs the necessary components for the SmartFill.AI resume auto-fill service

echo "Installing SmartFill.AI Resume Auto-Fill Service..."

# Create necessary directories
mkdir -p ~/Library/Services
mkdir -p ~/Library/Logs/SmartFill.AI
mkdir -p ~/Library/Application\ Support/SmartFill.AI

# Copy Automator service to Services directory
if [ -d "AutomatorService/SmartFill_Resume.workflow" ]; then
    cp -R "AutomatorService/SmartFill_Resume.workflow" ~/Library/Services/
    echo "✅ Installed Automator service"
else
    echo "❌ Error: Automator service not found"
    exit 1
fi

# Make bridge scripts executable
chmod +x autofill_bridge.py
chmod +x simple_bridge.py
echo "✅ Made bridge scripts executable"

# Check for required Python packages
echo "Checking Python dependencies..."
pip3 install --user rumps pyobjc-framework-Quartz pyobjc-core openai requests cryptography keyring tk Pillow
echo "✅ Installed Python dependencies"

# Restart the Services menu to recognize the new service
echo "Restarting Services menu..."
/System/Library/CoreServices/pbs -flush
killall Finder
echo "✅ Services menu restarted"

echo ""
echo "Installation complete! You can now use the 'SmartFill Resume Info' option in the right-click menu."
echo "To use the service:"
echo "1. Select text in any application"
echo "2. Right-click and select 'Services > SmartFill Resume Info'"
echo "3. The appropriate resume information will be inserted"
echo ""
echo "Note: You may need to grant accessibility permissions to the service when prompted."
