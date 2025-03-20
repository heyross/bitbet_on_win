#!/usr/bin/env python
# BitNet Installer GUI Tabs
# Contains the tab classes for the installer GUI

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import webbrowser
import logging
import time
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

class InstallerTab(ttk.Frame):
    """Installation tab for checking prerequisites and installing BitNet"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.config_data = app.config_data
        
        # Status flags for prerequisites
        self.git_installed = False
        self.conda_installed = False
        self.vs_installed = False
        
        # Initialize UI components
        self.create_ui()
        
        # Check prerequisites on startup
        self.check_prerequisites()
        
    def create_ui(self):
        """Create the installer tab UI"""
        # Main layout container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create a content frame for all content except buttons
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header
        header = ttk.Label(content_frame, text="BitNet Installer", style="Header.TLabel")
        header.pack(pady=(0, 10), anchor=tk.W)
        
        # Description
        desc = ttk.Label(content_frame, text="This installer will set up BitNet and all required dependencies on your system.",
                       wraplength=700)
        desc.pack(pady=(0, 15), anchor=tk.W)
        
        # Installation options section
        options_frame = ttk.LabelFrame(content_frame, text="Installation Options")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Install directory selection
        dir_frame = ttk.Frame(options_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(dir_frame, text="Installation Directory:").pack(anchor=tk.W, pady=(0, 5))
        
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill=tk.X)
        
        self.install_dir = tk.StringVar(value=self.config_data.get("install_dir", "D:\\bitnetLLM"))
        dir_entry = ttk.Entry(dir_select_frame, textvariable=self.install_dir)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(dir_select_frame, text="Browse", command=self.browse_install_dir)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # GPU options
        gpu_frame = ttk.Frame(options_frame)
        gpu_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Use GPU checkbox
        self.gpu_enabled = tk.BooleanVar(value=self.config_data.get("use_gpu", True))
        gpu_check = ttk.Checkbutton(gpu_frame, text="Use GPU acceleration (requires compatible NVIDIA GPU)", 
                                   variable=self.gpu_enabled)
        gpu_check.pack(anchor=tk.W)
        
        # Installation section
        install_frame = ttk.LabelFrame(content_frame, text="Installation")
        install_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Prerequisites
        prereq_frame = ttk.Frame(install_frame)
        prereq_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(prereq_frame, text="Prerequisites:").pack(anchor=tk.W, pady=(0, 5))
        
        # Git status
        git_frame = ttk.Frame(prereq_frame)
        git_frame.pack(fill=tk.X, pady=2)
        
        self.git_status = ttk.Label(git_frame, text="Checking Git...", width=30)
        self.git_status.pack(side=tk.LEFT, anchor=tk.W)
        
        self.git_btn = ttk.Button(git_frame, text="Install Git", command=self.install_git)
        self.git_btn.pack(side=tk.RIGHT)
        
        # Conda status
        conda_frame = ttk.Frame(prereq_frame)
        conda_frame.pack(fill=tk.X, pady=2)
        
        self.conda_status = ttk.Label(conda_frame, text="Checking Conda...", width=30)
        self.conda_status.pack(side=tk.LEFT, anchor=tk.W)
        
        self.conda_btn = ttk.Button(conda_frame, text="Install Conda", command=self.install_conda)
        self.conda_btn.pack(side=tk.RIGHT)
        
        # Visual Studio status
        vs_frame = ttk.Frame(prereq_frame)
        vs_frame.pack(fill=tk.X, pady=2)
        
        self.vs_status = ttk.Label(vs_frame, text="Checking Visual Studio...", width=30)
        self.vs_status.pack(side=tk.LEFT, anchor=tk.W)
        
        self.vs_btn = ttk.Button(vs_frame, text="Install VS Build Tools", command=self.install_vs)
        self.vs_btn.pack(side=tk.RIGHT)
        
        # Progress section
        progress_frame = ttk.Frame(install_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(progress_frame, text="Installation Progress:").pack(anchor=tk.W, pady=(0, 5))
        
        self.progress = ttk.Progressbar(progress_frame, length=100, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_frame, text="Ready to install")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Create a dedicated frame for buttons that will always be at the bottom of the main window
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 10))
        
        self.install_btn = ttk.Button(buttons_frame, text="Install BitNet", 
                                    command=self.install_bitnet, style="Primary.TButton")
        self.install_btn.pack(side=tk.RIGHT)
        self.install_btn.config(state=tk.DISABLED)  # Initially disabled until prerequisites are checked
        
        self.refresh_btn = ttk.Button(buttons_frame, text="Refresh Prerequisites", 
                                     command=self.check_prerequisites)
        self.refresh_btn.pack(side=tk.RIGHT, padx=10)
        
    def check_prerequisites(self):
        """Check for installed prerequisites"""
        self.status_label.config(text="Checking prerequisites...")
        
        # Reset prerequisites status
        self.git_installed = False
        self.conda_installed = False
        self.vs_installed = False
        self._update_install_button()
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._check_prerequisites_thread, daemon=True).start()
        
    def _check_prerequisites_thread(self):
        """Check prerequisites in a background thread"""
        try:
            # Check Git
            git_path = core.check_git()
            self.git_installed = git_path is not None
            self._update_status(self.git_status, self.git_btn, self.git_installed, 
                              "Found" if self.git_installed else "Not Found")
            if self.git_installed:
                self.config_data["git_path"] = git_path
            
            # Check Conda
            conda_path = core.check_conda()
            self.conda_installed = conda_path is not None
            self._update_status(self.conda_status, self.conda_btn, self.conda_installed, 
                              "Found" if self.conda_installed else "Not Found")
            if self.conda_installed:
                self.config_data["conda_path"] = conda_path
            
            # Check Visual Studio
            vs_path = core.check_visual_studio()
            self.vs_installed = vs_path is not None
            self._update_status(self.vs_status, self.vs_btn, self.vs_installed, 
                              "Found" if self.vs_installed else "Not Found")
            if self.vs_installed:
                self.config_data["vs_path"] = vs_path
            
            # Update UI
            self.status_label.config(text="Prerequisites check completed")
            self._update_install_button()
            
        except Exception as e:
            logger.error(f"Error checking prerequisites: {str(e)}")
            self.status_label.config(text=f"Error checking prerequisites: {str(e)}")
    
    def _update_status(self, status_label, button, is_found, text):
        """Update the status label and button for a prerequisite"""
        if is_found:
            status_label.config(text=text, foreground="green")
            button.config(state=tk.DISABLED)
        else:
            status_label.config(text=text, foreground="red")
            button.config(state=tk.NORMAL)
    
    def _update_install_button(self):
        """Enable or disable the install button based on prerequisites"""
        if self.git_installed and self.conda_installed and self.vs_installed:
            self.install_btn.config(state=tk.NORMAL)
            logger.debug("Install button enabled - all prerequisites met")
        else:
            self.install_btn.config(state=tk.DISABLED)
            logger.debug(f"Install button disabled - prerequisites missing: Git={self.git_installed}, Conda={self.conda_installed}, VS={self.vs_installed}")
    
    def browse_install_dir(self):
        """Open a dialog to select installation directory"""
        directory = filedialog.askdirectory(
            initialdir=self.install_dir.get(),
            title="Select BitNet Installation Directory"
        )
        if directory:
            self.install_dir.set(directory)
            self.config_data["install_dir"] = directory
            save_config(self.config_data)
    
    def install_git(self):
        """Install Git for Windows"""
        self.git_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Installing Git...")
        self.progress.config(value=0)
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._install_git_thread, daemon=True).start()
    
    def _install_git_thread(self):
        """Install Git in a background thread"""
        try:
            def progress_callback(current, total):
                progress = int(current / total * 100)
                self.progress.config(value=progress)
                self.status_label.config(text=f"Downloading Git... {progress}%")
            
            # Download and install Git
            temp_dir = os.path.join(APP_DATA, "temp")
            core.install_git(temp_dir, progress_callback=progress_callback)
            
            # Check if Git is now installed
            git_path = core.check_git()
            self.git_installed = git_path is not None
            self._update_status(self.git_status, self.git_btn, self.git_installed, 
                              "Found" if self.git_installed else "Not Found")
            if self.git_installed:
                self.config_data["git_path"] = git_path
            
            # Update the install button state
            self._update_install_button()
            
        except Exception as e:
            logger.error(f"Error installing Git: {str(e)}")
            self.status_label.config(text=f"Error installing Git: {str(e)}")
            self.git_btn.config(state=tk.NORMAL)
    
    def install_conda(self):
        """Install Miniconda"""
        self.conda_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Installing Miniconda...")
        self.progress.config(value=0)
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._install_conda_thread, daemon=True).start()
    
    def _install_conda_thread(self):
        """Install Miniconda in a background thread"""
        try:
            def progress_callback(current, total):
                progress = int(current / total * 100)
                self.progress.config(value=progress)
                self.status_label.config(text=f"Downloading Miniconda... {progress}%")
            
            # Download and install Miniconda
            temp_dir = os.path.join(APP_DATA, "temp")
            core.install_miniconda(temp_dir, progress_callback=progress_callback)
            
            # Check if Conda is now installed
            conda_path = core.check_conda()
            self.conda_installed = conda_path is not None
            self._update_status(self.conda_status, self.conda_btn, self.conda_installed, 
                              "Found" if self.conda_installed else "Not Found")
            if self.conda_installed:
                self.config_data["conda_path"] = conda_path
            
            # Update the install button state
            self._update_install_button()
            
        except Exception as e:
            logger.error(f"Error installing Miniconda: {str(e)}")
            self.status_label.config(text=f"Error installing Miniconda: {str(e)}")
            self.conda_btn.config(state=tk.NORMAL)
    
    def install_vs(self):
        """Install Visual Studio Build Tools"""
        self.vs_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Installing Visual Studio Build Tools...")
        self.progress.config(value=0)
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._install_vs_thread, daemon=True).start()
    
    def _install_vs_thread(self):
        """Install Visual Studio Build Tools in a background thread"""
        try:
            def progress_callback(current, total):
                progress = int(current / total * 100)
                self.progress.config(value=progress)
                self.status_label.config(text=f"Downloading Visual Studio Build Tools... {progress}%")
            
            # Download and install Visual Studio Build Tools
            temp_dir = os.path.join(APP_DATA, "temp")
            core.install_vs_build_tools(temp_dir, progress_callback=progress_callback)
            
            # Check if VS is now installed
            vs_path = core.check_visual_studio()
            self.vs_installed = vs_path is not None
            self._update_status(self.vs_status, self.vs_btn, self.vs_installed, 
                              "Found" if self.vs_installed else "Not Found")
            if self.vs_installed:
                self.config_data["vs_path"] = vs_path
            
            # Update the install button state
            self._update_install_button()
            
        except Exception as e:
            logger.error(f"Error installing Visual Studio Build Tools: {str(e)}")
            self.status_label.config(text=f"Error installing Visual Studio Build Tools: {str(e)}")
            self.vs_btn.config(state=tk.NORMAL)
    
    def install_bitnet(self):
        """Install BitNet"""
        # Save settings first
        self.config_data["install_dir"] = self.install_dir.get()
        self.config_data["use_gpu"] = self.gpu_enabled.get()
        save_config(self.config_data)
        
        # Disable buttons during installation
        self.install_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        
        # Update UI
        self.status_label.config(text="Installing BitNet...")
        self.progress.config(value=0)
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._install_bitnet_thread, daemon=True).start()
    
    def _install_bitnet_thread(self):
        """Install BitNet in a background thread"""
        try:
            install_dir = self.install_dir.get()
            
            # Create installation directory if it doesn't exist
            os.makedirs(install_dir, exist_ok=True)
            
            # Clone BitNet repository
            self.status_label.config(text="Cloning BitNet repository...")
            self.progress.config(value=10)
            
            def clone_progress(current, total):
                progress = 10 + int(current / total * 30)  # 10-40%
                self.progress.config(value=progress)
                self.status_label.config(text=f"Cloning BitNet repository... {current}/{total} objects")
            
            core.clone_bitnet(install_dir, progress_callback=clone_progress)
            
            # Set up conda environment
            self.status_label.config(text="Setting up conda environment...")
            self.progress.config(value=40)
            
            conda_path = self.config_data["conda_path"]
            gpu_enabled = self.gpu_enabled.get()
            
            # Update progress as setup progresses
            for i in range(41, 80):
                self.progress.config(value=i)
                self.update()  # Force UI update
                time.sleep(0.05)
            
            core.setup_conda_env(conda_path, install_dir, gpu_enabled)
            
            # Create startup script and shortcut
            self.status_label.config(text="Creating startup script...")
            self.progress.config(value=80)
            
            startup_path = core.create_startup_script(install_dir, conda_path)
            
            # Installation complete
            self.progress.config(value=100)
            self.status_label.config(text="Installation completed successfully!")
            
            # Re-enable buttons
            self.refresh_btn.config(state=tk.NORMAL)
            
            # Show success message
            messagebox.showinfo("Installation Complete", 
                              f"BitNet has been successfully installed to {install_dir}\n\n"
                              f"You can start BitNet using the created shortcut or by running:\n{startup_path}")
            
        except Exception as e:
            logger.error(f"Error installing BitNet: {str(e)}")
            self.status_label.config(text=f"Error installing BitNet: {str(e)}")
            
            # Re-enable buttons
            self.install_btn.config(state=tk.NORMAL)
            self.refresh_btn.config(state=tk.NORMAL)
            
            # Show error message
            messagebox.showerror("Installation Error", 
                               f"An error occurred during installation:\n\n{str(e)}\n\n"
                               "Please check the log for details.")
