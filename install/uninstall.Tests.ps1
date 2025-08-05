Describe "uninstall.ps1" {
    BeforeEach {
        $scriptPath = Join-Path $PSScriptRoot 'uninstall.ps1'
        $LogPath = Join-Path $PSScriptRoot 'uninstall.log'
        if (Test-Path $LogPath) { Remove-Item $LogPath }
    }

    It "logs when service removal fails" {
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'python' } -MockWith { $null }
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'nssm.exe' } -MockWith { [pscustomobject]@{} }
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'Remove-NetFirewallRule' } -MockWith { $null }
        function nssm { $global:LASTEXITCODE = 1 }
        function Get-Service { param($Name) return @{ Name = $Name } }

        . $scriptPath

        Get-Content $LogPath | Should -Match 'Failed to remove service WindowsAIService'
        Remove-Item function:nssm
        Remove-Item function:Get-Service
    }

    It "logs when firewall rule removal fails" {
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'python' } -MockWith { $null }
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'nssm.exe' } -MockWith { $null }
        Mock -CommandName Get-Command -ParameterFilter { $Name -eq 'Remove-NetFirewallRule' } -MockWith { [pscustomobject]@{} }
        function Remove-NetFirewallRule { $global:LASTEXITCODE = 1 }
        function Get-NetFirewallRule { param($DisplayName) return @{ Name = $DisplayName } }

        . $scriptPath

        Get-Content $LogPath | Should -Match "Failed to remove firewall rule 'Windows AI'"
        Remove-Item function:Remove-NetFirewallRule
        Remove-Item function:Get-NetFirewallRule
    }
}

