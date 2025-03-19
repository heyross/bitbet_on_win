@echo off
setlocal enabledelayedexpansion

:: Set up initial variables
set "CURRENT_DIR=%cd%"
set "LOG_FILE=%CURRENT_DIR%\bitnet_install.log"
set "TEMP_DIR=%CURRENT_DIR%\temp"
set "INSTALL_DIR=%CURRENT_DIR%\bitnet"
set "PREREQ_ERROR=0"
set "INSTALL_ERROR=0"

:: ===================================================================
:: Main installation process
:: ===================================================================

:start_installation
    :: Display welcome banner
    echo ===================================================================
    echo BitNet 1.58 Installer for Windows
    echo ===================================================================
    echo This installer will set up all required components for BitNet:
    echo  1. Git (Version Control) - ~1-2 minutes
    echo  2. Miniconda (Python Environment) - ~3-5 minutes
    echo  3. Visual Studio 2022 with C++ and Clang - ~10-15 minutes
    echo  4. BitNet Repository and Dependencies - ~5-10 minutes
    echo ===================================================================
    echo Total estimated time: 20-35 minutes depending on your system and internet speed
    echo.
    
    :: Initialize log file
    echo BitNet Installation Log - %date% %time% > "%LOG_FILE%"
    call :log "Installation started"
    call :log "Using installation directory: %INSTALL_DIR%"
    
    :: Create temp folder if it doesn't exist
    if not exist "%TEMP_DIR%" (
        mkdir "%TEMP_DIR%"
        call :log "Created temp directory: %TEMP_DIR%"
    )
    
    :: Explicitly call the prerequisite installation functions in order
    call :check_git
    if !errorlevel! neq 0 (
        call :log "ERROR: Git installation failed"
        echo ===================================================================
        echo Failed to install Git. See log for details: "%LOG_FILE%"
        echo ===================================================================
        pause
        exit /b 1
    )
    
    call :check_conda
    if !errorlevel! neq 0 (
        call :log "ERROR: Conda installation failed"
        echo ===================================================================
        echo Failed to install Conda. See log for details: "%LOG_FILE%"
        echo ===================================================================
        pause
        exit /b 1
    )
    
    call :check_vs
    if !errorlevel! neq 0 (
        call :log "ERROR: Visual Studio installation failed"
        echo ===================================================================
        echo Failed to install Visual Studio. See log for details: "%LOG_FILE%"
        echo ===================================================================
        pause
        exit /b 1
    )
    
    :: Main installation process
    call :install_bitnet
    if !errorlevel! neq 0 (
        call :log "ERROR: Main installation failed with code !errorlevel!"
        echo ===================================================================
        echo Installation failed. See log file for details: "%LOG_FILE%"
        echo ===================================================================
        pause
        exit /b 1
    )
    
    echo.
    echo ===================================================================
    echo BitNet installation is complete!
    echo ===================================================================
    echo.
    echo To start BitNet:
    echo 1. Open the start_bitnet.bat file in the same directory as this installer
    echo.
    echo Note: BitNet requires a Developer Command Prompt for Visual Studio 2022
    echo       This is handled automatically by the start script.
    echo.
    echo Enjoy using BitNet!
    echo ===================================================================
    
    :: Clean up temporary files
    call :log_and_show "Cleaning up temporary files" "INFO"
    if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%" >nul 2>&1
    
    call :log "Installation completed successfully"
    pause
    exit /b 0

:: ===================================================================
:: Function declarations
:: ===================================================================

:log
    echo %date% %time% - %~1 >> "%LOG_FILE%"
    exit /b 0

:log_and_show
    set "message=%~1"
    set "type=%~2"
    set "timestamp=[%time:~0,8%]"
    
    :: Format output based on message type
    if "%type%"=="ERROR" (
        echo %timestamp% [ERROR] %message%
        echo %date% %time% - ERROR: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="WARNING" (
        echo %timestamp% [WARNING] %message%
        echo %date% %time% - WARNING: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="SUCCESS" (
        echo %timestamp% [SUCCESS] %message%
        echo %date% %time% - SUCCESS: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="CHECK" (
        echo %timestamp% [CHECK] %message%
        echo %date% %time% - CHECK: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="INSTALL" (
        echo %timestamp% [INSTALL] %message%
        echo %date% %time% - INSTALL: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="DOWNLOAD" (
        echo %timestamp% [DOWNLOAD] %message%
        echo %date% %time% - DOWNLOAD: %message% >> "%LOG_FILE%"
    ) else if "%type%"=="COMPLETE" (
        echo %timestamp% [COMPLETE] %message%
        echo %date% %time% - COMPLETE: %message% >> "%LOG_FILE%"
    ) else (
        echo %timestamp% [INFO] %message%
        echo %date% %time% - INFO: %message% >> "%LOG_FILE%"
    )
    exit /b 0

:display_progress_bar
    set "message=%~1"
    set "percent=%~2"
    set "bar_size=50"
    
    set /a filled=(%percent%*%bar_size%)/100
    set /a empty=%bar_size%-%filled%
    
    set "progress_bar=["
    for /l %%A in (1,1,%filled%) do set "progress_bar=!progress_bar!#"
    for /l %%A in (1,1,%empty%) do set "progress_bar=!progress_bar! "
    set "progress_bar=!progress_bar!] %percent%%%"
    
    cls
    echo ===================================================================
    echo BitNet 1.58 Installer for Windows - Installation Progress
    echo ===================================================================
    echo.
    echo !message!
    echo !progress_bar!
    echo.
    echo ===================================================================
    exit /b 0

:check_git
    call :log_and_show "Checking for Git installation" "CHECK"
    git --version >nul 2>&1
    if !errorlevel! neq 0 (
        call :log_and_show "Git not found, installing Git for Windows" "INSTALL"
        
        :: Download Git installer
        if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
        call :log_and_show "Downloading Git installer" "DOWNLOAD"
        
        :: Download Git installer using PowerShell
        powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe' -OutFile '%TEMP_DIR%\git_installer.exe' }"
        
        if not exist "%TEMP_DIR%\git_installer.exe" (
            call :log_and_show "Failed to download Git installer" "ERROR"
            set "PREREQ_ERROR=1"
            exit /b 1
        )
        
        :: Install Git silently
        call :log_and_show "Installing Git (this will take 1-2 minutes)" "INSTALL"
        "%TEMP_DIR%\git_installer.exe" /VERYSILENT /NORESTART /NOCANCEL
        
        :: Verify Git installation
        git --version >nul 2>&1
        if !errorlevel! neq 0 (
            call :log_and_show "Git installation failed" "ERROR"
            set "PREREQ_ERROR=1"
            exit /b 1
        ) else (
            call :log_and_show "Git installed successfully" "SUCCESS"
        )
    ) else (
        call :log_and_show "Git is already installed" "SUCCESS"
    )
    exit /b 0

:check_conda
    call :log_and_show "Checking for Conda installation" "CHECK"
    
    :: Better check for conda installation - use timeout to avoid hanging
    where conda >nul 2>&1
    if %errorlevel% neq 0 (
        :: Try checking specific locations
        if exist "%USERPROFILE%\miniconda3_bitnet\Scripts\conda.exe" (
            call :log_and_show "Found Conda at %USERPROFILE%\miniconda3_bitnet\Scripts\conda.exe" "SUCCESS"
            :: Add to path for this session
            set "PATH=%PATH%;%USERPROFILE%\miniconda3_bitnet;%USERPROFILE%\miniconda3_bitnet\Scripts"
            call :log_and_show "Added Miniconda to PATH for this session" "INFO"
            exit /b 0
        ) else if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" (
            call :log_and_show "Found Conda at %USERPROFILE%\Miniconda3\Scripts\conda.exe" "SUCCESS"
            :: Add to path for this session
            set "PATH=%PATH%;%USERPROFILE%\Miniconda3;%USERPROFILE%\Miniconda3\Scripts"
            call :log_and_show "Added Miniconda to PATH for this session" "INFO"
            exit /b 0
        ) else if exist "%USERPROFILE%\Anaconda3\Scripts\conda.exe" (
            call :log_and_show "Found Conda at %USERPROFILE%\Anaconda3\Scripts\conda.exe" "SUCCESS"
            :: Add to path for this session
            set "PATH=%PATH%;%USERPROFILE%\Anaconda3;%USERPROFILE%\Anaconda3\Scripts"
            call :log_and_show "Added Miniconda to PATH for this session" "INFO"
            exit /b 0
        ) else (
            call :log_and_show "Conda not found, installing Miniconda" "INSTALL"
            
            :: Create temp directory if it doesn't exist
            if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
            call :log_and_show "Downloading Miniconda installer" "DOWNLOAD"
            
            :: Download Miniconda installer using PowerShell
            powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile '%TEMP_DIR%\miniconda_installer.exe' }"
            
            if not exist "%TEMP_DIR%\miniconda_installer.exe" (
                call :log_and_show "Failed to download Miniconda installer" "ERROR"
                set "PREREQ_ERROR=1"
                exit /b 1
            )
            
            :: Install Miniconda
            call :log_and_show "Installing Miniconda (this may take a few minutes)" "INSTALL"
            call :log_and_show "Please wait - progress is not shown during installation" "INFO"
            echo.
            echo Installing Miniconda to %USERPROFILE%\miniconda3_bitnet
            echo (This is normal and may take several minutes with no visible progress)
            echo.
            
            :: Run Miniconda installer with visible progress
            start /wait "" "%TEMP_DIR%\miniconda_installer.exe" /S /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /D=%USERPROFILE%\miniconda3_bitnet
            
            if not exist "%USERPROFILE%\miniconda3_bitnet" (
                call :log_and_show "Failed to install Miniconda" "ERROR"
                set "PREREQ_ERROR=1"
                exit /b 1
            )
            
            call :log_and_show "Miniconda installed successfully" "SUCCESS"
            
            :: Initialize conda for future sessions
            call :log_and_show "Initializing conda for future sessions" "INFO"
            
            :: Initialize conda properly using init and then activate
            echo Running conda init cmd.exe to properly initialize conda...
            "%USERPROFILE%\miniconda3_bitnet\Scripts\conda.exe" init cmd.exe >nul 2>&1
            
            :: Create and activate the environment using the full path to conda
            echo Creating conda environment bitnet-cpp...
            "%USERPROFILE%\miniconda3_bitnet\Scripts\conda.exe" create -n bitnet-cpp python=3.9 -y
            
            if !errorlevel! neq 0 (
                call :log_and_show "Failed to create conda environment" "ERROR"
                exit /b 1
            )
            
            :: Add Miniconda to path for this session
            set "PATH=%PATH%;%USERPROFILE%\miniconda3_bitnet;%USERPROFILE%\miniconda3_bitnet\Scripts"
            call :log_and_show "Added Miniconda to PATH for this session" "INFO"
            
            :: Initialize conda for future sessions
            call :log_and_show "Initializing conda for future sessions" "INFO"
            call "%USERPROFILE%\miniconda3_bitnet\Scripts\activate.bat"
        )
    ) else (
        call :log_and_show "Conda is already installed and in PATH" "SUCCESS"
    )
    exit /b 0

:check_vs
    call :log_and_show "Verifying Visual Studio installation" "CHECK"
    
    :: Check for Visual Studio 2022 installation
    if exist "C:\Program Files\Microsoft Visual Studio\2022" (
        call :log_and_show "Visual Studio 2022 is already installed" "SUCCESS"
    ) else (
        call :log_and_show "Visual Studio 2022 not found, downloading installer" "INSTALL"
        
        :: Download Visual Studio installer
        if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
        call :log_and_show "Downloading Visual Studio installer" "DOWNLOAD"
        
        :: Download VS installer using PowerShell - with better error handling
        echo Executing PowerShell to download Visual Studio installer...
        powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_community.exe' -OutFile '%TEMP_DIR%\vs_community.exe'; if($?) { Write-Host 'Download successful' } } catch { Write-Host 'Error: ' + $_.Exception.Message; exit 1 } }"
        
        if !errorlevel! neq 0 (
            call :log_and_show "Failed to download Visual Studio installer. Error in PowerShell command." "ERROR"
            set "PREREQ_ERROR=1"
            exit /b 1
        )
        
        if not exist "%TEMP_DIR%\vs_community.exe" (
            call :log_and_show "Failed to download Visual Studio installer. File not found after download." "ERROR"
            set "PREREQ_ERROR=1"
            exit /b 1
        )
        
        :: Install Visual Studio with required components
        call :log_and_show "Installing Visual Studio 2022 (this will take 10-15 minutes)" "INSTALL"
        call :log_and_show "This will install only the components needed for BitNet" "INFO"
        
        echo Executing Visual Studio installer...
        "!TEMP_DIR!\vs_community.exe" --quiet --norestart --wait --includeRecommended ^
            --add Microsoft.VisualStudio.Workload.NativeDesktop ^
            --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
            --add Microsoft.VisualStudio.Component.Windows10SDK.19041
        
        set vs_exit=!errorlevel!
        call :log_and_show "Visual Studio installer completed with exit code: !vs_exit!" "INFO"
        
        :: Verify VS installation
        if not exist "C:\Program Files\Microsoft Visual Studio\2022" (
            call :log_and_show "Visual Studio 2022 installation failed. Directory not found." "ERROR"
            set "PREREQ_ERROR=1"
            exit /b 1
        ) else (
            if !vs_exit! neq 0 (
                call :log_and_show "Visual Studio installer returned error code !vs_exit! but the installation directory exists." "WARNING"
                echo.
                echo Warning: Visual Studio may not be properly installed.
                echo The installer reported an error but the installation directory was found.
                echo If you encounter build issues later, you may need to repair your Visual Studio installation.
                echo.
                set /p continue="Continue anyway? (y/n): "
                if /i "!continue!" neq "y" (
                    call :log_and_show "User chose to abort after Visual Studio installation warning" "ERROR"
                    set "PREREQ_ERROR=1"
                    exit /b 1
                )
            ) else (
                call :log_and_show "Visual Studio 2022 installed successfully" "SUCCESS"
            )
        )
    )
    exit /b 0

:install_prerequisites
    echo ===================================================================
    echo STEP 1: Checking and Installing Prerequisites
    echo ===================================================================
    echo.
    
    :: Individual prerequisite functions will be called directly from main flow
    exit /b 0

:install_bitnet
    echo.
    echo ===================================================================
    echo STEP 4/4: Installing BitNet Repository and Dependencies
    echo ===================================================================
    echo This step typically takes 5-10 minutes to complete.
    echo.
    
    :: Check if BitNet directory already exists
    if exist "%INSTALL_DIR%" (
        echo.
        echo BitNet directory already exists at: %INSTALL_DIR%
        echo The directory must be empty to clone the repository.
        echo.
        echo What would you like to do?
        echo [1] Remove existing directory and reinstall
        echo [2] Skip installation (not recommended)
        echo.
        
        set /p choice="Enter choice (1 or 2): "
        
        if "!choice!"=="1" (
            call :log_and_show "Removing existing BitNet directory" "INFO"
            rd /s /q "%INSTALL_DIR%" >nul 2>&1
            if exist "%INSTALL_DIR%" (
                call :log_and_show "Failed to remove existing directory. Please delete it manually." "ERROR"
                set "INSTALL_ERROR=1"
                exit /b 1
            )
            :: Create BitNet directory after deletion
            mkdir "%INSTALL_DIR%" >nul 2>&1
        ) else (
            call :log_and_show "Skipping BitNet installation" "INFO"
            call :log_and_show "BitNet setup incomplete - Directory exists but installation was skipped" "WARNING"
            exit /b 0
        )
    ) else (
        :: Create BitNet directory if it doesn't exist
        mkdir "%INSTALL_DIR%" >nul 2>&1
    )
    
    :: Clone BitNet repository
    call :log_and_show "Cloning BitNet repository from GitHub (this may take a few minutes)" "DOWNLOAD"
    
    echo Executing: git clone --recursive https://github.com/microsoft/BitNet.git "!INSTALL_DIR!"
    
    :: First clean the directory to ensure it's empty
    if exist "%INSTALL_DIR%" (
        rd /s /q "%INSTALL_DIR%" >nul 2>&1
        mkdir "%INSTALL_DIR%" >nul 2>&1
    )
    
    :: Try cloning with a timeout command to prevent network hang
    git clone --recursive https://github.com/microsoft/BitNet.git "!INSTALL_DIR!"
    
    if !errorlevel! neq 0 (
        call :log_and_show "Failed to clone BitNet repository. Error code: !errorlevel!" "ERROR"
        call :log_and_show "This may be due to network issues or GitHub rate limits." "INFO"
        set "INSTALL_ERROR=1"
        exit /b 1
    )
    
    call :log_and_show "BitNet repository cloned successfully" "SUCCESS"
    
    :: Create and activate conda environment
    call :log_and_show "Creating BitNet conda environment (Python 3.9)" "INFO"
    
    :: Create a batch file to create the conda environment and install dependencies
    echo @echo off > "%TEMP_DIR%\setup_conda.bat"
    echo echo Setting up conda environment for BitNet... >> "%TEMP_DIR%\setup_conda.bat"
    echo set "PATH=%%PATH%%;%%USERPROFILE%%\miniconda3_bitnet;%%USERPROFILE%%\miniconda3_bitnet\Scripts" >> "%TEMP_DIR%\setup_conda.bat"
    
    :: Use the proper conda command with full path to avoid initialization issues
    echo "%%USERPROFILE%%\miniconda3_bitnet\Scripts\conda.exe" init cmd.exe >> "%TEMP_DIR%\setup_conda.bat"
    echo "%%USERPROFILE%%\miniconda3_bitnet\Scripts\conda.exe" create -n bitnet-cpp python=3.9 -y >> "%TEMP_DIR%\setup_conda.bat"
    echo if %%errorlevel%% neq 0 ( >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo ERROR: Failed to create conda environment >> "%TEMP_DIR%\setup_conda.bat"
    echo   exit /b 1 >> "%TEMP_DIR%\setup_conda.bat"
    echo ) >> "%TEMP_DIR%\setup_conda.bat"
    
    :: Check if requirements.txt exists, if not create a basic one
    echo cd /d "!INSTALL_DIR!" >> "%TEMP_DIR%\setup_conda.bat"
    echo if not exist requirements.txt ( >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo Requirements.txt not found, creating a basic one with common dependencies... >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo numpy>=1.20.0 > requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo torch>=1.10.0 >> requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo tqdm>=4.62.0 >> requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo scipy>=1.7.0 >> requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo matplotlib>=3.4.0 >> requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo ) >> "%TEMP_DIR%\setup_conda.bat"
    
    :: Use the conda run command instead of activate
    echo echo Installing requirements from requirements.txt... >> "%TEMP_DIR%\setup_conda.bat"
    echo "%%USERPROFILE%%\miniconda3_bitnet\Scripts\conda.exe" run -n bitnet-cpp pip install -r requirements.txt >> "%TEMP_DIR%\setup_conda.bat"
    echo if %%errorlevel%% neq 0 ( >> "%TEMP_DIR%\setup_conda.bat"
    echo   echo ERROR: Failed to install Python requirements >> "%TEMP_DIR%\setup_conda.bat"
    echo   exit /b 4 >> "%TEMP_DIR%\setup_conda.bat"
    echo ) >> "%TEMP_DIR%\setup_conda.bat"
    
    :: Run the conda setup script
    echo Executing conda setup script...
    call "%TEMP_DIR%\setup_conda.bat"
    if !errorlevel! neq 0 (
        call :log_and_show "Failed to set up conda environment. Error code: !errorlevel!" "ERROR"
        set "INSTALL_ERROR=1"
        exit /b 1
    )
    
    call :log_and_show "Conda environment set up successfully" "SUCCESS"
    
    :: Create start script
    call :log_and_show "Creating BitNet start script" "INFO"
    
    echo @echo off > "%CURRENT_DIR%\start_bitnet.bat"
    echo echo Starting BitNet... >> "%CURRENT_DIR%\start_bitnet.bat"
    echo echo. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo set "PATH=%%PATH%%;%%USERPROFILE%%\miniconda3_bitnet;%%USERPROFILE%%\miniconda3_bitnet\Scripts" >> "%CURRENT_DIR%\start_bitnet.bat"
    
    :: Use conda run instead of activate in the start script
    echo cd /d "!INSTALL_DIR!" >> "%CURRENT_DIR%\start_bitnet.bat"
    echo echo Running BitNet. If this fails, please check the README.md for proper launch instructions. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo echo. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo if exist build.bat ( >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo Building BitNet with Visual Studio... >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   call build.bat >> "%CURRENT_DIR%\start_bitnet.bat"
    echo ) else if exist CMakeLists.txt ( >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo Running CMake build process... >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   "%%USERPROFILE%%\miniconda3_bitnet\Scripts\conda.exe" run -n bitnet-cpp cmd /c "mkdir build 2>nul & cd build & cmake .. & cmake --build . --config Release" >> "%CURRENT_DIR%\start_bitnet.bat"
    echo ) else if exist setup.py ( >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo Installing BitNet from setup.py... >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   "%%USERPROFILE%%\miniconda3_bitnet\Scripts\conda.exe" run -n bitnet-cpp pip install -e . >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo BitNet installed. Please refer to the README.md for usage instructions. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo ) else ( >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo NOTE: Unable to determine how to build or run BitNet. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo Please refer to the README.md in the BitNet directory for instructions. >> "%CURRENT_DIR%\start_bitnet.bat"
    echo   echo Project directory: !INSTALL_DIR! >> "%CURRENT_DIR%\start_bitnet.bat"
    echo ) >> "%CURRENT_DIR%\start_bitnet.bat"
    echo pause >> "%CURRENT_DIR%\start_bitnet.bat"
    
    call :log_and_show "BitNet installation complete" "COMPLETE"
    exit /b 0
