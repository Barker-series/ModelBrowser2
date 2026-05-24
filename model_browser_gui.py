#!/usr/bin/env python3
"""
Model Browser GUI
A graphical interface for starting and managing the Model Browser server
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import sys
import os
import signal
import time
import webbrowser
from pathlib import Path

class ModelBrowserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Model Browser Server")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # Get the directory where this script is located
        if getattr(sys, 'frozen', False):
            # Running as AppImage
            self.script_dir = os.environ.get('APPDIR', os.path.dirname(sys.executable))
        else:
            # Running as script
            self.script_dir = os.path.dirname(os.path.abspath(__file__))

        self.model_server_path = os.path.join(self.script_dir, "model_server.py")

        # Setup virtual environment
        if os.environ.get('APPIMAGE'):
            self.venv_dir = os.path.expanduser("~/.local/share/ModelBrowser/venv")
        else:
            self.venv_dir = os.path.join(self.script_dir, "venv")

        self.python_path = os.path.join(self.venv_dir, "bin", "python3")

        # Server process
        self.server_process = None
        self.log_thread = None
        self.running = False

        self.create_widgets()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Setup virtual environment on startup
        self.setup_environment()

    def create_widgets(self):
        # Title bar
        title_frame = tk.Frame(self.root, bg="#2e3440", pady=15)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="🎨 Model Browser Server",
            font=("Arial", 18, "bold"),
            bg="#2e3440",
            fg="white"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="Browse and manage AI model files",
            font=("Arial", 10),
            bg="#2e3440",
            fg="#d8dee9"
        )
        subtitle_label.pack()

        # Control frame
        control_frame = tk.Frame(self.root, padx=20, pady=10)
        control_frame.pack(fill=tk.X)

        # Status
        status_frame = tk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = tk.Label(
            status_frame,
            text="● Stopped",
            font=("Arial", 10),
            fg="red"
        )
        self.status_label.pack(side=tk.LEFT)

        # Buttons
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Server",
            command=self.start_server,
            bg="#a3be8c",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            width=15,
            cursor="hand2",
            state=tk.DISABLED  # Disabled until environment is ready
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = tk.Button(
            button_frame,
            text="■ Stop Server",
            command=self.stop_server,
            bg="#bf616a",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            width=15,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.browser_button = tk.Button(
            button_frame,
            text="🌐 Open Browser",
            command=self.open_browser,
            bg="#5e81ac",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            width=15,
            cursor="hand2"
        )
        self.browser_button.pack(side=tk.LEFT)

        # URL display
        url_frame = tk.Frame(control_frame)
        url_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(url_frame, text="Server URL:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))

        url_entry = tk.Entry(url_frame, font=("Arial", 10))
        url_entry.insert(0, "http://localhost:8001/")
        url_entry.config(state="readonly")
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Log frame
        log_frame = tk.LabelFrame(self.root, text="Server Log", font=("Arial", 10, "bold"), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=15,
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Clear log button
        clear_button = tk.Button(
            log_frame,
            text="Clear Log",
            command=self.clear_log,
            bg="#4c566a",
            fg="white",
            font=("Arial", 9)
        )
        clear_button.pack(pady=(5, 0))

    def log(self, message, color=None):
        """Add a message to the log"""
        self.log_text.config(state=tk.NORMAL)
        if color:
            tag = f"color_{color}"
            self.log_text.tag_config(tag, foreground=color)
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        """Clear the log display"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def setup_environment(self):
        """Setup virtual environment and dependencies"""
        self.log("🔧 Setting up environment...", "#81a1c1")

        def setup():
            try:
                # Check if venv exists
                if not os.path.exists(self.venv_dir):
                    self.log("⚠️  Virtual environment not found. Creating it...")

                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(self.venv_dir), exist_ok=True)

                    # Create venv
                    subprocess.run(
                        ["python3", "-m", "venv", self.venv_dir],
                        check=True,
                        capture_output=True
                    )
                    self.log("✅ Virtual environment created")

                # Check if Pillow is installed
                result = subprocess.run(
                    [self.python_path, "-c", "from PIL import Image"],
                    capture_output=True
                )

                if result.returncode != 0:
                    self.log("⚠️  Pillow not found, installing...")
                    pip_path = os.path.join(self.venv_dir, "bin", "pip")
                    subprocess.run(
                        [pip_path, "install", "Pillow"],
                        check=True,
                        capture_output=True
                    )
                    self.log("✅ Pillow installed successfully")
                else:
                    self.log("✅ Pillow is available")

                self.log("✅ Environment ready!", "#a3be8c")

                # Enable start button
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))

            except Exception as e:
                self.log(f"❌ Error setting up environment: {e}", "#bf616a")
                self.root.after(0, lambda: messagebox.showerror(
                    "Setup Error",
                    f"Failed to setup environment:\n{str(e)}"
                ))

        # Run setup in background thread
        threading.Thread(target=setup, daemon=True).start()

    def start_server(self):
        """Start the model server"""
        if self.running:
            return

        # Check if model_server.py exists
        if not os.path.exists(self.model_server_path):
            messagebox.showerror(
                "Error",
                f"model_server.py not found!\n\nExpected: {self.model_server_path}"
            )
            return

        self.log("🚀 Starting Model Browser Server...", "#81a1c1")
        self.running = True

        # Update UI
        self.status_label.config(text="● Running", fg="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Change to script directory
        os.chdir(self.script_dir)

        # Start server process
        try:
            self.server_process = subprocess.Popen(
                [self.python_path, self.model_server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Start log reading thread
            self.log_thread = threading.Thread(target=self.read_logs, daemon=True)
            self.log_thread.start()

            self.log("✅ Server started on http://localhost:8001/", "#a3be8c")

            # Auto-open browser after 2 seconds
            self.root.after(2000, self.open_browser)

        except Exception as e:
            self.log(f"❌ Failed to start server: {e}", "#bf616a")
            self.running = False
            self.status_label.config(text="● Stopped", fg="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def stop_server(self):
        """Stop the model server"""
        if not self.running:
            return

        self.log("🛑 Stopping server...", "#81a1c1")

        if self.server_process:
            try:
                # Send SIGTERM to gracefully stop
                self.server_process.terminate()

                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.server_process.kill()
                    self.server_process.wait()

                self.server_process = None

            except Exception as e:
                self.log(f"⚠️  Error stopping server: {e}", "#ebcb8b")

        # Kill any remaining processes on port 8001
        try:
            subprocess.run(
                ["lsof", "-ti:8001"],
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(["pkill", "-f", "model_server.py"], capture_output=True)
        except:
            pass

        self.running = False
        self.status_label.config(text="● Stopped", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        self.log("✅ Server stopped", "#a3be8c")

    def read_logs(self):
        """Read server output and display in log"""
        if not self.server_process:
            return

        try:
            for line in iter(self.server_process.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                if line:
                    # Color code based on content
                    color = None
                    if "✅" in line or "Success" in line:
                        color = "#a3be8c"
                    elif "❌" in line or "Error" in line or "Failed" in line:
                        color = "#bf616a"
                    elif "⚠️" in line or "Warning" in line:
                        color = "#ebcb8b"

                    self.root.after(0, lambda l=line, c=color: self.log(l, c))
        except:
            pass

    def open_browser(self):
        """Open the browser to the server URL"""
        try:
            webbrowser.open("http://localhost:8001/")
            self.log("🌐 Opening browser...", "#81a1c1")
        except Exception as e:
            self.log(f"⚠️  Could not open browser: {e}", "#ebcb8b")

    def on_closing(self):
        """Handle window close event"""
        if self.running:
            if messagebox.askyesno("Quit", "Server is still running. Stop and quit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ModelBrowserGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
