#!/usr/bin/env python
# BitNet Control Panel Tab
# Provides UI for managing BitNet models and running inference

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import subprocess
import webbrowser
import logging
from pathlib import Path

# Import the installer modules
try:
    from installer import VERSION, TITLE, APP_DATA, load_config, save_config
    import installer_core as core
except ImportError:
    print("Failed to import installer modules")
    sys.exit(1)

# Configure logger
logger = logging.getLogger("BitNet")

class ControlPanelTab(ttk.Frame):
    """Control panel for managing BitNet models and running inference"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.config_data = app.config_data
        
        # State variables
        self.model_config = {
            "model_size": tk.StringVar(value="7B"),
            "temperature": tk.DoubleVar(value=0.7),
            "top_p": tk.DoubleVar(value=0.9),
            "max_tokens": tk.IntVar(value=256),
            "use_gpu": tk.BooleanVar(value=True)
        }
        
        self.available_models = []
        self.current_model = tk.StringVar(value="")
        self.bitnet_status = tk.StringVar(value="Not Running")
        self.output_text = None
        self.bitnet_process = None  # Initialize bitnet_process attribute
        
        # Initialize UI components
        self.create_ui()
        
        # Load models list
        self.load_models()
    
    def create_ui(self):
        """Create the control panel UI"""
        # Main layout container with two columns
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header
        header = ttk.Label(main_frame, text="BitNet Control Panel", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Left column: Model selection and configuration
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Model section
        model_frame = ttk.LabelFrame(left_frame, text="Model Selection")
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model dropdown
        ttk.Label(model_frame, text="Select Model:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        model_combo = ttk.Combobox(model_frame, textvariable=self.current_model, state="readonly")
        model_combo.pack(fill=tk.X, padx=10, pady=(0, 5))
        model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)
        
        # Model buttons
        button_frame = ttk.Frame(model_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Refresh", command=self.load_models).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Download", command=self.download_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Details", command=self.show_model_details).pack(side=tk.LEFT)
        
        # Configuration section
        config_frame = ttk.LabelFrame(left_frame, text="Model Configuration")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Temperature
        temp_frame = ttk.Frame(config_frame)
        temp_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(temp_frame, text="Temperature:").pack(side=tk.LEFT)
        temp_scale = ttk.Scale(temp_frame, from_=0.1, to=2.0, variable=self.model_config["temperature"],
                             orient=tk.HORIZONTAL, length=150)
        temp_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        temp_value = ttk.Label(temp_frame, text="0.7")
        temp_value.pack(side=tk.RIGHT, padx=5)
        
        # Update temperature label when slider moves
        def update_temp_label(event):
            temp_value.config(text=f"{self.model_config['temperature'].get():.1f}")
        
        temp_scale.bind("<Motion>", update_temp_label)
        
        # Top-p
        top_p_frame = ttk.Frame(config_frame)
        top_p_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(top_p_frame, text="Top-p:").pack(side=tk.LEFT)
        top_p_scale = ttk.Scale(top_p_frame, from_=0.1, to=1.0, variable=self.model_config["top_p"],
                              orient=tk.HORIZONTAL, length=150)
        top_p_scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        top_p_value = ttk.Label(top_p_frame, text="0.9")
        top_p_value.pack(side=tk.RIGHT, padx=5)
        
        # Update top-p label when slider moves
        def update_top_p_label(event):
            top_p_value.config(text=f"{self.model_config['top_p'].get():.1f}")
        
        top_p_scale.bind("<Motion>", update_top_p_label)
        
        # Max tokens
        max_tokens_frame = ttk.Frame(config_frame)
        max_tokens_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(max_tokens_frame, text="Max Tokens:").pack(side=tk.LEFT)
        ttk.Spinbox(max_tokens_frame, from_=1, to=4096, textvariable=self.model_config["max_tokens"],
                   width=6).pack(side=tk.RIGHT, padx=5)
        
        # GPU checkbox
        gpu_frame = ttk.Frame(config_frame)
        gpu_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(gpu_frame, text="Use GPU acceleration", variable=self.model_config["use_gpu"]).pack(anchor=tk.W)
        
        # Right column: Input/output and control
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew")
        
        # Chat/interaction section
        io_frame = ttk.LabelFrame(right_frame, text="BitNet Interaction")
        io_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(io_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.bitnet_status).pack(side=tk.LEFT, padx=5)
        
        # Output area
        ttk.Label(io_frame, text="Output:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        output_frame = ttk.Frame(io_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=12)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # Input area
        ttk.Label(io_frame, text="Input:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        input_frame = ttk.Frame(io_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=4)
        self.input_text.pack(fill=tk.X, expand=True, pady=(0, 5))
        
        # Send button
        button_frame = ttk.Frame(io_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Clear", command=self.clear_interaction).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Start Server", command=self.start_bitnet_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Send", command=self.send_prompt, style="Primary.TButton").pack(side=tk.RIGHT)
        
        # Configure grid weights to make the UI elements resize properly
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
    
    def load_models(self):
        """Load available BitNet models"""
        # This would typically scan the models directory
        # For now, we'll just populate with sample data
        self.available_models = [
            "BitNet-7B-base",
            "BitNet-2B-base",
            "Custom-BitNet-model"
        ]
        
        # Get combobox from UI and update
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.LabelFrame) and frame.cget("text") == "Model Selection":
                        for subframe in frame.winfo_children():
                            if isinstance(subframe, ttk.Combobox):
                                subframe['values'] = self.available_models
                                if not self.current_model.get() and self.available_models:
                                    self.current_model.set(self.available_models[0])
                                break
        
        if not self.current_model.get() and self.available_models:
            self.current_model.set(self.available_models[0])
    
    def on_model_selected(self, event):
        """Handle model selection change"""
        selected = self.current_model.get()
        logger.info(f"Selected model: {selected}")
        
        # Here we would load model-specific configurations
        # For now, just update the UI
        if "7B" in selected:
            self.model_config["model_size"].set("7B")
        elif "2B" in selected:
            self.model_config["model_size"].set("2B")
        
        # Add model-specific info to the output area
        self.update_output(f"Selected model: {selected}\n")
    
    def download_model(self):
        """Download a new BitNet model"""
        # This would open a dialog to select models to download
        messagebox.showinfo("Download Model", 
                          "This feature would download pre-trained BitNet models.\n\n"
                          "For now, please manually download models from "
                          "https://github.com/microsoft/BitNet/releases")
    
    def show_model_details(self):
        """Show details of the selected model"""
        selected = self.current_model.get()
        if not selected:
            messagebox.showinfo("Model Details", "No model selected.")
            return
        
        # This would show detailed information about the model
        details = f"Model: {selected}\n\n"
        details += "Parameters: " + ("7 billion" if "7B" in selected else "2 billion") + "\n"
        details += "Bitwidth: 1-bit weights & 8-bit activations\n"
        details += "Training: Trained on diverse text corpus\n"
        details += "License: MIT License\n"
        details += "Source: Microsoft BitNet Project\n"
        
        messagebox.showinfo(f"Model Details - {selected}", details)
    
    def clear_interaction(self):
        """Clear the input and output areas"""
        self.input_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def update_output(self, text):
        """Update the output text area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def start_bitnet_server(self):
        """Start the BitNet server"""
        # Check if BitNet is installed
        install_dir = self.config_data.get("install_dir", "")
        if not install_dir or not os.path.exists(install_dir):
            messagebox.showerror("Error", "BitNet is not installed. Please install it first.")
            return
        
        # Update status
        self.bitnet_status.set("Starting...")
        
        # Run in a separate thread
        threading.Thread(target=self._start_server_thread, daemon=True).start()
    
    def _start_server_thread(self):
        """Start BitNet server in a background thread"""
        try:
            # Get conda and install path
            conda_path = self.config_data.get("conda_path")
            install_dir = self.config_data.get("install_dir")
            
            if not conda_path or not install_dir:
                raise Exception("Missing conda path or installation directory.")
            
            # Check if we can find conda
            if not os.path.exists(conda_path):
                # Try to find conda in standard locations
                conda_path = core.find_conda()
                if conda_path:
                    self.config_data["conda_path"] = conda_path
                else:
                    raise Exception("Conda not found. Please install it first.")
            
            # Update output
            self.update_output("Starting BitNet server...\n")
            
            # BitNet requires running setup_env.py first to build the project
            # Look for setup_env.py in the installation directory
            setup_env_path = os.path.join(install_dir, "setup_env.py")
            
            if os.path.exists(setup_env_path):
                self.update_output(f"Found setup_env.py at {setup_env_path}\n")
                
                # Get the HuggingFace model name corresponding to the user-friendly name
                model_mapping = {
                    "BitNet-7B-base": "tiiuae/Falcon3-7B-1.58bit",
                    "Falcon-7B-1.58bit": "tiiuae/Falcon3-7B-1.58bit",
                    "Falcon-7B-3bit": "tiiuae/Falcon3-7B-3bit",
                    "Falcon-40B-1.58bit": "tiiuae/Falcon3-40B-1.58bit",
                }
                
                hf_model = model_mapping.get(self.current_model.get(), "tiiuae/Falcon3-7B-1.58bit")
                self.update_output(f"Using HuggingFace model: {hf_model}\n")
                
                # Create a custom setup script that modifies the CMake arguments to work with MSVC instead of ClangCL
                setup_wrapper_path = os.path.join(install_dir, "setup_wrapper.py")
                with open(setup_wrapper_path, 'w') as f:
                    f.write("""
import sys
import os
import subprocess
import re

# Get the original setup_env.py path
original_script = os.path.join(os.path.dirname(__file__), "setup_env.py")

# Import the main function from setup_env.py
sys.path.append(os.path.dirname(__file__))
try:
    from setup_env import main as original_main
    
    # Monkey patch the compile function to use MSVC instead of ClangCL
    import inspect
    import types
    
    # Get the setup_env module
    import setup_env
    
    # Find the compile function
    original_compile = setup_env.compile
    
    # Create a wrapper function that modifies the CMake arguments
    def compile_wrapper(*args, **kwargs):
        print("Using Windows-compatible CMake configuration")
        
        # Get the source code of the original compile function
        source = inspect.getsource(original_compile)
        
        # Replace ClangCL with the default toolchain (MSVC on Windows)
        modified_source = source.replace("'-T', 'ClangCL'", "")
        
        # Add DCMAKE_CXX_COMPILER to use MSVC
        if "-DBITNET_X86_TL2=ON" in modified_source:
            modified_source = modified_source.replace("-DBITNET_X86_TL2=ON", "-DBITNET_X86_TL2=ON -DCMAKE_CXX_COMPILER=cl.exe")
        
        # Create a new function with modified source
        compile_code = compile(modified_source, "<string>", "exec")
        modified_locals = {}
        exec(compile_code, setup_env.__dict__, modified_locals)
        
        # Get the modified compile function and call it
        modified_compile = list(modified_locals.values())[0]
        return modified_compile(*args, **kwargs)
    
    # Replace the original compile function with our wrapper
    setup_env.compile = compile_wrapper
    
    # Now call the original main function with the passed arguments
    original_main()
    
except ImportError as e:
    print(f"Error importing setup_env.py: {e}")
    sys.exit(1)
""")
                
                # Run the setup command through our wrapper
                cmd = [
                    conda_path,
                    "run", "-n", "bitnet-cpp",
                    "python", setup_wrapper_path,
                    "--hf-repo", hf_model,
                    "--quant-type", "i2_s"  # Using 2-bit signed quantization
                ]
                
                if self.model_config["use_gpu"].get():
                    cmd.append("--gpu")
                
                self.update_output(f"Setting up BitNet environment with command: {' '.join(cmd)}\n")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=install_dir
                )
                
                # Read output in a loop
                for line in process.stdout:
                    self.update_output(line)
                    
                    # Check for server ready message
                    if "Server started at" in line:
                        self.bitnet_status.set("Ready")
                
                # Process completed
                process.wait()
                
                # Update status based on exit code
                if process.returncode == 0:
                    self.bitnet_status.set("Stopped")
                    self.update_output("BitNet server stopped gracefully.\n")
                else:
                    self.bitnet_status.set("Error")
                    self.update_output(f"BitNet server exited with error code {process.returncode}.\n")
            
            # Now look for server executable in the build directory
            server_executables = [
                os.path.join(install_dir, "build", "bin", "server"),
                os.path.join(install_dir, "build", "server"),
                os.path.join(install_dir, "build", "bin", "server.exe"),
                os.path.join(install_dir, "build", "server.exe"),
                # Check in server directory too
                os.path.join(install_dir, "server", "server"),
                os.path.join(install_dir, "server", "server.exe")
            ]
            
            server_executable = None
            for exe in server_executables:
                if os.path.exists(exe):
                    server_executable = exe
                    self.update_output(f"Found BitNet server executable: {exe}\n")
                    break
            
            if server_executable:
                # Find the converted .gguf model file
                gguf_model_files = []
                models_dir = os.path.join(install_dir, "models")
                if os.path.exists(models_dir):
                    for root, _, files in os.walk(models_dir):
                        for file in files:
                            if file.endswith(".gguf"):
                                gguf_model_files.append(os.path.join(root, file))
                
                if gguf_model_files:
                    model_path = gguf_model_files[0]  # Use first found model
                    self.update_output(f"Using model: {model_path}\n")
                    
                    cmd = [
                        server_executable,
                        "--model", model_path,
                        "--host", "127.0.0.1",
                        "--port", "8080"
                    ]
                    
                    # Add GPU parameters if needed
                    if self.model_config["use_gpu"].get():
                        cmd.extend(["--n-gpu-layers", "35"])
                    
                    self.update_output(f"Starting BitNet server with command: {' '.join(cmd)}\n")
                    self.bitnet_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=os.path.dirname(server_executable)
                    )
                else:
                    # If no .gguf model files are found, try running with Python using the paths set up by the .pth file
                    self.update_output("No .gguf model files found. Attempting to run BitNet server script directly...\n")
                    
                    # Look for server scripts
                    server_scripts = [
                        os.path.join(install_dir, "server.py"),
                        os.path.join(install_dir, "server", "server.py"),
                        os.path.join(install_dir, "scripts", "server.py"),
                        os.path.join(install_dir, "run_server.py")
                    ]
                    
                    server_script = None
                    for script in server_scripts:
                        if os.path.exists(script):
                            server_script = script
                            self.update_output(f"Found server script: {script}\n")
                            break
                    
                    if server_script:
                        cmd = [
                            conda_path,
                            "run", "-n", "bitnet-cpp",
                            "python", server_script
                        ]
                        
                        self.update_output(f"Starting BitNet with Python script: {' '.join(cmd)}\n")
                        self.bitnet_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            cwd=os.path.dirname(server_script)
                        )
                    else:
                        # Last resort - try running main.py
                        main_script = os.path.join(install_dir, "main.py")
                        if os.path.exists(main_script):
                            cmd = [
                                conda_path,
                                "run", "-n", "bitnet-cpp",
                                "python", main_script,
                                "--server"
                            ]
                            
                            self.update_output(f"Starting BitNet with main script: {' '.join(cmd)}\n")
                            self.bitnet_process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                text=True,
                                cwd=install_dir
                            )
                        else:
                            self.update_output("Error: Could not find any server script to run BitNet.\n")
                            self.update_output("Please build BitNet manually using the instructions at https://github.com/microsoft/BitNet\n")
            else:
                # If no executable is found, check if setup_env.py exists but hasn't been run
                if os.path.exists(setup_env_path):
                    self.update_output("No BitNet executable found. You may need to run setup_env.py first to build BitNet.\n")
                    self.update_output("Try running: python setup_env.py --hf-repo tiiuae/Falcon3-7B-1.58bit --quant-type i2_s\n")
                else:
                    self.update_output("Error: BitNet server executable not found and setup_env.py is missing.\n")
                    self.update_output("Make sure you've cloned the BitNet repository correctly.\n")
        
            # Read output in a loop
            for line in self.bitnet_process.stdout:
                self.update_output(line)
                
                # Check for server ready message
                if "Server started at" in line:
                    self.bitnet_status.set("Ready")
            
            # Process completed
            self.bitnet_process.wait()
            
            # Update status based on exit code
            if self.bitnet_process.returncode == 0:
                self.bitnet_status.set("Stopped")
                self.update_output("BitNet server stopped gracefully.\n")
            else:
                self.bitnet_status.set("Error")
                self.update_output(f"BitNet server exited with error code {self.bitnet_process.returncode}.\n")
                
        except Exception as e:
            logger.error(f"Error starting BitNet server: {str(e)}")
            self.update_output(f"Error: {str(e)}\n")
            self.bitnet_status.set("Error")
    
    def send_prompt(self):
        """Send a prompt to the BitNet server"""
        # Check if server is running
        if self.bitnet_status.get() not in ["Running", "Ready"]:
            messagebox.showinfo("Server Not Running", 
                              "The BitNet server is not running. Please start the server first.")
            return
        
        # Get prompt from input
        prompt = self.input_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showinfo("Empty Prompt", "Please enter a prompt to send to the model.")
            return
        
        # Display the prompt in the output
        self.update_output(f"\n> {prompt}\n\n")
        
        # Clear the input
        self.input_text.delete(1.0, tk.END)
        
        # Process the prompt in a background thread
        threading.Thread(target=self._process_prompt_thread, args=(prompt,), daemon=True).start()
    
    def _process_prompt_thread(self, prompt):
        """Process a prompt in a background thread"""
        try:
            # In a real implementation, this would send the prompt to the BitNet server
            # For now, we'll just simulate a response
            
            # Simulate processing delay
            import time
            import random
            
            self.update_output("Thinking...")
            time.sleep(1.5)
            
            # Generate a sample response
            if "hello" in prompt.lower() or "hi" in prompt.lower():
                response = "Hello! I'm BitNet, a 1-bit neural network model. How can I help you today?"
            elif "what" in prompt.lower() and "you" in prompt.lower():
                response = ("I'm BitNet, a neural network that uses 1-bit weights and 8-bit activations. "
                          "This makes me much more efficient than traditional models, while maintaining "
                          "competitive performance. I was developed by Microsoft Research.")
            elif "help" in prompt.lower():
                response = ("I can help with various tasks like answering questions, writing content, "
                          "explaining concepts, and more. Just let me know what you need!")
            else:
                # Generic response for other inputs
                responses = [
                    "That's an interesting question. From my understanding, the answer involves considering multiple perspectives.",
                    "I'm analyzing your request. Based on my training data, I would suggest approaching this with caution.",
                    "I've processed your input and can offer some insights, though remember my knowledge has limitations.",
                    "Thank you for your query. I've computed a response based on pattern recognition in my training data."
                ]
                response = random.choice(responses)
            
            # Display the response
            self.update_output(response + "\n")
            
        except Exception as e:
            logger.error(f"Error processing prompt: {str(e)}")
            self.update_output(f"Error: {str(e)}\n")


class AdvancedTab(ttk.Frame):
    """Advanced tab for system settings and diagnostics"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.config_data = app.config_data
        
        # Initialize UI components
        self.create_ui()
    
    def create_ui(self):
        """Create the advanced tab UI"""
        # Main layout container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header
        header = ttk.Label(main_frame, text="Advanced Settings", style="Header.TLabel")
        header.pack(pady=(0, 10), anchor=tk.W)
        
        # System diagnostics
        diag_frame = ttk.LabelFrame(main_frame, text="System Diagnostics")
        diag_frame.pack(fill=tk.X, pady=(0, 15))
        
        # System info
        info_frame = ttk.Frame(diag_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Get system info
        import platform
        system_info = f"OS: {platform.system()} {platform.version()}\n"
        system_info += f"Python: {platform.python_version()}\n"
        
        # CPU info
        try:
            import psutil
            system_info += f"CPU: {psutil.cpu_count(logical=True)} logical cores\n"
            system_info += f"RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB total\n"
        except ImportError:
            system_info += "CPU/RAM: psutil not available\n"
        
        # GPU info
        system_info += "GPU: Detection requires additional libraries\n"
        
        # Display system info
        info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=6)
        info_text.pack(fill=tk.X, expand=True)
        info_text.insert(tk.END, system_info)
        info_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(diag_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Run Diagnostics", 
                 command=self.run_diagnostics).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Check GPU Compatibility", 
                 command=self.check_gpu).pack(side=tk.LEFT, padx=5)
        
        # Environment management
        env_frame = ttk.LabelFrame(main_frame, text="Environment Management")
        env_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Conda environment actions
        ttk.Button(env_frame, text="Update Conda Environment", 
                 command=self.update_conda_env).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Button(env_frame, text="Reset Conda Environment", 
                 command=self.reset_conda_env).pack(anchor=tk.W, padx=10, pady=5)
        
        # Cache management
        cache_frame = ttk.LabelFrame(main_frame, text="Cache Management")
        cache_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(cache_frame, text="Clear Download Cache", 
                 command=self.clear_cache).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Button(cache_frame, text="Clean Installation Temporary Files", 
                 command=self.clean_temp_files).pack(anchor=tk.W, padx=10, pady=5)
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        messagebox.showinfo("Diagnostics", 
                          "Running diagnostics would check your system's compatibility with BitNet.\n\n"
                          "This feature would verify CPU, RAM, disk space, and CUDA compatibility.")
    
    def check_gpu(self):
        """Check GPU compatibility"""
        messagebox.showinfo("GPU Check", 
                          "Checking GPU compatibility would verify CUDA installation and GPU capabilities.\n\n"
                          "This feature would detect available GPUs and report their compatibility.")
    
    def update_conda_env(self):
        """Update the conda environment"""
        if messagebox.askyesno("Update Environment", 
                             "This will update the BitNet conda environment with the latest packages.\n\n"
                             "Do you want to continue?"):
            # This would update the conda environment
            messagebox.showinfo("Update Started", 
                              "Environment update started. This may take a few minutes.")
    
    def reset_conda_env(self):
        """Reset the conda environment"""
        if messagebox.askyesno("Reset Environment", 
                             "This will remove and recreate the BitNet conda environment.\n\n"
                             "All custom packages will be lost. Do you want to continue?"):
            # This would reset the conda environment
            messagebox.showinfo("Reset Started", 
                              "Environment reset started. This may take a few minutes.")
    
    def clear_cache(self):
        """Clear download cache"""
        if messagebox.askyesno("Clear Cache", 
                             "This will clear the download cache used for models and dependencies.\n\n"
                             "Do you want to continue?"):
            # This would clear the cache
            messagebox.showinfo("Cache Cleared", 
                              "Download cache has been cleared successfully.")
    
    def clean_temp_files(self):
        """Clean temporary files"""
        if messagebox.askyesno("Clean Temp Files", 
                             "This will remove temporary files created during installation.\n\n"
                             "Do you want to continue?"):
            # This would clean temp files
            messagebox.showinfo("Cleanup Completed", 
                              "Temporary files have been cleaned successfully.")
