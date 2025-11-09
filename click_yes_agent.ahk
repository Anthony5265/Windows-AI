; AutoHotkey Script - Auto-clicks "Yes" on Copilot approval dialogs
; Monitors for approval prompts and automatically approves them

#NoEnv
#Persistent
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

global LogFile := "C:\Users\antho\logs\unified_sessions\ahk_autoapprove_" . A_Now . ".log"
global CheckInterval := 500  ; Check every 500ms
global IsEnabled := true

; Log function
LogMessage(msg) {
    FormatTime, timestamp, , yyyy-MM-dd HH:mm:ss
    FileAppend, %timestamp% - %msg%`n, %LogFile%
}

LogMessage("Auto-approve agent started via AutoHotkey")

; Main monitoring loop
SetTimer, CheckForPrompts, %CheckInterval%
return

CheckForPrompts:
    if (!IsEnabled)
        return
    
    ; Look for windows with approval text
    WinGet, windows, List
    Loop, %windows% {
        WinGet, winTitle, ProcessName, % "ahk_id " windows%A_Index%
        WinGetText, winText, % "ahk_id " windows%A_Index%
        
        ; Check if window contains approval prompt keywords
        if (InStr(winText, "Do you want to") || InStr(winText, "Approve") || InStr(winText, "Continue")) {
            ; Look for Yes/OK/Continue button
            ControlClick, Button1, % "ahk_id " windows%A_Index%
            LogMessage("Auto-approved prompt in window: " . winTitle)
            
            ; Also try sending 'y' key + Enter multiple times
            ControlSend, , y, % "ahk_id " windows%A_Index%
            Sleep, 50
            ControlSend, , {Enter}, % "ahk_id " windows%A_Index%
            Sleep, 50
            ControlSend, , {Enter}, % "ahk_id " windows%A_Index%
        }
    }
return

; Hotkey to toggle on/off: Ctrl+Alt+A
^!a::
    IsEnabled := !IsEnabled
    if (IsEnabled) {
        LogMessage("Auto-approve ENABLED")
        TrayTip, Auto-Approve Agent, Enabled, 2, 1
    } else {
        LogMessage("Auto-approve DISABLED")
        TrayTip, Auto-Approve Agent, Disabled, 2, 2
    }
return

; Hotkey to exit: Ctrl+Alt+X
^!x::
    LogMessage("Auto-approve agent stopped by user")
    ExitApp
return
