#!/bin/bash

# Replace these variables with your GitHub information
GITHUB_USERNAME="your-username"
REPO_NAME="autofilltable"

# Add the GitHub repository as a remote
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Push the code to GitHub
git push -u origin main

echo "Repository has been pushed to GitHub at https://github.com/$GITHUB_USERNAME/$REPO_NAME"
