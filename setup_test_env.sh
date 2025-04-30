#!/bin/bash

# Create virtual environment for the test website
python3 -m venv ./test_website_env

# Activate virtual environment
source ./test_website_env/bin/activate

# Install required packages
pip install flask flask-login pandas

# Create project directory structure
mkdir -p ./drug_management_test/{templates,static}
