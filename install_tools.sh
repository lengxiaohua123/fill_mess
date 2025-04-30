#!/bin/bash

# Update package list
sudo apt update

# Install required system packages
sudo apt install -y python3-full python3-venv wget

# Create a virtual environment
python3 -m venv ./automation_env

# Activate virtual environment
source ./automation_env/bin/activate

# Install required Python packages in the virtual environment
pip install playwright pandas openpyxl

# 安装 Playwright 浏览器
playwright install

echo "All tools have been installed successfully!"
echo "To activate the virtual environment in the future, use:"
echo "source ~/automation_env/bin/activate"
