"""
Enhanced Windows AI Context Menu Handler
Provides rich context menu integration with multiple AI actions
"""
import sys
import os
import subprocess
import json
from pathlib import Path
import requests
from typing import Optional, Dict, Any


BACKEND_URL = "http://127.0.0.1:8010"
GUI_PATH = Path(__file__).parent.parent / "apps" / "gui"


class ContextMenuHandler:
    """Enhanced context menu handler with multiple AI capabilities"""

    def __init__(self, backend_url: str = BACKEND_URL):
        self.backend_url = backend_url
        self.max_content_size = 1024 * 1024  # 1MB max for content preview

    def read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with encoding fallback"""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(self.max_content_size)
                    return content
            except (UnicodeDecodeError, IOError):
                continue
        return None

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract comprehensive file metadata"""
        path = Path(file_path)
        stat = path.stat() if path.exists() else None

        return {
            "name": path.name,
            "path": str(path.absolute()),
            "extension": path.suffix,
            "size": stat.st_size if stat else 0,
            "created": stat.st_ctime if stat else None,
            "modified": stat.st_mtime if stat else None,
            "is_directory": path.is_dir(),
            "parent": str(path.parent)
        }

    def send_to_backend(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Send data to backend with error handling"""
        try:
            response = requests.post(
                f"{self.backend_url}{endpoint}",
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # Show notification if available
            if result.get('message'):
                self.show_notification("Windows AI", result['message'])

            return True
        except requests.exceptions.ConnectionError:
            self.show_error("Cannot connect to Windows AI. Is it running?")
            return False
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            return False

    def show_notification(self, title: str, message: str):
        """Show Windows notification"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
        except:
            # Fallback to console
            print(f"[{title}] {message}")

    def show_error(self, message: str):
        """Show error notification"""
        self.show_notification("Windows AI Error", message)

    def open_gui_with_context(self, context_data: Dict[str, Any]):
        """Open GUI application with preloaded context"""
        try:
            # Store context in temp file
            context_file = Path.home() / ".windows-ai" / "context.json"
            context_file.parent.mkdir(parents=True, exist_ok=True)

            with open(context_file, 'w') as f:
                json.dump(context_data, f)

            # Launch GUI
            subprocess.Popen([
                "npm", "start"
            ], cwd=str(GUI_PATH), shell=True)

            return True
        except Exception as e:
            self.show_error(f"Failed to open GUI: {e}")
            return False

    # === Context Menu Actions ===

    def analyze_file(self, file_path: str) -> bool:
        """Analyze file with AI"""
        metadata = self.get_file_metadata(file_path)
        content = self.read_file_content(file_path)

        data = {
            "action": "analyze_file",
            "metadata": metadata,
            "content": content
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def summarize_file(self, file_path: str) -> bool:
        """Generate file summary"""
        content = self.read_file_content(file_path)

        if not content:
            self.show_error("Cannot read file content")
            return False

        data = {
            "action": "summarize",
            "file_path": file_path,
            "content": content
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def extract_info(self, file_path: str) -> bool:
        """Extract key information from file"""
        content = self.read_file_content(file_path)

        if not content:
            self.show_error("Cannot read file content")
            return False

        data = {
            "action": "extract_info",
            "file_path": file_path,
            "content": content
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def ask_about(self, path: str) -> bool:
        """Open chat with file/folder context"""
        metadata = self.get_file_metadata(path)
        content = None

        if not metadata["is_directory"]:
            content = self.read_file_content(path)

        context_data = {
            "type": "file_context",
            "metadata": metadata,
            "content": content
        }

        return self.open_gui_with_context(context_data)

    def translate_file(self, file_path: str, target_lang: str = "es") -> bool:
        """Translate file content"""
        content = self.read_file_content(file_path)

        if not content:
            self.show_error("Cannot read file content")
            return False

        data = {
            "action": "translate",
            "file_path": file_path,
            "content": content,
            "target_language": target_lang
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def generate_documentation(self, file_path: str) -> bool:
        """Generate documentation for code file"""
        content = self.read_file_content(file_path)
        metadata = self.get_file_metadata(file_path)

        if not content:
            self.show_error("Cannot read file content")
            return False

        data = {
            "action": "generate_docs",
            "file_path": file_path,
            "content": content,
            "language": metadata["extension"]
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def organize_folder(self, folder_path: str) -> bool:
        """AI-powered folder organization"""
        metadata = self.get_file_metadata(folder_path)

        if not metadata["is_directory"]:
            self.show_error("Not a directory")
            return False

        # Get file list
        path = Path(folder_path)
        files = []
        for item in path.iterdir():
            if item.is_file():
                files.append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "extension": item.suffix
                })

        data = {
            "action": "organize_folder",
            "folder_path": folder_path,
            "files": files
        }

        return self.send_to_backend("/integrations/context_menu", data)

    def batch_rename(self, folder_path: str) -> bool:
        """AI-assisted batch renaming"""
        metadata = self.get_file_metadata(folder_path)

        if not metadata["is_directory"]:
            self.show_error("Not a directory")
            return False

        data = {
            "action": "batch_rename",
            "folder_path": folder_path
        }

        return self.send_to_backend("/integrations/context_menu", data)


def main():
    """Main entry point for context menu handler"""
    if len(sys.argv) < 3:
        print("Usage: enhanced_handler.py <action> <path> [args...]")
        print("\nAvailable actions:")
        print("  analyze       - Analyze file with AI")
        print("  summarize     - Generate summary")
        print("  extract       - Extract key information")
        print("  ask           - Open chat with context")
        print("  translate     - Translate content")
        print("  document      - Generate documentation")
        print("  organize      - Organize folder")
        print("  batch_rename  - Batch rename files")
        sys.exit(1)

    action = sys.argv[1]
    path = sys.argv[2]

    if not os.path.exists(path):
        print(f"Path not found: {path}")
        sys.exit(1)

    handler = ContextMenuHandler()

    # Route to appropriate action
    actions = {
        "analyze": handler.analyze_file,
        "summarize": handler.summarize_file,
        "extract": handler.extract_info,
        "ask": handler.ask_about,
        "translate": handler.translate_file,
        "document": handler.generate_documentation,
        "organize": handler.organize_folder,
        "batch_rename": handler.batch_rename
    }

    action_func = actions.get(action)
    if not action_func:
        print(f"Unknown action: {action}")
        sys.exit(1)

    # Execute action
    success = action_func(path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
