param()

Describe 'install.ps1' {
    BeforeAll {
        $root = Resolve-Path (Join-Path $PSScriptRoot '..' '..')
        $scriptPath = Join-Path $root.Path 'install/install.ps1'
    }

    It 'logs missing command errors to transcript' {
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'python' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'nssm.exe' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'mkcert' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'New-NetFirewallRule' }
        Mock Invoke-WebRequest { param($Uri,$OutFile) New-Item -Path $OutFile -ItemType File -Force | Out-Null }
        Mock Expand-Archive {
            param($Path,$DestinationPath)
            New-Item -ItemType Directory -Path (Join-Path $DestinationPath 'nssm-2.24/win64') -Force | Out-Null
            New-Item -Path (Join-Path $DestinationPath 'nssm-2.24/win64/nssm.exe') -ItemType File -Force | Out-Null
        }
        Mock Start-Process {}

        & $scriptPath -CacheDir $TestDrive > $null 2>&1

        $log = Get-Content (Join-Path $TestDrive 'install.log') -Raw
        $log | Should -Match "Required command 'nssm.exe' not found"
        $log | Should -Match "Required command 'mkcert' not found"
        $log | Should -Match "Required command 'python' not found"
        $log | Should -Match "Required command 'New-NetFirewallRule' not found"
    }

    It 'downloads missing tools when absent' {
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'python' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'nssm.exe' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'mkcert' }
        Mock Get-Command { $null } -ParameterFilter { $Name -eq 'New-NetFirewallRule' }
        Mock Invoke-WebRequest { param($Uri,$OutFile) New-Item -Path $OutFile -ItemType File -Force | Out-Null }
        Mock Expand-Archive {
            param($Path,$DestinationPath)
            New-Item -ItemType Directory -Path (Join-Path $DestinationPath 'nssm-2.24/win64') -Force | Out-Null
            New-Item -Path (Join-Path $DestinationPath 'nssm-2.24/win64/nssm.exe') -ItemType File -Force | Out-Null
        }
        Mock Start-Process {}

        & $scriptPath -CacheDir $TestDrive > $null 2>&1

        Test-Path (Join-Path $TestDrive 'mkcert.exe') | Should -BeTrue
        Test-Path (Join-Path $TestDrive 'nssm-2.24/win64/nssm.exe') | Should -BeTrue
        Assert-MockCalled Invoke-WebRequest -ParameterFilter { $Uri -match 'nssm' } -Times 1
        Assert-MockCalled Invoke-WebRequest -ParameterFilter { $Uri -match 'mkcert' } -Times 1
    }
}

