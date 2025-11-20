"""
Windows AI Context Menu Handler
Handles file/folder selections from Windows Explorer context menu
"""
import sys
import os
import requests
import json
from pathlib import Path


BACKEND_URL = "http://127.0.0.1:8010"


def read_file_content(file_path):
    """Read file content (text files only)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return None


def get_file_info(file_path):
    """Get file information"""
    path = Path(file_path)
    return {
        "name": path.name,
        "size": path.stat().st_size if path.exists() else 0,
        "type": path.suffix,
        "path": str(path.absolute())
    }


def analyze_file(file_path):
    """Send file to Windows AI for analysis"""
    file_info = get_file_info(file_path)

    # Read content for text files
    content = read_file_content(file_path)

    data = {
        "action": "analyze_file",
        "file_info": file_info,
        "content": content if content else None
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/integrations/context_menu",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print("Analysis sent to Windows AI")
        print(f"Response: {result.get('message', 'Success')}")
        return True
    except Exception as e:
        print(f"Error communicating with Windows AI: {e}")
        print("Make sure Windows AI is running")
        return False


def summarize_file(file_path):
    """Summarize file content"""
    content = read_file_content(file_path)

    if not content:
        print("Cannot read file content")
        return False

    data = {
        "action": "summarize_file",
        "file_path": file_path,
        "content": content
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/integrations/context_menu",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print("Summarization request sent to Windows AI")
        print(f"Response: {result.get('message', 'Success')}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def ask_about(path):
    """Open chat with context about this file/folder"""
    is_folder = os.path.isdir(path)

    data = {
        "action": "ask_about",
        "path": path,
        "is_folder": is_folder
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/integrations/context_menu",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print("Context loaded in Windows AI")
        print(f"Response: {result.get('message', 'Success')}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: handler.py <action> <file_path>")
        print("Actions: analyze, summarize, ask")
        sys.exit(1)

    action = sys.argv[1]
    file_path = sys.argv[2]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    if action == "analyze":
        success = analyze_file(file_path)
    elif action == "summarize":
        success = summarize_file(file_path)
    elif action == "ask":
        success = ask_about(file_path)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
