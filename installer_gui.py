#!/usr/bin/env python
# BitNet Installer GUI
# Provides a user-friendly interface for installing and managing BitNet

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import logging
import traceback
from datetime import datetime

# Configure logger before imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BitNet")

# Import the installer modules
try:
    from installer import VERSION, TITLE, APP_DATA, load_config, save_config
    import installer_core as core
    logger.debug("Successfully imported core modules")
except ImportError as e:
    error_msg = f"Failed to import installer modules: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    print(error_msg)
    sys.exit(1)

class InstallerApp:
    """Main installer application window"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # Check if parent is the root window or a frame
        self.is_root = isinstance(parent, tk.Tk)
        
        # Configure the root window if this is the main window
        if self.is_root:
            self.parent.title(TITLE)
            self.parent.geometry("800x700")  # Increased height from 600 to 700
            self.parent.minsize(700, 600)    # Increased min height from 500 to 600
            self.parent.config(bg="#f0f0f0")
            
            # Set icon if available
            try:
                self.parent.iconbitmap(os.path.join(os.path.dirname(__file__), "assets", "icon.ico"))
            except:
                pass
            
        # Load configuration
        self.config_data = load_config()
        
        # Initialize UI components
        self.init_styles()
        self.create_menu()
        self.create_tabs()
        
        # Bind close event if this is the main window
        if self.is_root:
            self.parent.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center the window if this is the main window
        if self.is_root:
            self.center_window()
        
    def init_styles(self):
        """Initialize ttk styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a more modern looking theme
        
        # Configure styles
        self.style.configure("TNotebook", background="#f0f0f0", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#e0e0e0", padding=[10, 5], font=('Segoe UI', 10))
        self.style.map("TNotebook.Tab", background=[("selected", "#f0f0f0")])
        
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", font=('Segoe UI', 10), padding=5)
        self.style.configure("TLabel", background="#f0f0f0", font=('Segoe UI', 10))
        self.style.configure("TCheckbutton", background="#f0f0f0", font=('Segoe UI', 10))
        
        # Special styles
        self.style.configure("Header.TLabel", font=('Segoe UI', 14, 'bold'))
        self.style.configure("Subheader.TLabel", font=('Segoe UI', 12))
        self.style.configure("Primary.TButton", font=('Segoe UI', 11, 'bold'))
        
    def create_menu(self):
        """Create the application menu"""
        if self.is_root:
            menubar = tk.Menu(self.parent)
            self.parent.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="Settings", command=self.show_settings)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.on_close)
            menubar.add_cascade(label="File", menu=file_menu)
            
            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(label="View Log", command=self.show_log)
            help_menu.add_command(label="About", command=self.show_about)
            help_menu.add_command(label="BitNet Documentation", 
                                  command=lambda: webbrowser.open("https://github.com/microsoft/BitNet"))
            menubar.add_cascade(label="Help", menu=help_menu)
        
    def create_tabs(self):
        """Create the main notebook tabs"""
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Import here to avoid circular imports
        try:
            from installer_gui_tabs import InstallerTab
            from control_panel_tab import ControlPanelTab, AdvancedTab
            
            # Create each tab
            self.installer_tab = InstallerTab(self.notebook, self)
            self.control_panel_tab = ControlPanelTab(self.notebook, self)
            self.advanced_tab = AdvancedTab(self.notebook, self)
            
            # Add tabs to notebook
            self.notebook.add(self.installer_tab, text="Installer")
            self.notebook.add(self.control_panel_tab, text="Control Panel")
            self.notebook.add(self.advanced_tab, text="Advanced")
            
            logger.debug("Successfully created tabs")
        except Exception as e:
            error_msg = f"Error creating tabs: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            messagebox.showerror("Error", f"Failed to initialize tabs: {str(e)}")
            
            # Create a basic frame as a placeholder
            frame = ttk.Frame(self.notebook)
            label = ttk.Label(frame, text=f"Error loading tabs: {str(e)}\n\nPlease check logs for details.")
            label.pack(padx=20, pady=20)
            self.notebook.add(frame, text="Error")
        
    def center_window(self):
        """Center the application window on the screen"""
        if self.is_root:
            self.parent.update_idletasks()
            width = self.parent.winfo_width()
            height = self.parent.winfo_height()
            x = (self.parent.winfo_screenwidth() // 2) - (width // 2)
            y = (self.parent.winfo_screenheight() // 2) - (height // 2)
            self.parent.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    def show_settings(self):
        """Show the settings dialog"""
        try:
            from installer_dialogs import SettingsDialog
            SettingsDialog(self.parent)
        except Exception as e:
            logger.error(f"Error showing settings dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open settings: {str(e)}")
        
    def show_log(self):
        """Show the log viewer dialog"""
        try:
            from installer_dialogs import LogViewerDialog
            LogViewerDialog(self.parent)
        except Exception as e:
            logger.error(f"Error showing log dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open log viewer: {str(e)}")
        
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About BitNet Installer",
            f"BitNet Installer v{VERSION}\n\n"
            "This installer will setup BitNet and its required dependencies.\n\n"
            " 2025 BitNet Project\n"
            "https://github.com/microsoft/BitNet"
        )
        
    def on_close(self):
        """Handle window close event"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit BitNet Installer?"):
            # Save config before exit
            save_config(self.config_data)
            self.parent.destroy()

if __name__ == "__main__":
    # Create the main window and application
    try:
        root = tk.Tk()
        app = InstallerApp(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        if 'root' in locals() and root:
            messagebox.showerror("Fatal Error", f"A fatal error occurred: {str(e)}\n\nSee logs for details.")
        else:
            print(error_msg)
        sys.exit(1)
