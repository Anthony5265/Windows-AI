param()

Describe 'install.ps1' {
    BeforeAll {
        $root = Resolve-Path (Join-Path $PSScriptRoot '..' '..')
        $scriptPath = Join-Path $root.Path 'install/install.ps1'
    }

    It 'creates a transcript log' {
        Mock Invoke-WebRequest {}
        Mock Expand-Archive {}
        Mock Start-Process {}

        & $scriptPath -CacheDir $TestDrive

        Test-Path (Join-Path $TestDrive 'install.log') | Should -BeTrue
    }

    It 'downloads missing tools when absent' {
        Mock Invoke-WebRequest {}
        Mock Expand-Archive {}
        Mock Start-Process {}

        & $scriptPath -CacheDir $TestDrive > $null 2>&1

        Assert-MockCalled Invoke-WebRequest -ParameterFilter { $Uri -match 'nssm' } -Times 1
        Assert-MockCalled Invoke-WebRequest -ParameterFilter { $Uri -match 'mkcert' } -Times 1
    }
}

