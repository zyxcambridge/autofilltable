#!/bin/bash

# This script converts SVG icons to PNG for browser compatibility
# Requires Inkscape or other SVG to PNG converter

# Check if Inkscape is installed
if command -v inkscape >/dev/null 2>&1; then
  echo "Converting icons using Inkscape..."
  
  # Convert icon128.svg to various sizes
  inkscape -w 16 -h 16 icons/icon128.svg -o icons/icon16.png
  inkscape -w 48 -h 48 icons/icon128.svg -o icons/icon48.png
  inkscape -w 128 -h 128 icons/icon128.svg -o icons/icon128.png
  
  echo "Icon conversion complete!"
else
  echo "Inkscape not found. Please install Inkscape or manually convert the SVG icons to PNG."
  echo "You need the following sizes: 16x16, 48x48, and 128x128 pixels."
fi
