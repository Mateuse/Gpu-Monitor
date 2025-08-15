#!/bin/bash

# GPU Monitor Launcher Script
# This script launches the GPU Monitor application

echo "Starting GPU Monitor..."
echo "Checking system requirements..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: nvidia-smi is not available. The application may not work properly."
    echo "Please ensure NVIDIA drivers are installed."
fi

# Check if the main script exists
if [ ! -f "gpu_monitor.py" ]; then
    echo "Error: gpu_monitor.py not found in current directory"
    exit 1
fi

# Run the application
echo "Launching GPU Monitor..."
python3 gpu_monitor.py
