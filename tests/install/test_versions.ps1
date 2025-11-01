Describe "Installer version checks" {
    BeforeAll {
        . "$PSScriptRoot/../../install/install.ps1"
    }

    Context "Get-ToolVersion" {
        It "extracts version numbers from command output" {
            function fakecmd { param([string]$arg) return 'tool 1.2.3' }
            (Get-ToolVersion -Command fakecmd -Arguments 'version') | Should -Be ([Version]'1.2.3')
        }
    }

    Context "Require-MinVersion" {
        It "passes when version meets minimum" {
            Mock Get-ToolVersion { [Version]'2.0' }
            { Require-MinVersion -Name 'tool' -Command 'tool' -Minimum ([Version]'1.0') -Arguments 'version' } | Should -Not -Throw
        }

        It "throws when version is below minimum" {
            Mock Get-ToolVersion { [Version]'1.0' }
            { Require-MinVersion -Name 'tool' -Command 'tool' -Minimum ([Version]'2.0') -Arguments 'version' } | Should -Throw
        }
    }
}

