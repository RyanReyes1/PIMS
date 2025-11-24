# PIMS (Patient Information Management System) - Startup Script
# This script sets up and runs the project with all necessary services

param(
    [switch]$NoTailwind = $false,
    [switch]$NoPython = $false
)

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

Write-Info "================================"
Write-Info "PIMS - Startup Script"
Write-Info "================================"

# Get script directory
$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Write-Info "Project directory: $scriptDir"

# Check if we're in the correct directory
if (-not (Test-Path "$scriptDir\app.py")) {
    Write-Error "Error: app.py not found in $scriptDir"
    exit 1
}

# Install Python dependencies
if (-not $NoPython) {
    Write-Info "`nInstalling Python dependencies..."
    
    # Check if already in a virtual environment
    $inVenv = $env:VIRTUAL_ENV -ne $null
    if ($inVenv) {
        Write-Info "Already running inside a virtual environment"
    } else {
        if (-not (Test-Path "$scriptDir\venv")) {
            Write-Info "Creating Python virtual environment..."
            python -m venv "$scriptDir\venv"
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to create virtual environment"
                exit 1
            }
        }
        
        # Activate virtual environment
        Write-Info "Activating virtual environment..."
        $activateScript = "$scriptDir\venv\Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            & $activateScript
        } else {
            Write-Error "Virtual environment activation script not found at $activateScript"
            exit 1
        }
    }
    
    Write-Info "Installing packages from requirements.txt..."
    pip install -r "$scriptDir\requirements.txt" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Python dependencies"
        exit 1
    }
    Write-Success "Python dependencies installed"
} else {
    Write-Info "Skipping Python setup"
}

# Install Node dependencies and start Tailwind CSS watcher
if (-not $NoTailwind) {
    Write-Info "`nInstalling Node dependencies..."
    if (-not (Test-Path "$scriptDir\node_modules")) {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install Node dependencies"
            exit 1
        }
    }
    Write-Success "Node dependencies installed"
    
    Write-Info "Starting Tailwind CSS watcher in background..."
    $tailwindJob = Start-Job -ScriptBlock {
        param($scriptDir)
        Set-Location $scriptDir
        npx tailwindcss -i ./static/css/input.css -o ./static/css/style.css --watch
    } -ArgumentList $scriptDir
    Write-Success "Tailwind CSS watcher started (Job ID: $($tailwindJob.Id))"
    Write-Info "Tailwind CSS will auto-compile when you save CSS changes`n"
} else {
    Write-Info "Skipping Tailwind CSS watcher"
}

# Start Flask development server
Write-Info "Starting Flask development server..."
Write-Info "Access the application at: http://localhost:5000"
Write-Info "`nPress Ctrl+C to stop the server`n"

flask run

# Cleanup
if (-not $NoTailwind) {
    Write-Info "`nStopping Tailwind CSS watcher..."
    Get-Job | Stop-Job
    Remove-Job -State Completed
}
