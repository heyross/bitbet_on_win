#!/usr/bin/env python
# BitNet Installer Dialogs
# Contains dialog windows used in the BitNet installer

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import logging
from datetime import datetime

# Import the installer modules
try:
    from installer import VERSION, TITLE, APP_DATA, LOG_FILE, load_config, save_config
except ImportError:
    print("Failed to import installer modules")
    sys.exit(1)

# Configure logger
logger = logging.getLogger("BitNet")

class SettingsDialog(tk.Toplevel):
    """Settings dialog for the BitNet installer"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config_data = parent.config_data.copy()  # Work with a copy
        
        # Configure window
        self.title("BitNet Settings")
        self.geometry("500x400")
        self.minsize(500, 400)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Initialize UI
        self.create_ui()
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Make dialog modal
        self.wait_window(self)
    
    def create_ui(self):
        """Create the settings dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for settings categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # General settings tab
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="General")
        
        # Installation directory
        dir_frame = ttk.Frame(general_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Installation Directory:").pack(side=tk.LEFT, padx=(0, 10))
        self.install_dir = tk.StringVar(value=self.config_data.get("install_dir", ""))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.install_dir, width=40)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_install_dir).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Create shortcut option
        self.create_shortcut = tk.BooleanVar(value=self.config_data.get("create_shortcut", True))
        shortcut_check = ttk.Checkbutton(general_frame, text="Create desktop shortcut", 
                                       variable=self.create_shortcut)
        shortcut_check.pack(anchor=tk.W, pady=5)
        
        # Advanced settings tab
        advanced_frame = ttk.Frame(notebook, padding=10)
        notebook.add(advanced_frame, text="Advanced")
        
        # GPU settings
        self.enable_gpu = tk.BooleanVar(value=self.config_data.get("enable_gpu", True))
        gpu_check = ttk.Checkbutton(advanced_frame, text="Enable GPU acceleration", 
                                  variable=self.enable_gpu)
        gpu_check.pack(anchor=tk.W, pady=5)
        
        # Conda path
        conda_frame = ttk.Frame(advanced_frame)
        conda_frame.pack(fill=tk.X, pady=5)
        ttk.Label(conda_frame, text="Conda Path:").pack(side=tk.LEFT, padx=(0, 10))
        self.conda_path = tk.StringVar(value=self.config_data.get("conda_path", ""))
        conda_entry = ttk.Entry(conda_frame, textvariable=self.conda_path, width=40)
        conda_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(conda_frame, text="Browse", command=self.browse_conda_path).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Git path
        git_frame = ttk.Frame(advanced_frame)
        git_frame.pack(fill=tk.X, pady=5)
        ttk.Label(git_frame, text="Git Path:").pack(side=tk.LEFT, padx=(0, 10))
        self.git_path = tk.StringVar(value=self.config_data.get("git_path", ""))
        git_entry = ttk.Entry(git_frame, textvariable=self.git_path, width=40)
        git_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(git_frame, text="Browse", command=self.browse_git_path).pack(side=tk.RIGHT, padx=(10, 0))
        
        # VS path
        vs_frame = ttk.Frame(advanced_frame)
        vs_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vs_frame, text="Visual Studio Path:").pack(side=tk.LEFT, padx=(0, 10))
        self.vs_path = tk.StringVar(value=self.config_data.get("vs_path", ""))
        vs_entry = ttk.Entry(vs_frame, textvariable=self.vs_path, width=40)
        vs_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(vs_frame, text="Browse", command=self.browse_vs_path).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.save_settings).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=10)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.LEFT)
    
    def browse_install_dir(self):
        """Browse for installation directory"""
        directory = filedialog.askdirectory(
            initialdir=self.install_dir.get(),
            title="Select BitNet Installation Directory"
        )
        if directory:
            self.install_dir.set(directory)
    
    def browse_conda_path(self):
        """Browse for Conda executable"""
        file_path = filedialog.askopenfilename(
            initialdir=os.path.dirname(self.conda_path.get()) if self.conda_path.get() else None,
            title="Select Conda Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.conda_path.set(file_path)
    
    def browse_git_path(self):
        """Browse for Git executable"""
        file_path = filedialog.askopenfilename(
            initialdir=os.path.dirname(self.git_path.get()) if self.git_path.get() else None,
            title="Select Git Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.git_path.set(file_path)
    
    def browse_vs_path(self):
        """Browse for Visual Studio path"""
        directory = filedialog.askdirectory(
            initialdir=self.vs_path.get(),
            title="Select Visual Studio Installation Directory"
        )
        if directory:
            self.vs_path.set(directory)
    
    def reset_defaults(self):
        """Reset settings to defaults"""
        from installer import DEFAULT_CONFIG
        
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            # Copy default values but preserve any keys not in DEFAULT_CONFIG
            for key, value in DEFAULT_CONFIG.items():
                self.config_data[key] = value
            
            # Update UI
            self.install_dir.set(self.config_data["install_dir"])
            self.create_shortcut.set(self.config_data["create_shortcut"])
            self.enable_gpu.set(self.config_data["enable_gpu"])
            self.conda_path.set(self.config_data.get("conda_path", ""))
            self.git_path.set(self.config_data.get("git_path", ""))
            self.vs_path.set(self.config_data.get("vs_path", ""))
    
    def save_settings(self):
        """Save settings and close the dialog"""
        # Update config data from UI
        self.config_data["install_dir"] = self.install_dir.get()
        self.config_data["create_shortcut"] = self.create_shortcut.get()
        self.config_data["enable_gpu"] = self.enable_gpu.get()
        self.config_data["conda_path"] = self.conda_path.get()
        self.config_data["git_path"] = self.git_path.get()
        self.config_data["vs_path"] = self.vs_path.get()
        
        # Copy back to parent
        for key, value in self.config_data.items():
            self.parent.config_data[key] = value
        
        # Save to file
        save_config(self.parent.config_data)
        
        # Close dialog
        self.destroy()

class LogViewerDialog(tk.Toplevel):
    """Dialog for viewing installer logs"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Configure window
        self.title("BitNet Installer Log")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.transient(parent)
        
        # Initialize UI
        self.create_ui()
        
        # Load log content
        self.load_log()
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def create_ui(self):
        """Create the log viewer UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log file path
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(path_frame, text="Log File:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(path_frame, text=LOG_FILE).pack(side=tk.LEFT)
        
        # Log content
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.NONE)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Refresh", command=self.load_log).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Save As...", command=self.save_log).pack(side=tk.RIGHT, padx=10)
    
    def load_log(self):
        """Load and display log content"""
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    content = f.read()
                    self.log_text.insert(tk.END, content)
            else:
                self.log_text.insert(tk.END, "Log file does not exist yet.")
            
            self.log_text.config(state=tk.DISABLED)
            
            # Scroll to end
            self.log_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load log file: {str(e)}")
    
    def clear_log(self):
        """Clear the log file"""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the log file?"):
            try:
                with open(LOG_FILE, 'w') as f:
                    f.write(f"Log cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                self.load_log()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear log file: {str(e)}")
    
    def save_log(self):
        """Save log to a new file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Log As"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                messagebox.showinfo("Success", f"Log saved to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log file: {str(e)}")
