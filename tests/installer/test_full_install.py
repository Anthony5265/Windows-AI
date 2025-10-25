import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="PowerShell not available")
def test_installer_downloads_prerequisites(tmp_path):
    script = Path(__file__).resolve().parents[2] / "install" / "install.ps1"
    log = tmp_path / "log.txt"

    ps = f"""
$ErrorActionPreference='Stop'
$Log = '{log}'
function Invoke-WebRequest {{ param($Uri,$OutFile) Add-Content -Path $Log -Value $Uri; New-Item -ItemType File -Path $OutFile -Force | Out-Null }}
function Expand-Archive {{ param($Path,$DestinationPath,[switch]$Force) Add-Content -Path $Log -Value "EXPAND:$Path"; New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null; New-Item -ItemType File -Path (Join-Path $DestinationPath 'nssm.exe') -Force | Out-Null }}
function Start-Process {{ param($FilePath,$ArgumentList,[switch]$Wait) Add-Content -Path $Log -Value "START:$FilePath" }}
function nssm {{ param($Action,$Name,$Exe,$Args) Add-Content -Path $Log -Value "NSSM:$Action" }}
function mkcert {{ param($Arg) Add-Content -Path $Log -Value "MKCERT:$Arg" }}
function node {{ param($A,$B,$C) Add-Content -Path $Log -Value "NODE:$A" }}
$env:PATH=''
$env:ProgramData='{tmp_path}'
$env:TEMP='{tmp_path}'
. '{script}'
"""

    subprocess.run(["pwsh", "-NoLogo", "-NoProfile", "-Command", ps], check=True)
    lines = log.read_text().splitlines()
    assert any("nssm.cc" in line for line in lines)
    assert any("mkcert" in line for line in lines)
    assert any("nodejs.org" in line for line in lines)
