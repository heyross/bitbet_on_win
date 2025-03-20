#!/usr/bin/env python
# BitNet Installer Core Functionality
# Handles all installation logic and prerequisite checking

import os
import sys
import subprocess
import shutil
import logging
import platform
import time
import winreg
import urllib.request
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Import constants from installer module
from installer import BITNET_REPO, APP_DATA

# Configure logger to use the same as main installer
logger = logging.getLogger("BitNet")

# Custom exception for installation errors
class InstallationError(Exception):
    """Custom exception for installation errors"""
    pass

def check_windows_version():
    """Check if running on a supported Windows version"""
    if not platform.system() == "Windows":
        raise InstallationError("This installer only supports Windows operating systems")
    
    version = platform.version().split('.')
    windows_ver = int(platform.win32_ver()[0])
    
    if windows_ver < 10:
        raise InstallationError("Windows 10 or later is required to run BitNet")
    
    return True

def find_program(program_name, common_paths=None):
    """Find a program in PATH or common installation directories"""
    # Check in PATH
    which_cmd = subprocess.run(
        ["where", program_name], 
        capture_output=True, 
        text=True, 
        shell=True
    )
    
    if which_cmd.returncode == 0:
        # Return the first line of output (first match)
        return which_cmd.stdout.strip().split('\n')[0]
    
    # Check in common paths if provided
    if common_paths:
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
    
    return None

def check_git():
    """Check if Git is installed"""
    logger.info("Checking for Git installation")
    
    # Common Git installation paths
    git_common_paths = [
        r"%ProgramFiles%\Git\cmd\git.exe",
        r"%ProgramFiles(x86)%\Git\cmd\git.exe",
        r"%LocalAppData%\Programs\Git\cmd\git.exe"
    ]
    
    git_path = find_program("git.exe", git_common_paths)
    
    if git_path:
        logger.info(f"Git found at: {git_path}")
        return git_path
    
    logger.warning("Git not found")
    return None

def check_conda():
    """Check if Conda is installed"""
    logger.info("Checking for Conda installation")
    
    # Common Conda installation paths
    conda_common_paths = [
        r"%USERPROFILE%\miniconda3\Scripts\conda.exe",
        r"%USERPROFILE%\Anaconda3\Scripts\conda.exe",
        r"%ProgramData%\miniconda3\Scripts\conda.exe",
        r"%ProgramData%\Anaconda3\Scripts\conda.exe",
        r"%USERPROFILE%\miniconda3_bitnet\Scripts\conda.exe"
    ]
    
    conda_path = find_program("conda.exe", conda_common_paths)
    
    if conda_path:
        logger.info(f"Conda found at: {conda_path}")
        return conda_path
    
    logger.warning("Conda not found")
    return None

def check_visual_studio():
    """Check if Visual Studio Build Tools or full VS is installed"""
    logger.info("Checking for Visual Studio installation")
    
    # Check registry for VS installation
    vs_paths = []
    try:
        # Check Visual Studio 2022
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                          r"SOFTWARE\Microsoft\VisualStudio\SxS\VS7") as key:
            for i in range(winreg.QueryInfoKey(key)[1]):
                name, value, _ = winreg.EnumValue(key, i)
                vs_paths.append((name, value))
    except:
        pass
    
    # Check common VS paths
    for path in [r"C:\Program Files\Microsoft Visual Studio\2022",
                r"C:\Program Files (x86)\Microsoft Visual Studio\2022"]:
        if os.path.exists(path):
            logger.info(f"Visual Studio found at: {path}")
            return path
    
    if vs_paths:
        logger.info(f"Visual Studio found in registry: {vs_paths}")
        return vs_paths[0][1]  # Return the path of the first entry
    
    logger.warning("Visual Studio not found")
    return None

def download_file(url, destination, progress_callback=None):
    """Download a file with progress reporting"""
    logger.info(f"Downloading {url} to {destination}")
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    try:
        # Open request
        with urllib.request.urlopen(url) as response:
            file_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            # Start progress reporting
            if progress_callback:
                progress_callback(0, file_size)
            
            with open(destination, 'wb') as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(downloaded, file_size)
        
        logger.info(f"Successfully downloaded {url}")
        return True
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return False

def install_git(temp_dir, progress_callback=None):
    """Install Git for Windows"""
    logger.info("Installing Git for Windows")
    
    git_url = "https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe"
    installer_path = os.path.join(temp_dir, "git_installer.exe")
    
    # Download Git installer
    success = download_file(git_url, installer_path, progress_callback)
    if not success:
        raise InstallationError("Failed to download Git installer")
    
    # Run the installer silently
    logger.info("Running Git installer")
    try:
        result = subprocess.run(
            [installer_path, "/VERYSILENT", "/NORESTART"],
            check=True
        )
        
        # Verify installation
        if check_git():
            logger.info("Git installed successfully")
            return True
        else:
            raise InstallationError("Git installation could not be verified")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git installation failed: {str(e)}")
        raise InstallationError(f"Git installation failed with exit code {e.returncode}")

def install_miniconda(temp_dir, progress_callback=None):
    """Install Miniconda"""
    logger.info("Installing Miniconda")
    
    conda_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    installer_path = os.path.join(temp_dir, "miniconda_installer.exe")
    install_path = os.path.join(os.path.expanduser("~"), "miniconda3_bitnet")
    
    # Download Miniconda installer
    success = download_file(conda_url, installer_path, progress_callback)
    if not success:
        raise InstallationError("Failed to download Miniconda installer")
    
    # Run the installer silently
    logger.info(f"Running Miniconda installer to {install_path}")
    try:
        result = subprocess.run(
            [installer_path, "/S", "/RegisterPython=0", "/AddToPath=0", f"/D={install_path}"],
            check=True
        )
        
        # Verify installation
        conda_exe = os.path.join(install_path, "Scripts", "conda.exe")
        if os.path.exists(conda_exe):
            logger.info("Miniconda installed successfully")
            
            # Initialize conda
            logger.info("Initializing conda")
            subprocess.run([conda_exe, "init", "cmd.exe"], check=True)
            
            return conda_exe
        else:
            raise InstallationError("Miniconda installation could not be verified")
    except subprocess.CalledProcessError as e:
        logger.error(f"Miniconda installation failed: {str(e)}")
        raise InstallationError(f"Miniconda installation failed with exit code {e.returncode}")

def install_vs_build_tools(temp_dir, progress_callback=None):
    """Install Visual Studio Build Tools"""
    logger.info("Installing Visual Studio Build Tools")
    
    vs_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
    installer_path = os.path.join(temp_dir, "vs_buildtools.exe")
    
    # Download VS Build Tools installer
    success = download_file(vs_url, installer_path, progress_callback)
    if not success:
        raise InstallationError("Failed to download Visual Studio Build Tools installer")
    
    # Run the installer with required components
    logger.info("Running Visual Studio Build Tools installer")
    try:
        # Install with Desktop C++ workload
        result = subprocess.run([
            installer_path, 
            "--quiet", "--norestart", "--wait",
            "--add", "Microsoft.VisualStudio.Workload.VCTools",
            "--includeRecommended"
        ], check=True)
        
        # Verify installation
        if check_visual_studio():
            logger.info("Visual Studio Build Tools installed successfully")
            return True
        else:
            raise InstallationError("Visual Studio Build Tools installation could not be verified")
    except subprocess.CalledProcessError as e:
        logger.error(f"Visual Studio Build Tools installation failed: {str(e)}")
        raise InstallationError(f"Visual Studio Build Tools installation failed with exit code {e.returncode}")

def clone_bitnet(install_dir, progress_callback=None):
    """Clone the BitNet repository"""
    logger.info(f"Cloning BitNet repository to {install_dir}")
    
    try:
        # Create install directory if it doesn't exist
        os.makedirs(install_dir, exist_ok=True)
        
        # Check if directory is empty or repository already exists
        if os.path.exists(os.path.join(install_dir, ".git")):
            logger.info("BitNet repository already exists, pulling latest changes")
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=install_dir,
                    check=False,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"Git pull failed: {result.stderr}")
                    raise InstallationError(f"Git pull failed: {result.stderr}")
                return True
            except Exception as e:
                logger.error(f"Error pulling repository: {str(e)}")
                raise InstallationError(f"Error pulling repository: {str(e)}")
        
        # Log the Git command for debugging
        logger.info(f"Cloning from {BITNET_REPO} to {install_dir}")
        
        # Clone with progress reporting
        if progress_callback:
            # Start progress indication
            progress_callback(0, 100)
            
            # Clone in a separate thread to allow progress reporting
            clone_process = subprocess.Popen(
                ["git", "clone", "--recursive", "--progress", BITNET_REPO, install_dir],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Capture all output for error reporting
            all_output = []
            
            # Parse git output for progress
            for line in clone_process.stderr:
                all_output.append(line)
                logger.debug(f"Git output: {line.strip()}")
                if "Receiving objects" in line and "%" in line:
                    try:
                        percent = int(line.split("%")[0].split()[-1])
                        progress_callback(percent, 100)
                    except:
                        pass
                        
            # Ensure process completes
            returncode = clone_process.wait()
            if returncode != 0:
                error_msg = "\n".join(all_output)
                logger.error(f"Git clone failed with exit code {returncode}. Details: {error_msg}")
                
                # Special handling for common Git errors
                if "could not create work tree" in error_msg.lower():
                    raise InstallationError(f"Git clone failed: Could not create work tree. Check folder permissions.")
                elif "authentication failed" in error_msg.lower():
                    raise InstallationError(f"Git clone failed: Authentication failed. Check network connection.")
                else:
                    raise InstallationError(f"Git clone failed with exit code {returncode}. Details: {error_msg}")
                
            # Complete progress
            progress_callback(100, 100)
        else:
            # Simple clone without progress reporting but with error capture
            try:
                result = subprocess.run(
                    ["git", "clone", "--recursive", BITNET_REPO, install_dir],
                    check=False,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"Git clone failed: {result.stderr}")
                    raise InstallationError(f"Git clone failed: {result.stderr}")
            except Exception as e:
                logger.error(f"Error during Git clone: {str(e)}")
                raise InstallationError(f"Error during Git clone: {str(e)}")
        
        logger.info("BitNet repository cloned successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clone BitNet repository: {str(e)}")
        raise InstallationError(f"Failed to clone BitNet repository: {str(e)}")

def setup_conda_env(conda_path, install_dir, enable_gpu=False, progress_callback=None):
    """Set up the conda environment for BitNet"""
    logger.info("Setting up conda environment")
    
    env_name = "bitnet-cpp"
    
    try:
        # Check if the environment already exists
        result = subprocess.run(
            [conda_path, "env", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if env_name in result.stdout:
            logger.info(f"Conda environment '{env_name}' already exists")
        else:
            # Create the environment
            logger.info(f"Creating conda environment '{env_name}'")
            subprocess.run(
                [conda_path, "create", "-n", env_name, "python=3.9", "-y"],
                check=True
            )
        
        # Create or update requirements.txt if needed
        requirements_path = os.path.join(install_dir, "requirements.txt")
        if not os.path.exists(requirements_path):
            logger.info("Creating requirements.txt")
            with open(requirements_path, 'w') as f:
                f.write("numpy>=1.20.0\n")
                f.write("torch>=1.10.0\n")
                f.write("tqdm>=4.62.0\n")
                f.write("scipy>=1.7.0\n")
                f.write("matplotlib>=3.4.0\n")
        
        # Install requirements
        logger.info("Installing Python requirements")
        subprocess.run(
            [conda_path, "run", "-n", env_name, "pip", "install", "-r", requirements_path],
            check=True,
            cwd=install_dir
        )
        
        # Install BitNet package in development mode
        logger.info("Installing BitNet package")
        
        # Skip the standard installation attempt as BitNet doesn't have setup.py/pyproject.toml
        logger.info("Using .pth file approach for BitNet package installation")
        
        # Look for potential Python package directories
        potential_dirs = []
        for root, dirs, files in os.walk(install_dir):
            # Look for directories that might be Python packages
            for d in dirs:
                if os.path.exists(os.path.join(root, d, "__init__.py")):
                    potential_dirs.append(os.path.join(root, d))
            
            # Also check for any Python files in the root
            python_files = [f for f in files if f.endswith(".py")]
            if python_files:
                potential_dirs.append(root)
            
            # Don't go more than 2 levels deep
            if root.replace(install_dir, "").count(os.sep) >= 2:
                dirs[:] = []
        
        # If we found potential package directories, try to add them to Python path
        if potential_dirs:
            logger.info(f"Found potential package directories: {potential_dirs}")
            
            # Create a .pth file in the site-packages directory to add our paths
            site_packages_cmd = [conda_path, "run", "-n", env_name, "python", "-c", 
                                "import site; print(site.getsitepackages()[0])"]
            site_packages_result = subprocess.run(
                site_packages_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            site_packages_dir = site_packages_result.stdout.strip()
            pth_file_path = os.path.join(site_packages_dir, "bitnet.pth")
            
            with open(pth_file_path, "w") as f:
                for dir_path in potential_dirs:
                    f.write(dir_path + "\n")
            
            logger.info(f"Created path file at {pth_file_path} with paths: {', '.join(potential_dirs)}")
            
            # Verify it worked by importing
            verify_cmd = [conda_path, "run", "-n", env_name, "python", "-c", 
                         "try:\n    import bitnet\n    print('Import successful')\nexcept ImportError as e:\n    print(f'Import failed: {e}')"]
            verify_result = subprocess.run(
                verify_cmd,
                capture_output=True,
                text=True
            )
            
            if "Import successful" in verify_result.stdout:
                logger.info("BitNet package successfully installed using path file")
            else:
                logger.warning(f"BitNet package import verification failed: {verify_result.stdout} {verify_result.stderr}")
        else:
            logger.warning("Could not find any potential Python package directories")
        
        logger.info("Conda environment setup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Conda environment setup failed: {str(e)}")
        raise InstallationError(f"Conda environment setup failed with exit code {e.returncode}")
    except Exception as e:
        logger.error(f"Conda environment setup failed: {str(e)}")
        raise InstallationError(f"Conda environment setup failed: {str(e)}")

def create_startup_script(install_dir, conda_path):
    """Create a startup script for BitNet"""
    logger.info("Creating BitNet startup script")
    
    startup_path = os.path.join(os.path.dirname(install_dir), "start_bitnet.bat")
    
    try:
        with open(startup_path, 'w') as f:
            f.write("@echo off\n")
            f.write("echo Starting BitNet...\n")
            f.write("echo.\n")
            
            # Add conda to PATH
            f.write(f'set "PATH=%PATH%;{os.path.dirname(conda_path)};{os.path.dirname(os.path.dirname(conda_path))}"\n')
            
            # Change to install directory
            f.write(f'cd /d "{install_dir}"\n')
            f.write("echo Running BitNet. If this fails, please check the README.md for proper launch instructions.\n")
            f.write("echo.\n")
            
            # Add different startup methods
            f.write("if exist build.bat (\n")
            f.write("  echo Building BitNet with Visual Studio...\n")
            f.write("  call build.bat\n")
            f.write(") else if exist CMakeLists.txt (\n")
            f.write("  echo Running CMake build process...\n")
            f.write(f'  "{conda_path}" run -n bitnet-cpp cmd /c "mkdir build 2>nul & cd build & cmake .. & cmake --build . --config Release"\n')
            f.write(") else if exist setup.py (\n")
            f.write("  echo Installing BitNet from setup.py...\n")
            f.write(f'  "{conda_path}" run -n bitnet-cpp pip install -e .\n')
            f.write("  echo.\n")
            f.write("  echo BitNet installed. Please refer to the README.md for usage instructions.\n")
            f.write(") else (\n")
            f.write("  echo.\n")
            f.write("  echo NOTE: Unable to determine how to build or run BitNet.\n")
            f.write("  echo Please refer to the README.md in the BitNet directory for instructions.\n")
            f.write(f'  echo Project directory: {install_dir}\n')
            f.write(")\n")
            f.write("pause\n")
        
        logger.info(f"Startup script created at {startup_path}")
        return startup_path
    except Exception as e:
        logger.error(f"Failed to create startup script: {str(e)}")
        raise InstallationError(f"Failed to create startup script: {str(e)}")

def create_shortcut(startup_script_path):
    """Create a desktop shortcut for the BitNet startup script"""
    try:
        import time
        logger.info("Creating desktop shortcut")
        
        # Get the desktop path
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, "BitNet.lnk")
        
        # Ensure desktop directory exists (it should, but check anyway)
        if not os.path.exists(desktop_path):
            logger.warning(f"Desktop directory not found at {desktop_path}, trying alternative paths")
            # Try alternative desktop paths
            desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            shortcut_path = os.path.join(desktop_path, "BitNet.lnk")
            
            # If still doesn't exist, try to create it
            if not os.path.exists(desktop_path):
                logger.warning(f"Alternative desktop path {desktop_path} also not found, creating directory")
                os.makedirs(desktop_path, exist_ok=True)
        
        # Check if Windows
        if os.name == 'nt':
            # Ensure parent directory of shortcut exists
            os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
            
            # Ensure startup script exists
            if not os.path.exists(startup_script_path):
                logger.error(f"Startup script not found at {startup_script_path}")
                return False
                
            # Use PowerShell to create shortcut on Windows
            powershell_command = f'''
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{startup_script_path}"
            $Shortcut.WorkingDirectory = "{os.path.dirname(startup_script_path)}"
            $Shortcut.Description = "Start BitNet"
            $Shortcut.Save()
            '''
            
            # Create a temporary PowerShell script
            ps_script_path = os.path.join(os.environ.get('TEMP', os.getcwd()), 'create_shortcut.ps1')
            with open(ps_script_path, 'w') as f:
                f.write(powershell_command)
            
            # Execute the PowerShell script
            result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path], 
                                    capture_output=True, 
                                    text=True)
            
            if result.returncode != 0:
                logger.error(f"PowerShell shortcut creation failed: {result.stderr}")
                
            # Remove the temporary script
            try:
                time.sleep(1)  # Wait a bit before deleting the file
                os.unlink(ps_script_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary script: {str(e)}")
            
            # Verify shortcut was created
            if os.path.exists(shortcut_path):
                logger.info(f"Desktop shortcut created at {shortcut_path}")
                return True
            else:
                # Try a direct method as fallback
                try:
                    logger.warning("Attempting fallback shortcut creation method")
                    # Create a simple batch file as an alternative
                    with open(shortcut_path.replace(".lnk", ".bat"), 'w') as f:
                        f.write(f'@echo off\nstart "" "{startup_script_path}"\n')
                    logger.info(f"Created batch file shortcut at {shortcut_path.replace('.lnk', '.bat')}")
                    return True
                except Exception as e:
                    logger.error(f"Fallback shortcut creation also failed: {str(e)}")
                    return False
        else:
            logger.warning("Desktop shortcut creation is only supported on Windows")
            return False
    except Exception as e:
        logger.error(f"Failed to create desktop shortcut: {str(e)}")
        # Don't raise an exception, just return False to indicate failure
        # This is a non-critical error, the installation can still proceed
        return False
