<#!
.SYNOPSIS
Registers context menu entries and global hotkeys for AI prototypes.

.DESCRIPTION
Adds "Open AI File Explorer" and "Open AI Terminal" entries to the
Windows Explorer background context menu and registers Ctrl+Alt+E and
Ctrl+Alt+T as global hotkeys to launch the prototypes.
#>

$python = (Get-Command python).Path
$base = "HKCU:\Software\Classes\Directory\Background\shell"

# Context menu for AI File Explorer
$explorerKey = Join-Path $base "AIFileExplorer"
New-Item -Path $explorerKey -Force | Out-Null
Set-ItemProperty -Path $explorerKey -Name "Icon" -Value $python
Set-ItemProperty -Path $explorerKey -Name "(default)" -Value "Open AI File Explorer"
$explorerCmd = Join-Path $explorerKey "command"
New-Item -Path $explorerCmd -Force | Out-Null
Set-ItemProperty -Path $explorerCmd -Name "(default)" -Value "`"$python`" -m ui.os_integrations.file_explorer"

# Context menu for AI Terminal
$terminalKey = Join-Path $base "AITerminal"
New-Item -Path $terminalKey -Force | Out-Null
Set-ItemProperty -Path $terminalKey -Name "Icon" -Value $python
Set-ItemProperty -Path $terminalKey -Name "(default)" -Value "Open AI Terminal"
$terminalCmd = Join-Path $terminalKey "command"
New-Item -Path $terminalCmd -Force | Out-Null
Set-ItemProperty -Path $terminalCmd -Name "(default)" -Value "`"$python`" -m ui.os_integrations.terminal"

# Register global hotkeys using a small WinForms app
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class HotKeyForm : Form {
    [DllImport("user32.dll")]
    public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
    private const int MOD_ALT = 0x1;
    private const int MOD_CONTROL = 0x2;
    private const int WM_HOTKEY = 0x0312;

    protected override void WndProc(ref Message m) {
        base.WndProc(ref m);
        if (m.Msg == WM_HOTKEY) {
            if (m.WParam.ToInt32() == 1)
                System.Diagnostics.Process.Start("python", "-m ui.os_integrations.file_explorer");
            if (m.WParam.ToInt32() == 2)
                System.Diagnostics.Process.Start("python", "-m ui.os_integrations.terminal");
        }
    }

    public HotKeyForm() {
        RegisterHotKey(this.Handle, 1, MOD_CONTROL | MOD_ALT, (uint)Keys.E);
        RegisterHotKey(this.Handle, 2, MOD_CONTROL | MOD_ALT, (uint)Keys.T);
    }
}
"@ -ReferencedAssemblies System.Windows.Forms

[void][System.Windows.Forms.Application]::Run([HotKeyForm]::new())
