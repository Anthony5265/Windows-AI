"""
Shell Automation Plugin for Windows AI
Provides Windows Shell automation and command execution
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class ShellAutomationPlugin(IntegrationPlugin):
    """
    Windows Shell automation plugin
    
    Provides comprehensive shell operations including:
    - Command execution
    - Shell namespace operations
    - File/folder dialogs
    - Shell verbs and context menus
    - Environment variables
    - Path operations
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows-shell-automation",
            name="Windows Shell Automation",
            description="Shell automation and command execution",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "shell", "automation", "command", "explorer"],
            requirements=[]
        )
        super().__init__(metadata)
        
        self.actions = {
            # Command Execution
            "run_command": {
                "description": "Run a shell command",
                "script": """
$command = '{command}'
$workingDir = '{working_directory}'
$timeout = {timeout}
if ($timeout -eq 0) {{ $timeout = 30 }}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'cmd.exe'
$psi.Arguments = "/c $command"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
if ($workingDir) {{ $psi.WorkingDirectory = $workingDir }}

$process = [System.Diagnostics.Process]::Start($psi)
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit($timeout * 1000) | Out-Null

@{{
    exit_code = $process.ExitCode
    stdout = $stdout
    stderr = $stderr
    success = $process.ExitCode -eq 0
}} | ConvertTo-Json
"""
            },
            "run_powershell_command": {
                "description": "Run a PowerShell command",
                "script": """
$command = '{command}'
$result = Invoke-Expression $command
@{{ result = $result; success = $true }} | ConvertTo-Json -Depth 5
"""
            },
            "run_elevated": {
                "description": "Run a command with elevated privileges",
                "script": """
$command = '{command}'
$arguments = '{arguments}'
Start-Process -FilePath $command -ArgumentList $arguments -Verb RunAs -Wait
@{{ success = $true; message = 'Elevated command executed' }} | ConvertTo-Json
"""
            },
            "run_hidden": {
                "description": "Run a command in hidden window",
                "script": """
$command = '{command}'
$arguments = '{arguments}'
Start-Process -FilePath $command -ArgumentList $arguments -WindowStyle Hidden -Wait
@{{ success = $true; message = 'Hidden command executed' }} | ConvertTo-Json
"""
            },
            
            # Environment Variables
            "get_env_variable": {
                "description": "Get an environment variable",
                "script": """
$name = '{name}'
$scope = '{scope}'
if (-not $scope) {{ $scope = 'Process' }}

$value = [Environment]::GetEnvironmentVariable($name, $scope)
@{{
    name = $name
    value = $value
    scope = $scope
    exists = $null -ne $value
}} | ConvertTo-Json
"""
            },
            "set_env_variable": {
                "description": "Set an environment variable",
                "script": """
$name = '{name}'
$value = '{value}'
$scope = '{scope}'
if (-not $scope) {{ $scope = 'User' }}

[Environment]::SetEnvironmentVariable($name, $value, $scope)
@{{
    success = $true
    name = $name
    value = $value
    scope = $scope
}} | ConvertTo-Json
"""
            },
            "remove_env_variable": {
                "description": "Remove an environment variable",
                "script": """
$name = '{name}'
$scope = '{scope}'
if (-not $scope) {{ $scope = 'User' }}

[Environment]::SetEnvironmentVariable($name, $null, $scope)
@{{ success = $true; name = $name; scope = $scope }} | ConvertTo-Json
"""
            },
            "list_env_variables": {
                "description": "List all environment variables",
                "script": """
$scope = '{scope}'
if (-not $scope) {{ $scope = 'Process' }}

$vars = [Environment]::GetEnvironmentVariables($scope)
$result = @{{}}
foreach ($key in $vars.Keys) {{
    $result[$key] = $vars[$key]
}}
@{{ scope = $scope; variables = $result; count = $vars.Count }} | ConvertTo-Json -Depth 3
"""
            },
            "expand_env_string": {
                "description": "Expand environment variables in a string",
                "script": """
$text = '{text}'
$expanded = [Environment]::ExpandEnvironmentVariables($text)
@{{ original = $text; expanded = $expanded }} | ConvertTo-Json
"""
            },
            
            # Path Operations
            "add_to_path": {
                "description": "Add a directory to PATH",
                "script": """
$directory = '{directory}'
$scope = '{scope}'
if (-not $scope) {{ $scope = 'User' }}

$currentPath = [Environment]::GetEnvironmentVariable('PATH', $scope)
if ($currentPath -notlike "*$directory*") {{
    $newPath = "$currentPath;$directory"
    [Environment]::SetEnvironmentVariable('PATH', $newPath, $scope)
    @{{ success = $true; message = "Added to $scope PATH"; directory = $directory }} | ConvertTo-Json
}} else {{
    @{{ success = $true; message = 'Directory already in PATH'; directory = $directory }} | ConvertTo-Json
}}
"""
            },
            "remove_from_path": {
                "description": "Remove a directory from PATH",
                "script": """
$directory = '{directory}'
$scope = '{scope}'
if (-not $scope) {{ $scope = 'User' }}

$currentPath = [Environment]::GetEnvironmentVariable('PATH', $scope)
$paths = $currentPath -split ';' | Where-Object {{ $_ -ne $directory -and $_ -ne '' }}
$newPath = $paths -join ';'
[Environment]::SetEnvironmentVariable('PATH', $newPath, $scope)
@{{ success = $true; message = "Removed from $scope PATH"; directory = $directory }} | ConvertTo-Json
"""
            },
            "get_path_entries": {
                "description": "Get all PATH entries",
                "script": """
$scope = '{scope}'
if (-not $scope) {{ $scope = 'Process' }}

$path = [Environment]::GetEnvironmentVariable('PATH', $scope)
$entries = $path -split ';' | Where-Object {{ $_ -ne '' }} | ForEach-Object {{
    @{{
        path = $_
        exists = Test-Path $_
    }}
}}
@{{ scope = $scope; entries = @($entries); count = @($entries).Count }} | ConvertTo-Json -Depth 3
"""
            },
            
            # Shell Namespace
            "get_special_folder": {
                "description": "Get a special folder path",
                "script": """
$folderName = '{folder_name}'
$path = [Environment]::GetFolderPath($folderName)
@{{ folder = $folderName; path = $path; exists = Test-Path $path }} | ConvertTo-Json
"""
            },
            "list_special_folders": {
                "description": "List all special folder paths",
                "script": """
$folders = [Enum]::GetNames([Environment+SpecialFolder]) | ForEach-Object {{
    $path = [Environment]::GetFolderPath($_)
    @{{
        name = $_
        path = $path
        exists = if ($path) {{ Test-Path $path }} else {{ $false }}
    }}
}} | Where-Object {{ $_.path -ne '' }}
@{{ folders = @($folders); count = @($folders).Count }} | ConvertTo-Json -Depth 3
"""
            },
            "open_folder": {
                "description": "Open a folder in Explorer",
                "script": """
$path = '{path}'
if (Test-Path $path) {{
    Start-Process explorer.exe -ArgumentList $path
    @{{ success = $true; path = $path }} | ConvertTo-Json
}} else {{
    @{{ success = $false; error = "Path not found: $path" }} | ConvertTo-Json
}}
"""
            },
            "select_file_in_explorer": {
                "description": "Open Explorer and select a file",
                "script": """
$filePath = '{file_path}'
if (Test-Path $filePath) {{
    Start-Process explorer.exe -ArgumentList "/select,`"$filePath`""
    @{{ success = $true; file = $filePath }} | ConvertTo-Json
}} else {{
    @{{ success = $false; error = "File not found: $filePath" }} | ConvertTo-Json
}}
"""
            },
            
            # Shell Verbs
            "get_shell_verbs": {
                "description": "Get available shell verbs for a file",
                "script": """
$filePath = '{file_path}'
if (Test-Path $filePath) {{
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.Namespace((Split-Path $filePath -Parent))
    $item = $folder.ParseName((Split-Path $filePath -Leaf))
    $verbs = $item.Verbs() | ForEach-Object {{ $_.Name }}
    @{{ file = $filePath; verbs = @($verbs) }} | ConvertTo-Json -Depth 2
}} else {{
    @{{ error = "File not found: $filePath" }} | ConvertTo-Json
}}
"""
            },
            "invoke_shell_verb": {
                "description": "Invoke a shell verb on a file",
                "script": """
$filePath = '{file_path}'
$verb = '{verb}'

if (Test-Path $filePath) {{
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.Namespace((Split-Path $filePath -Parent))
    $item = $folder.ParseName((Split-Path $filePath -Leaf))
    $item.InvokeVerb($verb)
    @{{ success = $true; file = $filePath; verb = $verb }} | ConvertTo-Json
}} else {{
    @{{ success = $false; error = "File not found: $filePath" }} | ConvertTo-Json
}}
"""
            },
            "open_with": {
                "description": "Open a file with a specific application",
                "script": """
$filePath = '{file_path}'
$application = '{application}'

if (Test-Path $filePath) {{
    Start-Process -FilePath $application -ArgumentList "`"$filePath`""
    @{{ success = $true; file = $filePath; application = $application }} | ConvertTo-Json
}} else {{
    @{{ success = $false; error = "File not found: $filePath" }} | ConvertTo-Json
}}
"""
            },
            "open_properties": {
                "description": "Open file/folder properties dialog",
                "script": """
$path = '{path}'
if (Test-Path $path) {{
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.Namespace((Split-Path $path -Parent))
    $item = $folder.ParseName((Split-Path $path -Leaf))
    $item.InvokeVerb('properties')
    @{{ success = $true; path = $path }} | ConvertTo-Json
}} else {{
    @{{ success = $false; error = "Path not found: $path" }} | ConvertTo-Json
}}
"""
            },
            
            # File Dialogs
            "show_open_dialog": {
                "description": "Show file open dialog",
                "script": """
$filter = '{filter}'
$title = '{title}'
$initialDir = '{initial_directory}'

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
if ($filter) {{ $dialog.Filter = $filter }}
if ($title) {{ $dialog.Title = $title }}
if ($initialDir -and (Test-Path $initialDir)) {{ $dialog.InitialDirectory = $initialDir }}

$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    @{{ success = $true; selected = $dialog.FileName }} | ConvertTo-Json
}} else {{
    @{{ success = $false; cancelled = $true }} | ConvertTo-Json
}}
"""
            },
            "show_save_dialog": {
                "description": "Show file save dialog",
                "script": """
$filter = '{filter}'
$title = '{title}'
$initialDir = '{initial_directory}'
$defaultName = '{default_name}'

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.SaveFileDialog
if ($filter) {{ $dialog.Filter = $filter }}
if ($title) {{ $dialog.Title = $title }}
if ($defaultName) {{ $dialog.FileName = $defaultName }}
if ($initialDir -and (Test-Path $initialDir)) {{ $dialog.InitialDirectory = $initialDir }}

$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    @{{ success = $true; selected = $dialog.FileName }} | ConvertTo-Json
}} else {{
    @{{ success = $false; cancelled = $true }} | ConvertTo-Json
}}
"""
            },
            "show_folder_dialog": {
                "description": "Show folder browser dialog",
                "script": """
$description = '{description}'
$selectedPath = '{selected_path}'

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
if ($description) {{ $dialog.Description = $description }}
if ($selectedPath -and (Test-Path $selectedPath)) {{ $dialog.SelectedPath = $selectedPath }}

$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    @{{ success = $true; selected = $dialog.SelectedPath }} | ConvertTo-Json
}} else {{
    @{{ success = $false; cancelled = $true }} | ConvertTo-Json
}}
"""
            },
            
            # Input Dialogs
            "show_input_box": {
                "description": "Show input dialog box",
                "script": """
$prompt = '{prompt}'
$title = '{title}'
$defaultValue = '{default_value}'

Add-Type -AssemblyName Microsoft.VisualBasic
$result = [Microsoft.VisualBasic.Interaction]::InputBox($prompt, $title, $defaultValue)
if ($result) {{
    @{{ success = $true; value = $result }} | ConvertTo-Json
}} else {{
    @{{ success = $false; cancelled = $true }} | ConvertTo-Json
}}
"""
            },
            "show_message_box": {
                "description": "Show message box",
                "script": """
$message = '{message}'
$title = '{title}'
$buttons = '{buttons}'
$icon = '{icon}'

Add-Type -AssemblyName System.Windows.Forms
$buttonType = [System.Windows.Forms.MessageBoxButtons]::$buttons
$iconType = [System.Windows.Forms.MessageBoxIcon]::$icon

$result = [System.Windows.Forms.MessageBox]::Show($message, $title, $buttonType, $iconType)
@{{ result = $result.ToString() }} | ConvertTo-Json
"""
            },
            
            # Shell Extensions
            "refresh_shell": {
                "description": "Refresh Windows Shell (update icons, associations)",
                "script": """
$code = @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SHChangeNotify(int wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
$type = Add-Type -MemberDefinition $code -Name 'SHChange' -Namespace 'Win32' -PassThru
$type::SHChangeNotify(0x8000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
@{{ success = $true; message = 'Shell refreshed' }} | ConvertTo-Json
"""
            },
            "restart_explorer": {
                "description": "Restart Windows Explorer",
                "script": """
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process explorer.exe
@{{ success = $true; message = 'Explorer restarted' }} | ConvertTo-Json
"""
            },
            
            # Command History
            "get_command_history": {
                "description": "Get PowerShell command history",
                "script": """
$maxCount = {max_count}
if ($maxCount -eq 0) {{ $maxCount = 50 }}

$history = Get-History -Count $maxCount | ForEach-Object {{
    @{{
        id = $_.Id
        command = $_.CommandLine
        start_time = $_.StartExecutionTime.ToString('yyyy-MM-dd HH:mm:ss')
        end_time = $_.EndExecutionTime.ToString('yyyy-MM-dd HH:mm:ss')
        status = $_.ExecutionStatus.ToString()
    }}
}}
@{{ history = @($history); count = @($history).Count }} | ConvertTo-Json -Depth 3
"""
            },
            "clear_command_history": {
                "description": "Clear PowerShell command history",
                "script": """
Clear-History
@{{ success = $true; message = 'Command history cleared' }} | ConvertTo-Json
"""
            },
            
            # Aliases
            "get_aliases": {
                "description": "Get PowerShell aliases",
                "script": """
$pattern = '{pattern}'
$aliases = Get-Alias | Where-Object {{ 
    if ($pattern) {{ $_.Name -like $pattern -or $_.Definition -like $pattern }}
    else {{ $true }}
}} | ForEach-Object {{
    @{{
        name = $_.Name
        definition = $_.Definition
        description = $_.Description
    }}
}}
@{{ aliases = @($aliases); count = @($aliases).Count }} | ConvertTo-Json -Depth 3
"""
            },
            "create_alias": {
                "description": "Create a PowerShell alias",
                "script": """
$name = '{name}'
$value = '{value}'
$description = '{description}'

Set-Alias -Name $name -Value $value -Description $description -Scope Global
@{{ success = $true; name = $name; value = $value }} | ConvertTo-Json
"""
            },
            "remove_alias": {
                "description": "Remove a PowerShell alias",
                "script": """
$name = '{name}'
Remove-Item -Path "Alias:\\$name" -Force -ErrorAction SilentlyContinue
@{{ success = $true; name = $name }} | ConvertTo-Json
"""
            },
            
            # Shell Information
            "get_shell_info": {
                "description": "Get shell and system information",
                "script": """
@{{
    powershell_version = $PSVersionTable.PSVersion.ToString()
    powershell_edition = $PSVersionTable.PSEdition
    os_version = [Environment]::OSVersion.VersionString
    machine_name = [Environment]::MachineName
    user_name = [Environment]::UserName
    user_domain = [Environment]::UserDomainName
    is_64bit_os = [Environment]::Is64BitOperatingSystem
    is_64bit_process = [Environment]::Is64BitProcess
    processor_count = [Environment]::ProcessorCount
    system_directory = [Environment]::SystemDirectory
    current_directory = [Environment]::CurrentDirectory
}} | ConvertTo-Json
"""
            },
            
            # Clipboard Operations
            "get_clipboard": {
                "description": "Get clipboard content",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
$content = [System.Windows.Forms.Clipboard]::GetText()
@{{ content = $content; has_content = ($content.Length -gt 0) }} | ConvertTo-Json
"""
            },
            "set_clipboard": {
                "description": "Set clipboard content",
                "script": """
$text = '{text}'
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::SetText($text)
@{{ success = $true; length = $text.Length }} | ConvertTo-Json
"""
            },
            "clear_clipboard": {
                "description": "Clear clipboard",
                "script": """
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::Clear()
@{{ success = $true; message = 'Clipboard cleared' }} | ConvertTo-Json
"""
            },
            
            # Script Execution
            "run_script_file": {
                "description": "Run a PowerShell script file",
                "script": """
$scriptPath = '{script_path}'
$arguments = '{arguments}'

if (Test-Path $scriptPath) {{
    $result = & $scriptPath $arguments
    @{{ success = $true; output = $result }} | ConvertTo-Json -Depth 5
}} else {{
    @{{ success = $false; error = "Script not found: $scriptPath" }} | ConvertTo-Json
}}
"""
            },
            "create_script_file": {
                "description": "Create a PowerShell script file",
                "script": """
$scriptPath = '{script_path}'
$content = @'
{script_content}
'@

$content | Out-File -FilePath $scriptPath -Encoding UTF8
@{{ success = $true; path = $scriptPath }} | ConvertTo-Json
"""
            },
            
            # System Utilities
            "get_system_uptime": {
                "description": "Get system uptime",
                "script": """
$os = Get-CimInstance Win32_OperatingSystem
$uptime = (Get-Date) - $os.LastBootUpTime
@{{
    days = $uptime.Days
    hours = $uptime.Hours
    minutes = $uptime.Minutes
    seconds = $uptime.Seconds
    total_hours = [math]::Round($uptime.TotalHours, 2)
    last_boot = $os.LastBootUpTime.ToString('yyyy-MM-dd HH:mm:ss')
}} | ConvertTo-Json
"""
            },
            "shutdown_system": {
                "description": "Shutdown the system",
                "script": """
$delay = {delay}
$force = '{force}'
$restart = '{restart}'

if ($delay -eq 0) {{ $delay = 0 }}
$args = "/s /t $delay"
if ($force -eq 'true') {{ $args += " /f" }}
if ($restart -eq 'true') {{ $args = $args.Replace('/s', '/r') }}

Start-Process shutdown.exe -ArgumentList $args
@{{ success = $true; action = if ($restart -eq 'true') {{ 'restart' }} else {{ 'shutdown' }}; delay = $delay }} | ConvertTo-Json
"""
            },
            "lock_workstation": {
                "description": "Lock the workstation",
                "script": """
$code = @'
[DllImport("user32.dll", SetLastError = true)]
public static extern bool LockWorkStation();
'@
$type = Add-Type -MemberDefinition $code -Name 'User32' -Namespace 'Win32' -PassThru
$type::LockWorkStation()
@{{ success = $true; message = 'Workstation locked' }} | ConvertTo-Json
"""
            }
        }
    

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the service"""
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a shell automation action"""
        action = kwargs.get("action", "get_shell_info")
        
        if action not in self.actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Available: {list(self.actions.keys())}"
            }
        
        action_info = self.actions[action]
        script = action_info["script"]
        
        # Replace parameters in script
        for key, value in kwargs.items():
            if key != "action":
                script = script.replace(f"{{{key}}}", str(value) if value else "")
        
        try:
            result = await self._run_powershell(script)
            return {
                "status": "success",
                "action": action,
                "description": action_info["description"],
                "result": result
            }
        except Exception as e:
            logger.error(f"Shell automation action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }
    
    async def _run_powershell(self, script: str) -> str:
        """Execute PowerShell script"""
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(stderr.decode() if stderr else "PowerShell execution failed")
        
        return stdout.decode().strip()


plugin = ShellAutomationPlugin()
