[CmdletBinding()]
param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 5500,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot "backend"
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort/index.html"

function Import-DotEnv {
    $envPath = Join-Path $BackendRoot ".env"
    if (-not (Test-Path $envPath)) {
        return
    }

    foreach ($line in (Get-Content -LiteralPath $envPath -Encoding UTF8)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) {
            continue
        }

        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Find-Python {
    $venvPython = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        return $python.Source
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $py) {
        return $py.Source
    }

    throw "Python was not found. Install Python 3.10+ or create backend\.venv."
}

function Stop-ChildProcess {
    param([System.Diagnostics.Process]$Process)

    if ($null -ne $Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    }
}

$python = Find-Python
$backendProcess = $null
$frontendProcess = $null
Import-DotEnv

try {
    Write-Host "Starting FastAPI backend on $BackendUrl ..."
    $backendProcess = Start-Process -FilePath $python `
        -WorkingDirectory $BackendRoot `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort", "--reload") `
        -PassThru

    Write-Host "Starting static frontend on http://127.0.0.1:$FrontendPort ..."
    $frontendProcess = Start-Process -FilePath $python `
        -WorkingDirectory $FrontendRoot `
        -ArgumentList @("-m", "http.server", "$FrontendPort", "--bind", "127.0.0.1") `
        -PassThru

    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        if ($backendProcess.HasExited) {
            throw "Backend stopped during startup. Check Firebase credentials and backend dependencies."
        }

        try {
            $health = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 2
            if ($health.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            # The backend may need a few seconds to import Firebase and load the app.
        }

        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "Backend did not become ready at $BackendUrl/health."
    }

    Write-Host "Backend and frontend are running."
    Write-Host "Open $FrontendUrl"
    Write-Host "Press Ctrl+C to stop both processes."

    if (-not $NoBrowser) {
        Start-Process $FrontendUrl | Out-Null
    }

    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-ChildProcess $frontendProcess
    Stop-ChildProcess $backendProcess
}