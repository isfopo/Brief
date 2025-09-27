#!/bin/bash

echo "Setting up Python project with virtual environment..."

if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

if [ ! -d "env" ]; then
    python -m venv env
    echo "Virtual environment created in 'env'"
else
    echo "Virtual environment already exists"
fi

source env/bin/activate
pip install -r requirements.txt

echo "Dependencies installed."
echo "Setup complete. Activate the environment with 'source env/bin/activate'"