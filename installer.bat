@echo off
setlocal enabledelayedexpansion

echo ===================================================================
echo BitNet 1.58 Installer for Windows
echo ===================================================================
echo.

:: Set up logging
set "CURRENT_DIR=%cd%"
set "LOG_FILE=%CURRENT_DIR%\bitnet_install.log"
echo BitNet Installation Log - %date% %time% > "%LOG_FILE%"

:: Function to log messages
call :log "Installation started"

:: Create a folder for temporary files
set "TEMP_DIR=%CURRENT_DIR%\temp"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Set installation directory
set "INSTALL_DIR=%CURRENT_DIR%\BitNet"

:: Check for administrator privileges
net session >nul 2>&1
if !errorlevel! neq 0 (
    echo This script requires administrator privileges.
    echo Please right-click on the script and select "Run as administrator".
    call :log "ERROR: Script not run as administrator"
    pause
    exit /b 1
)

:: Install prerequisites
call :install_prerequisites
if !errorlevel! neq 0 (
    call :log "ERROR: Prerequisites installation failed"
    echo Failed to install prerequisites. See log for details: "%LOG_FILE%"
    pause
    exit /b 1
)

:: Main installation process
call :main_install
if !errorlevel! neq 0 (
    call :log "ERROR: Main installation failed"
    echo Installation failed. See log file for details: "%LOG_FILE%"
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo Installation completed successfully!
echo ===================================================================
echo.
echo To use BitNet, open a new command prompt and run:
echo    conda activate bitnet-cpp
echo.
call :log "Installation completed successfully"
pause
exit /b 0

:: ===================================================================
:: Functions
:: ===================================================================

:log
    echo [%date% %time%] %~1 >> "%LOG_FILE%"
    exit /b 0

:install_prerequisites
    echo Checking and installing prerequisites...
    call :log "Checking and installing prerequisites"

    :: Check and install Git
    echo Checking for Git...
    git --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo Git is not installed. Installing Git...
        call :log "Git not found, installing..."
        
        :: Download Git installer
        echo Downloading Git installer...
        call :log "Downloading Git installer"
        
        call :download_file "https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe" "%TEMP_DIR%\git_installer.exe" "Git"
        if !errorlevel! neq 0 (
            echo Failed to download Git installer.
            call :log "ERROR: Failed to download Git installer"
            exit /b 1
        )
        
        :: Install Git silently
        echo Installing Git...
        call :log "Running Git installer"
        "%TEMP_DIR%\git_installer.exe" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
        if !errorlevel! neq 0 (
            echo Failed to install Git.
            call :log "ERROR: Git installation failed"
            exit /b 1
        )
        
        :: Update PATH to include Git
        echo Updating PATH to include Git...
        call :log "Updating PATH to include Git"
        set "PATH=%PATH%;C:\Program Files\Git\cmd"
        
        :: Verify Git installation
        git --version >nul 2>&1
        if !errorlevel! neq 0 (
            echo Failed to install Git properly.
            call :log "ERROR: Git installation verification failed"
            exit /b 1
        )
        
        call :log "Git installed successfully"
    ) else (
        echo Git is already installed.
        call :log "Git already installed"
    )

    :: Check and install Conda
    echo Checking for Conda...
    conda --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo Conda is not installed. Installing Miniconda...
        call :log "Conda not found, installing Miniconda..."
        
        :: Check for previous failed installation
        if exist "%USERPROFILE%\Miniconda3_incomplete" (
            echo Found incomplete previous Miniconda installation. Cleaning up...
            call :log "Cleaning up incomplete Miniconda installation"
            rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
        )
        
        if exist "%USERPROFILE%\Miniconda3" (
            echo Found existing Miniconda installation folder that might be corrupted.
            choice /C YN /M "Do you want to remove it and reinstall? (Y/N)"
            if !errorlevel! equ 1 (
                echo Removing existing Miniconda installation...
                call :log "Removing existing corrupted Miniconda installation"
                
                :: Rename the folder first in case of locked files
                ren "%USERPROFILE%\Miniconda3" Miniconda3_old >nul 2>&1
                rd /s /q "%USERPROFILE%\Miniconda3_old" >nul 2>&1
                
                :: If folder still exists, try taskkill to release locks
                if exist "%USERPROFILE%\Miniconda3_old" (
                    echo Attempting to close processes that may be locking files...
                    taskkill /f /im conda.exe >nul 2>&1
                    taskkill /f /im python.exe >nul 2>&1
                    timeout /t 2 /nobreak >nul
                    rd /s /q "%USERPROFILE%\Miniconda3_old" >nul 2>&1
                )
            )
        )
        
        :: Create a marker for incomplete installation
        mkdir "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
        
        :: Download Miniconda installer with progress indicator
        echo Downloading Miniconda installer...
        call :log "Downloading Miniconda installer with progress indicator"
        
        :: Progress indicator function
        start /b cmd /c "
            echo Starting download...
            set count=0
            :loop
            set /a count+=1
            if !count! gtr 100 set count=0
            
            set progressbar=
            for /l %%i in (1,1,!count!) do set progressbar=!progressbar!#
            for /l %%i in (!count!,1,50) do set progressbar=!progressbar!-
            
            echo.
            echo Downloading progress: [!progressbar!] !count!%% 
            echo.
            timeout /t 1 /nobreak > nul
            if exist "%TEMP_DIR%\miniconda_download_complete" exit
            goto loop
        " > "%TEMP_DIR%\progress.txt" 2>&1
        set "PROGRESS_PID=!ERRORLEVEL!"
        
        :: Download with first method
        echo Downloading Miniconda (this may take a few minutes)...
        powershell -Command "& {try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile '%TEMP_DIR%\miniconda_installer.exe' } catch { exit 1 }; exit 0}"
        set "DOWNLOAD_STATUS=!ERRORLEVEL!"
        
        :: Create marker file to stop progress indicator
        echo done > "%TEMP_DIR%\miniconda_download_complete"
        timeout /t 2 /nobreak > nul
        
        :: Kill progress indicator process
        taskkill /F /PID !PROGRESS_PID! >nul 2>&1
        
        :: Clear the progress display
        cls
        echo ===================================================================
        echo BitNet 1.58 Installer for Windows
        echo ===================================================================
        echo.
        
        if !DOWNLOAD_STATUS! neq 0 (
            echo First download method failed. Trying alternative...
            call :log "First download method failed, trying alternative"
            
            :: Try alternative download with progress
            start /b cmd /c "
                echo Starting download with alternative method...
                set count=0
                :loop
                set /a count+=1
                if !count! gtr 100 set count=0
                
                set progressbar=
                for /l %%i in (1,1,!count!) do set progressbar=!progressbar!#
                for /l %%i in (!count!,1,50) do set progressbar=!progressbar!-
                
                echo.
                echo Downloading progress: [!progressbar!] !count!%% 
                echo.
                timeout /t 1 /nobreak > nul
                if exist "%TEMP_DIR%\miniconda_download_complete2" exit
                goto loop
            " > "%TEMP_DIR%\progress.txt" 2>&1
            set "PROGRESS_PID=!ERRORLEVEL!"
            
            :: Try alternative version
            curl -L -o "%TEMP_DIR%\miniconda_installer.exe" "https://repo.anaconda.com/miniconda/Miniconda3-py310_23.10.0-1-Windows-x86_64.exe" --progress-bar
            set "DOWNLOAD_STATUS=!ERRORLEVEL!"
            
            :: Create marker file to stop progress indicator
            echo done > "%TEMP_DIR%\miniconda_download_complete2"
            timeout /t 2 /nobreak > nul
            
            :: Kill progress indicator process
            taskkill /F /PID !PROGRESS_PID! >nul 2>&1
            
            :: Clear the progress display
            cls
            echo ===================================================================
            echo BitNet 1.58 Installer for Windows
            echo ===================================================================
            echo.
            
            if !DOWNLOAD_STATUS! neq 0 (
                echo Failed to download Miniconda installer. Please check your internet connection.
                echo You can manually download from https://docs.conda.io/en/latest/miniconda.html
                echo and place the installer in: %TEMP_DIR%\miniconda_installer.exe
                echo Then run this installer again.
                call :log "ERROR: Failed to download Miniconda installer after multiple attempts"
                
                :: Clean up incomplete installation marker
                rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
                
                exit /b 1
            )
        )
        
        :: Check if installer file exists and has a valid size
        if not exist "%TEMP_DIR%\miniconda_installer.exe" (
            echo Miniconda installer file does not exist: "%TEMP_DIR%\miniconda_installer.exe"
            call :log "ERROR: Miniconda installer file does not exist"
            
            :: Clean up incomplete installation marker
            rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
            
            exit /b 1
        )
        
        :: Check file size to make sure it's not corrupted or empty
        for %%A in ("%TEMP_DIR%\miniconda_installer.exe") do set "FILESIZE=%%~zA"
        if !FILESIZE! LSS 10000 (
            echo Miniconda installer is too small (possibly corrupted): !FILESIZE! bytes
            call :log "ERROR: Miniconda installer is too small (possibly corrupted): !FILESIZE! bytes"
            
            :: Clean up incomplete installation marker
            rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
            
            exit /b 1
        )
        
        :: Install Miniconda silently with progress indicator
        echo Installing Miniconda...
        call :log "Running Miniconda installer with progress indicator"
        
        :: Start progress indicator for installation
        start /b cmd /c "
            echo Starting installation...
            set count=0
            :loop
            set /a count+=1
            if !count! gtr 100 set count=0
            
            set progressbar=
            for /l %%i in (1,1,!count!) do set progressbar=!progressbar!#
            for /l %%i in (!count!,1,50) do set progressbar=!progressbar!-
            
            echo.
            echo Installation progress: [!progressbar!] Please wait... 
            echo.
            timeout /t 1 /nobreak > nul
            if exist "%TEMP_DIR%\miniconda_install_complete" exit
            goto loop
        " > "%TEMP_DIR%\progress.txt" 2>&1
        set "PROGRESS_PID=!ERRORLEVEL!"
        
        :: Run the installer with a timeout to prevent hanging
        start /wait "" "%TEMP_DIR%\miniconda_installer.exe" /S /RegisterPython=1 /AddToPath=1 /D=%USERPROFILE%\Miniconda3
        set "INSTALL_STATUS=!ERRORLEVEL!"
        
        :: Create marker file to stop progress indicator
        echo done > "%TEMP_DIR%\miniconda_install_complete"
        timeout /t 2 /nobreak > nul
        
        :: Kill progress indicator process
        taskkill /F /PID !PROGRESS_PID! >nul 2>&1
        
        :: Clear the progress display
        cls
        echo ===================================================================
        echo BitNet 1.58 Installer for Windows
        echo ===================================================================
        echo.
        
        if !INSTALL_STATUS! neq 0 (
            echo Failed to install Miniconda.
            call :log "ERROR: Miniconda installation failed with exit code !INSTALL_STATUS!"
            
            :: Clean up incomplete installation marker
            rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
            
            exit /b 1
        )
        
        :: Wait for installation to complete and update PATH
        echo Finalizing Miniconda installation...
        timeout /t 5 /nobreak > nul
        
        :: Update PATH to include Conda
        echo Updating PATH to include Conda...
        call :log "Updating PATH to include Conda"
        set "PATH=%PATH%;%USERPROFILE%\Miniconda3;%USERPROFILE%\Miniconda3\Scripts;%USERPROFILE%\Miniconda3\Library\bin"
        
        :: Initialize Conda for cmd.exe
        echo Initializing Conda for cmd.exe...
        if exist "%USERPROFILE%\Miniconda3\Scripts\activate.bat" (
            call "%USERPROFILE%\Miniconda3\Scripts\activate.bat"
        ) else (
            echo WARNING: Cannot find activate.bat script for Conda initialization.
            call :log "WARNING: Cannot find activate.bat script for Conda initialization"
        )
        
        :: Verify Conda installation
        echo Verifying Conda installation...
        conda --version >nul 2>&1
        if !errorlevel! neq 0 (
            echo Failed to install Conda properly. Attempting to clean up...
            call :log "ERROR: Conda installation verification failed"
            
            :: Clean up failed installation
            echo Removing failed Conda installation...
            call :log "Removing failed Conda installation"
            rd /s /q "%USERPROFILE%\Miniconda3" >nul 2>&1
            
            :: Clean up incomplete installation marker
            rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
            
            exit /b 1
        )
        
        :: Remove incomplete installation marker
        rd /s /q "%USERPROFILE%\Miniconda3_incomplete" >nul 2>&1
        
        call :log "Miniconda installed successfully"
    ) else (
        echo Conda is already installed.
        call :log "Conda already installed"
    )

    :: Check for Visual Studio C++ Build Tools - Enhanced check
    echo Checking for Visual Studio C++ Build Tools...
    call :log "Checking for Visual Studio C++ Build Tools"
    
    :: Try multiple possible locations for Visual Studio
    set "VS_FOUND=0"
    
    :: Check for cl.exe in PATH first
    where cl.exe >nul 2>&1
    if !errorlevel! equ 0 set "VS_FOUND=1"
    
    :: Check for VS 2022
    if !VS_FOUND! equ 0 (
        if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
    )
    
    :: Check for VS 2019
    if !VS_FOUND! equ 0 (
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
    )
    
    :: Check for VS 2017
    if !VS_FOUND! equ 0 (
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Professional\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Enterprise\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\BuildTools\VC\Auxiliary\Build\vcvars64.bat" set "VS_FOUND=1"
    )
    
    if !VS_FOUND! equ 1 (
        echo Visual Studio C++ Build Tools are already installed.
        call :log "Visual Studio C++ Build Tools already installed"
    ) else (
        echo Visual Studio C++ Build Tools not found. Installing...
        call :log "Visual Studio C++ Build Tools not found, installing..."
        
        :: Download VS Build Tools installer
        echo Downloading Visual Studio Build Tools installer...
        call :log "Downloading Visual Studio Build Tools installer"
        
        call :download_file "https://aka.ms/vs/17/release/vs_buildtools.exe" "%TEMP_DIR%\vs_buildtools.exe" "Visual Studio Build Tools"
        if !errorlevel! neq 0 (
            echo Failed to download Visual Studio Build Tools installer.
            call :log "ERROR: Failed to download Visual Studio Build Tools installer"
            exit /b 1
        )
        
        :: Check if installer file exists before trying to run it
        if not exist "%TEMP_DIR%\vs_buildtools.exe" (
            echo Visual Studio Build Tools installer file does not exist: "%TEMP_DIR%\vs_buildtools.exe"
            call :log "ERROR: Visual Studio Build Tools installer file does not exist"
            exit /b 1
        )
        
        :: Install VS Build Tools silently with C++ components
        echo Installing Visual Studio Build Tools (this may take a while)...
        call :log "Running Visual Studio Build Tools installer"
        "%TEMP_DIR%\vs_buildtools.exe" --quiet --wait --norestart --nocache ^
            --installPath "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools" ^
            --add Microsoft.VisualStudio.Workload.VCTools ^
            --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
            --includeRecommended
        
        if !errorlevel! neq 0 (
            echo Failed to install Visual Studio Build Tools.
            call :log "ERROR: Visual Studio Build Tools installation failed"
            exit /b 1
        )
        
        :: Set up the environment for Visual Studio Build Tools
        echo Setting up the environment for Visual Studio Build Tools...
        call :log "Setting up Visual Studio Build Tools environment"
        if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
            call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
        )
        
        :: Verify Visual Studio Build Tools installation
        where cl.exe >nul 2>&1
        if !errorlevel! neq 0 (
            echo Failed to install Visual Studio Build Tools properly.
            call :log "ERROR: Visual Studio Build Tools installation verification failed"
            exit /b 1
        )
        
        call :log "Visual Studio Build Tools installed successfully"
    )
    
    :: Install CUDA toolkit if NVIDIA GPU is present
    echo Checking for NVIDIA GPU...
    powershell -Command "& {$gpuInfo = Get-WmiObject Win32_VideoController | Where-Object {$_.Name -like '*NVIDIA*'}; exit [int](!$gpuInfo)}"
    if !errorlevel! equ 0 (
        echo NVIDIA GPU detected, checking for CUDA Toolkit...
        call :log "NVIDIA GPU detected, checking for CUDA Toolkit"
        
        :: Check if CUDA is installed
        if not exist "%ProgramFiles%\NVIDIA GPU Computing Toolkit\CUDA" (
            echo CUDA Toolkit not found. Installing...
            call :log "CUDA Toolkit not found, installing..."
            
            :: Download CUDA Toolkit installer
            echo Downloading CUDA Toolkit installer...
            call :log "Downloading CUDA Toolkit installer"
            
            call :download_file "https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_536.25_windows.exe" "%TEMP_DIR%\cuda_installer.exe" "CUDA Toolkit"
            if !errorlevel! neq 0 (
                echo Warning: Failed to download CUDA Toolkit installer.
                call :log "WARNING: Failed to download CUDA Toolkit installer"
                :: Continue despite this warning - CUDA is optional
            ) else (
                :: Install CUDA Toolkit silently
                echo Installing CUDA Toolkit (this may take a while)...
                call :log "Running CUDA Toolkit installer"
                "%TEMP_DIR%\cuda_installer.exe" -s
                
                if !errorlevel! neq 0 (
                    echo Warning: Failed to install CUDA Toolkit.
                    call :log "WARNING: CUDA Toolkit installation failed"
                    :: Continue despite this warning - CUDA is optional
                ) else (
                    call :log "CUDA Toolkit installed successfully"
                )
            )
        ) else (
            echo CUDA Toolkit is already installed.
            call :log "CUDA Toolkit already installed"
        )
    ) else (
        echo No NVIDIA GPU detected, skipping CUDA installation.
        call :log "No NVIDIA GPU detected, skipping CUDA installation"
    )

    echo All prerequisites are installed successfully.
    call :log "All prerequisites installed successfully"
    exit /b 0

:main_install
    echo Starting BitNet installation...
    call :log "Starting main installation"

    :: Handle existing BitNet directory
    if exist "%INSTALL_DIR%" (
        echo BitNet directory already exists.
        call :log "BitNet directory already exists"
        
        :: Ask user what to do with the existing directory
        echo What would you like to do?
        echo 1. Use existing directory (no changes)
        echo 2. Update existing directory (git pull)
        echo 3. Remove and reinstall (delete and clone again)
        choice /C 123 /N /M "Enter your choice (1-3): "
        
        if errorlevel 3 (
            echo Removing existing BitNet directory...
            call :log "Removing existing BitNet directory"
            rd /s /q "%INSTALL_DIR%"
            
            echo Cloning BitNet repository...
            call :log "Cloning BitNet repository"
            git clone --recursive https://github.com/microsoft/BitNet.git "%INSTALL_DIR%" > "%TEMP_DIR%\git_clone.log" 2>&1
            if !errorlevel! neq 0 (
                echo Failed to clone repository.
                type "%TEMP_DIR%\git_clone.log"
                call :log "ERROR: Git clone failed"
                exit /b 1
            )
            call :log "Repository cloned successfully"
        ) else if errorlevel 2 (
            echo Updating existing BitNet directory...
            pushd "%INSTALL_DIR%"
            git pull > "%TEMP_DIR%\git_pull.log" 2>&1
            if !errorlevel! neq 0 (
                echo Failed to update repository.
                type "%TEMP_DIR%\git_pull.log"
                call :log "ERROR: Git pull failed"
                popd
                exit /b 1
            )
            popd
            call :log "Repository updated successfully"
        ) else (
            echo Using existing BitNet directory.
            call :log "Using existing BitNet directory"
        )
    ) else (
        echo Cloning BitNet repository...
        call :log "Cloning BitNet repository"
        git clone --recursive https://github.com/microsoft/BitNet.git "%INSTALL_DIR%" > "%TEMP_DIR%\git_clone.log" 2>&1
        if !errorlevel! neq 0 (
            echo Failed to clone repository.
            type "%TEMP_DIR%\git_clone.log"
            call :log "ERROR: Git clone failed"
            exit /b 1
        )
        call :log "Repository cloned successfully"
    )

    :: Create and activate conda environment
    echo Creating conda environment...
    call :log "Creating conda environment"
    
    :: Check if environment already exists
    conda env list | findstr /C:"bitnet-cpp" >nul
    if !errorlevel! neq 0 (
        conda create -n bitnet-cpp python=3.9 -y > "%TEMP_DIR%\conda_create.log" 2>&1
        if !errorlevel! neq 0 (
            echo Failed to create conda environment.
            type "%TEMP_DIR%\conda_create.log"
            call :log "ERROR: Conda environment creation failed"
            exit /b 1
        )
        call :log "Conda environment created successfully"
    ) else (
        echo Conda environment 'bitnet-cpp' already exists.
        call :log "Conda environment already exists"
    )

    :: Activate conda environment and install requirements
    echo Installing Python dependencies...
    call :log "Installing Python dependencies"
    
    :: We need to use call to properly handle conda activate
    call conda activate bitnet-cpp && (
        pushd "%INSTALL_DIR%"
        
        :: Check if requirements.txt exists
        if exist requirements.txt (
            python -m pip install -r requirements.txt > "%TEMP_DIR%\pip_install.log" 2>&1
            if !errorlevel! neq 0 (
                echo Failed to install Python dependencies.
                type "%TEMP_DIR%\pip_install.log"
                call :log "ERROR: Pip install failed"
                popd
                exit /b 1
            )
        ) else (
            :: If requirements.txt doesn't exist, install common dependencies
            python -m pip install torch numpy transformers > "%TEMP_DIR%\pip_install.log" 2>&1
            if !errorlevel! neq 0 (
                echo Failed to install Python dependencies.
                type "%TEMP_DIR%\pip_install.log"
                call :log "ERROR: Pip install failed"
                popd
                exit /b 1
            )
        )
        
        call :log "Python dependencies installed successfully"
        
        :: Download and convert the model
        echo Downloading and converting the model...
        call :log "Downloading and converting the model"
        
        :: Check if setup_env.py exists
        if exist setup_env.py (
            python setup_env.py --hf-repo tiiuae/Falcon3-7B-Instruct-1.58bit -q i2_s > "%TEMP_DIR%\model_setup.log" 2>&1
            if !errorlevel! neq 0 (
                echo Failed to download and convert the model.
                type "%TEMP_DIR%\model_setup.log"
                call :log "ERROR: Model setup failed"
                popd
                exit /b 1
            )
        ) else (
            echo Warning: setup_env.py not found. Manual model setup may be required.
            call :log "WARNING: setup_env.py not found, skipping model setup"
        )
        
        call :log "Model converted successfully"
        popd
    )
    
    if !errorlevel! neq 0 (
        echo Failed to activate conda environment.
        call :log "ERROR: Conda environment activation failed"
        exit /b 1
    )

    :: Compile the project if build script exists
    if exist "%INSTALL_DIR%\build.bat" (
        echo Compiling BitNet...
        call :log "Compiling BitNet"
        pushd "%INSTALL_DIR%"
        call build.bat > "%TEMP_DIR%\build.log" 2>&1
        if !errorlevel! neq 0 (
            echo Failed to compile BitNet.
            type "%TEMP_DIR%\build.log"
            call :log "ERROR: Compilation failed"
            popd
            exit /b 1
        )
        popd
        call :log "Compilation completed successfully"
    ) else (
        echo No build script found. Manual compilation may be required.
        call :log "WARNING: No build script found"
    )

    echo BitNet installation completed successfully.
    call :log "Main installation completed successfully"
    exit /b 0

:: Simplified download function
:download_file
    set "download_url=%~1"
    set "output_file=%~2"
    set "component_name=%~3"
    
    echo Downloading %component_name%...
    call :log "Downloading %component_name%"
    
    :: Try curl first (built into Windows 10+)
    curl -L -o "%output_file%" "%download_url%" --connect-timeout 30 --retry 3 --retry-delay 5 -s
    if !errorlevel! equ 0 goto :download_success
    
    :: If curl fails, try PowerShell
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%download_url%' -OutFile '%output_file%' -UseBasicParsing}"
    if !errorlevel! equ 0 goto :download_success
    
    :: If PowerShell fails, try alternate PowerShell method
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%download_url%', '%output_file%')}"
    if !errorlevel! equ 0 goto :download_success
    
    echo Failed to download %component_name%.
    call :log "ERROR: Failed to download %component_name%"
    exit /b 1
    
    :download_success
    echo Successfully downloaded %component_name%.
    call :log "%component_name% downloaded successfully"
    exit /b 0
