# GPU Monitor

A simple GUI application to monitor NVIDIA GPU status using `nvidia-smi` with configurable update intervals.

## Features

- **Real-time GPU Monitoring**: Display GPU temperature, utilization, memory usage, and power consumption
- **Configurable Update Intervals**: Set refresh rates from 1 to 60 seconds
- **Multiple Display Views**: 
  - Summary view with key metrics
  - Detailed view with full nvidia-smi output
  - Raw output view for debugging
- **User-friendly Interface**: Clean, modern GUI built with tkinter
- **Cross-platform**: Works on Ubuntu and other Linux distributions

## Prerequisites

### System Requirements

1. **NVIDIA GPU**: The application requires an NVIDIA GPU with proper drivers installed
2. **nvidia-smi**: NVIDIA System Management Interface must be available
3. **Python 3.6+**: With tkinter support (usually included by default)

### Installing NVIDIA Drivers

If you don't have NVIDIA drivers installed:

```bash
# Check if nvidia-smi is available
nvidia-smi --version

# If not available, install NVIDIA drivers
sudo apt update
sudo apt install nvidia-driver-xxx  # Replace xxx with appropriate version
```

## Installation

1. **Clone or download** the application files to your desired directory

2. **Make the script executable** (optional):
   ```bash
   chmod +x gpu_monitor.py
   ```

3. **Run the application**:
   ```bash
   python3 gpu_monitor.py
   ```

## Usage

### Starting the Application

```bash
python3 gpu_monitor.py
```

### Using the Interface

1. **Set Update Interval**: Use the spinbox to set how often the GPU data should refresh (1-60 seconds)
2. **Start Monitoring**: Click "Start Monitoring" to begin continuous monitoring
3. **Manual Refresh**: Click "Refresh Now" to update data immediately
4. **View Different Tabs**:
   - **Summary**: Key metrics for each GPU
   - **Detailed**: Full nvidia-smi output
   - **Raw Output**: Complete raw output for debugging

### Controls

- **Update Interval**: Set the refresh rate in seconds
- **Start/Stop Monitoring**: Toggle continuous monitoring
- **Refresh Now**: Manually update GPU data
- **Status Display**: Shows current application status and last update time

## Troubleshooting

### Common Issues

1. **"nvidia-smi not found"**
   - Ensure NVIDIA drivers are properly installed
   - Check if `nvidia-smi` is in your PATH
   - Try running `nvidia-smi` directly in terminal

2. **"No GPU data available"**
   - Verify your NVIDIA GPU is detected
   - Check if GPU is being used by other processes
   - Ensure you have proper permissions

3. **GUI not displaying properly**
   - Ensure tkinter is installed: `python3 -c "import tkinter"`
   - Try running with different display settings

### Debugging

- Check the "Raw Output" tab to see the complete nvidia-smi output
- Look at the status label for error messages
- Run `nvidia-smi` directly in terminal to verify it works

## Technical Details

### Architecture

- **GUI Framework**: tkinter (Python standard library)
- **Data Source**: nvidia-smi command-line tool
- **Update Mechanism**: Threading for non-blocking updates
- **Data Parsing**: Custom parser for nvidia-smi CSV output

### Data Collected

The application collects the following GPU metrics:
- GPU index and name
- Temperature (°C)
- GPU utilization (%)
- Memory usage (MB)
- Total memory (MB)
- Power consumption (W)

### Performance

- Minimal CPU usage during monitoring
- Non-blocking GUI updates
- Configurable refresh rates to balance accuracy and performance

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your system meets the prerequisites
3. Test `nvidia-smi` directly in terminal
4. Check the application logs for error messages

## Install as a pip package

You can install this project locally or publish it to PyPI.

### Local editable install (development)

```bash
# From the project root
python3 -m pip install --upgrade pip build
python3 -m pip install -e .

# Run using the console script entry point
gpu-monitor
```

### Build distributions

```bash
python3 -m build
# Artifacts will appear in the dist/ directory (.whl and .tar.gz)
```

### Publish to PyPI (optional)

```bash
python3 -m pip install --upgrade twine
python3 -m build
python3 -m twine upload dist/*
# Enter your PyPI credentials when prompted
```

### Install from source or wheel

```bash
# From a source checkout
python3 -m pip install .

# From a wheel
python3 -m pip install dist/gpu_monitor_gui-0.1.0-py3-none-any.whl
```

### Requirements on end-user machines

- Python 3.8+
- A working `nvidia-smi` in PATH (from NVIDIA drivers)
- Tkinter available for their Python installation (usually included on Ubuntu via `python3-tk`)
