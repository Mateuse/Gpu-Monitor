#!/usr/bin/env python3
"""
GPU Monitor - A simple GUI application to monitor NVIDIA GPU status
using nvidia-smi with configurable update intervals.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
import subprocess
import threading
import time
import json
from typing import Dict, List, Optional
from collections import defaultdict


class GPUMonitor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GPU Monitor")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configuration
        self.update_interval = tk.IntVar(value=5)  # Default 5 seconds
        self.is_monitoring = False
        self.monitor_thread = None
        
        # GPU data storage
        self.gpu_data = defaultdict(dict)
        self.gpu_cards = {}
        
        self.apply_theme()
        self.setup_ui()
        self.check_nvidia_smi()
    
    def apply_theme(self):
        """Apply a modern ttk theme and widget styles."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            # Fallback to default theme
            pass

        # Base fonts
        base_font = tkfont.nametofont("TkDefaultFont")
        title_font = (base_font.actual('family'), max(base_font.actual('size') + 2, 11), 'bold')
        metric_font = (base_font.actual('family'), base_font.actual('size'))
        small_font = (base_font.actual('family'), max(base_font.actual('size') - 1, 8))

        # Colors
        bg = '#0f172a'  # slate-900
        panel_bg = '#111827'  # gray-900
        card_bg = '#111827'
        fg = '#e5e7eb'  # gray-200
        muted = '#9ca3af'  # gray-400
        accent = '#3b82f6'  # blue-500
        success = '#22c55e'  # green-500
        warn = '#f59e0b'  # amber-500
        danger = '#ef4444'  # red-500

        # Window background
        self.root.configure(bg=bg)

        # General styles
        style.configure('TFrame', background=bg)
        style.configure('TLabelframe', background=bg, foreground=fg)
        style.configure('TLabelframe.Label', background=bg, foreground=fg, font=title_font)
        style.configure('TLabel', background=bg, foreground=fg, font=metric_font)
        style.configure('Small.TLabel', background=bg, foreground=muted, font=small_font)
        style.configure('Title.TLabel', background=bg, foreground=fg, font=title_font)
        style.configure('Muted.TLabel', background=bg, foreground=muted, font=metric_font)
        style.configure('TempWarn.TLabel', background=bg, foreground=warn, font=metric_font)
        style.configure('TempHigh.TLabel', background=bg, foreground=danger, font=metric_font)
        style.configure('TempOk.TLabel', background=bg, foreground=success, font=metric_font)
        style.configure('Card.TLabelframe', background=card_bg, foreground=fg)
        style.configure('Card.TLabelframe.Label', background=card_bg, foreground=fg, font=title_font)
        style.configure('Card.TFrame', background=card_bg)

        # Buttons, Spinbox
        style.configure('TButton', padding=6)
        style.map('TButton', background=[('active', accent)])
        style.configure('TSpinbox', padding=4)

        # Progress bars
        style.configure('Util.Horizontal.TProgressbar', troughcolor=panel_bg, background=accent)
        style.configure('Mem.Horizontal.TProgressbar', troughcolor=panel_bg, background=success)

    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10", style='Card.TLabelframe')
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Update interval control
        ttk.Label(control_frame, text="Update Interval (seconds):").grid(row=0, column=0, padx=(0, 5))
        interval_spinbox = ttk.Spinbox(control_frame, from_=1, to=60, width=10, 
                                     textvariable=self.update_interval)
        interval_spinbox.grid(row=0, column=1, padx=(0, 10))
        
        # Start/Stop button
        self.monitor_button = ttk.Button(control_frame, text="Start Monitoring", 
                                       command=self.toggle_monitoring)
        self.monitor_button.grid(row=0, column=2, padx=(0, 10))
        
        # Manual refresh button
        refresh_button = ttk.Button(control_frame, text="Refresh Now", 
                                  command=self.refresh_gpu_data)
        refresh_button.grid(row=0, column=3)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready", style='Muted.TLabel')
        self.status_label.grid(row=1, column=0, columnspan=4, pady=(5, 0))
        
        # GPU information display
        info_frame = ttk.LabelFrame(main_frame, text="GPU Information", padding="10", style='Card.TLabelframe')
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create notebook for tabbed display
        self.notebook = ttk.Notebook(info_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.dashboard_container = ttk.Frame(self.dashboard_frame, padding="5", style='TFrame')
        self.dashboard_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.dashboard_frame.columnconfigure(0, weight=1)
        self.dashboard_frame.rowconfigure(0, weight=1)

        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Summary")
        
        # Summary text widget
        self.summary_text = tk.Text(self.summary_frame, wrap=tk.WORD, height=15, bg='#0b1220', fg='#e5e7eb', insertbackground='#e5e7eb')
        summary_scrollbar = ttk.Scrollbar(self.summary_frame, orient=tk.VERTICAL, 
                                        command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        summary_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.rowconfigure(0, weight=1)
        
        # Detailed tab
        self.detailed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.detailed_frame, text="Detailed")
        
        # Detailed text widget
        self.detailed_text = tk.Text(self.detailed_frame, wrap=tk.WORD, height=15, bg='#0b1220', fg='#e5e7eb', insertbackground='#e5e7eb')
        detailed_scrollbar = ttk.Scrollbar(self.detailed_frame, orient=tk.VERTICAL, 
                                         command=self.detailed_text.yview)
        self.detailed_text.configure(yscrollcommand=detailed_scrollbar.set)
        
        self.detailed_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        detailed_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.detailed_frame.columnconfigure(0, weight=1)
        self.detailed_frame.rowconfigure(0, weight=1)
        
        # Raw output tab
        self.raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_frame, text="Raw Output")
        
        # Raw text widget
        self.raw_text = tk.Text(self.raw_frame, wrap=tk.WORD, height=15, bg='#0b1220', fg='#e5e7eb', insertbackground='#e5e7eb')
        raw_scrollbar = ttk.Scrollbar(self.raw_frame, orient=tk.VERTICAL, 
                                    command=self.raw_text.yview)
        self.raw_text.configure(yscrollcommand=raw_scrollbar.set)
        
        self.raw_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        raw_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.raw_frame.columnconfigure(0, weight=1)
        self.raw_frame.rowconfigure(0, weight=1)

    def clear_dashboard(self):
        for child in self.dashboard_container.winfo_children():
            child.destroy()
        self.gpu_cards = {}

    def get_temp_style(self, temperature_c: int) -> str:
        if temperature_c is None:
            return 'Muted.TLabel'
        if temperature_c >= 80:
            return 'TempHigh.TLabel'
        if temperature_c >= 70:
            return 'TempWarn.TLabel'
        return 'TempOk.TLabel'

    def build_or_update_dashboard(self, gpu_data: Dict):
        """Create or update per-GPU cards in the dashboard."""
        # If GPU set changed, rebuild
        current_ids = set(self.gpu_cards.keys())
        new_ids = set(gpu_data.keys())
        if current_ids != new_ids:
            self.clear_dashboard()
            row = 0
            for gpu_id in sorted(gpu_data.keys(), key=lambda x: int(x)):
                card_widgets = self._create_gpu_card(gpu_id, gpu_data[gpu_id], row)
                self.gpu_cards[gpu_id] = card_widgets
                row += 1

        # Update values
        for gpu_id, info in gpu_data.items():
            if gpu_id in self.gpu_cards:
                self._update_gpu_card(self.gpu_cards[gpu_id], info)

    def _create_gpu_card(self, gpu_id: str, info: Dict, row_index: int) -> Dict[str, object]:
        lf = ttk.LabelFrame(self.dashboard_container, text=f"GPU {gpu_id} — {info.get('name', 'Unknown')}", padding="10", style='Card.TLabelframe')
        lf.grid(row=row_index, column=0, sticky=(tk.W, tk.E), pady=8)
        lf.columnconfigure(1, weight=1)

        # Temperature
        ttk.Label(lf, text="Temperature:", style='Muted.TLabel').grid(row=0, column=0, sticky=tk.W)
        temp_label = ttk.Label(lf, text="-- °C", style=self.get_temp_style(info.get('temperature')))
        temp_label.grid(row=0, column=1, sticky=tk.W)

        # Utilization
        ttk.Label(lf, text="GPU Utilization:", style='Muted.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        util_bar = ttk.Progressbar(lf, style='Util.Horizontal.TProgressbar', maximum=100, value=0)
        util_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(6, 0))
        util_label = ttk.Label(lf, text="0%", style='Small.TLabel')
        util_label.grid(row=1, column=2, sticky=tk.W, padx=(6, 0))

        # Memory
        ttk.Label(lf, text="Memory Usage:", style='Muted.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(6, 0))
        mem_bar = ttk.Progressbar(lf, style='Mem.Horizontal.TProgressbar', maximum=100, value=0)
        mem_bar.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(6, 0))
        mem_label = ttk.Label(lf, text="0 / 0 MB (0%)", style='Small.TLabel')
        mem_label.grid(row=2, column=2, sticky=tk.W, padx=(6, 0))

        # Power
        ttk.Label(lf, text="Power:", style='Muted.TLabel').grid(row=3, column=0, sticky=tk.W, pady=(6, 0))
        power_label = ttk.Label(lf, text="-- W", style='Small.TLabel')
        power_label.grid(row=3, column=1, sticky=tk.W, pady=(6, 0))

        return {
            'frame': lf,
            'temp_label': temp_label,
            'util_bar': util_bar,
            'util_label': util_label,
            'mem_bar': mem_bar,
            'mem_label': mem_label,
            'power_label': power_label,
        }

    def _update_gpu_card(self, widgets: Dict[str, object], info: Dict):
        # Temperature
        temperature = info.get('temperature')
        if isinstance(temperature, (int, float)):
            widgets['temp_label'].configure(text=f"{int(temperature)} °C", style=self.get_temp_style(int(temperature)))
        else:
            widgets['temp_label'].configure(text="-- °C", style='Muted.TLabel')

        # Utilization
        utilization = info.get('utilization')
        try:
            util_val = int(utilization) if utilization is not None else 0
        except Exception:
            util_val = 0
        widgets['util_bar']['value'] = max(0, min(util_val, 100))
        widgets['util_label'].configure(text=f"{util_val}%")

        # Memory
        mem_used = info.get('memory_used') or 0
        mem_total = info.get('memory_total') or 0
        try:
            mem_used_i = int(mem_used)
            mem_total_i = int(mem_total) if int(mem_total) > 0 else 0
        except Exception:
            mem_used_i = 0
            mem_total_i = 0
        mem_pct = int((mem_used_i / mem_total_i) * 100) if mem_total_i else 0
        widgets['mem_bar']['value'] = max(0, min(mem_pct, 100))
        widgets['mem_label'].configure(text=f"{mem_used_i} / {mem_total_i} MB ({mem_pct}%)")

        # Power
        power = info.get('power_draw')
        try:
            power_f = float(power)
            widgets['power_label'].configure(text=f"{power_f:.2f} W")
        except Exception:
            widgets['power_label'].configure(text="-- W")

    
    def check_nvidia_smi(self):
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(['nvidia-smi', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.status_label.config(text="nvidia-smi available")
                return True
            else:
                self.status_label.config(text="nvidia-smi not available")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.status_label.config(text="nvidia-smi not found")
            return False
    
    def get_gpu_data(self) -> Optional[str]:
        """Get GPU data from nvidia-smi."""
        try:
            # Get basic GPU information
            result = subprocess.run(['nvidia-smi', '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def get_detailed_gpu_data(self) -> Optional[str]:
        """Get detailed GPU information."""
        try:
            result = subprocess.run(['nvidia-smi'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def parse_gpu_data(self, data: str) -> Dict:
        """Parse GPU data from nvidia-smi output."""
        gpu_info = defaultdict(dict)
        
        if not data:
            return gpu_info
        
        lines = data.strip().split('\n')
        for line in lines:
            if line.strip():
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 7:
                    gpu_id = parts[0]
                    # Safe conversions
                    def to_int(value):
                        try:
                            return int(float(value))
                        except Exception:
                            return None
                    def to_float(value):
                        try:
                            return float(value)
                        except Exception:
                            return None

                    gpu_info[gpu_id] = {
                        'name': parts[1],
                        'temperature': to_int(parts[2]),
                        'utilization': to_int(parts[3]),
                        'memory_used': to_int(parts[4]),
                        'memory_total': to_int(parts[5]),
                        'power_draw': to_float(parts[6])
                    }
        
        return gpu_info
    
    def format_summary(self, gpu_data: Dict) -> str:
        """Format GPU data for summary display."""
        if not gpu_data:
            return "No GPU data available"
        
        summary = "GPU Summary:\n" + "="*50 + "\n\n"
        
        for gpu_id, info in gpu_data.items():
            summary += f"GPU {gpu_id}: {info['name']}\n"
            summary += f"  Temperature: {info['temperature']}°C\n"
            summary += f"  Utilization: {info['utilization']}%\n"
            summary += f"  Memory: {info['memory_used']}MB / {info['memory_total']}MB\n"
            summary += f"  Power: {info['power_draw']}W\n"
            summary += "\n"
        
        return summary
    
    def refresh_gpu_data(self):
        """Refresh GPU data and update display."""
        if not self.check_nvidia_smi():
            messagebox.showerror("Error", "nvidia-smi is not available")
            return
        
        # Get basic GPU data
        basic_data = self.get_gpu_data()
        if basic_data:
            self.gpu_data = self.parse_gpu_data(basic_data)
        
        # Get detailed data
        detailed_data = self.get_detailed_gpu_data()
        
        # Update dashboard
        self.build_or_update_dashboard(self.gpu_data)

        # Update displays
        self.update_summary_display()
        self.update_detailed_display(detailed_data)
        self.update_raw_display(detailed_data)
        
        # Update status
        timestamp = time.strftime("%H:%M:%S")
        self.status_label.config(text=f"Last updated: {timestamp}")
    
    def update_summary_display(self):
        """Update the summary display."""
        self.summary_text.delete(1.0, tk.END)
        summary = self.format_summary(self.gpu_data)
        self.summary_text.insert(1.0, summary)
    
    def update_detailed_display(self, detailed_data: Optional[str]):
        """Update the detailed display."""
        self.detailed_text.delete(1.0, tk.END)
        if detailed_data:
            self.detailed_text.insert(1.0, detailed_data)
        else:
            self.detailed_text.insert(1.0, "No detailed data available")
    
    def update_raw_display(self, raw_data: Optional[str]):
        """Update the raw output display."""
        self.raw_text.delete(1.0, tk.END)
        if raw_data:
            self.raw_text.insert(1.0, raw_data)
        else:
            self.raw_text.insert(1.0, "No raw data available")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start continuous monitoring."""
        if not self.check_nvidia_smi():
            messagebox.showerror("Error", "nvidia-smi is not available")
            return
        
        self.is_monitoring = True
        self.monitor_button.config(text="Stop Monitoring")
        self.status_label.config(text="Monitoring started...")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.is_monitoring = False
        self.monitor_button.config(text="Start Monitoring")
        self.status_label.config(text="Monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Refresh data in main thread
                self.root.after(0, self.refresh_gpu_data)
                
                # Wait for next update
                time.sleep(self.update_interval.get())
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                break


def main():
    """Main function to run the GPU Monitor application."""
    root = tk.Tk()
    app = GPUMonitor(root)
    
    # Handle window close
    def on_closing():
        app.stop_monitoring()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
