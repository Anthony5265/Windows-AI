"""
File System Operations Module
Advanced file system operations including Windows-specific features
"""
from typing import Dict, Any, List, Optional
import logging
import os
import shutil
import platform
import pathlib

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32file
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
        logger.warning("pywin32 not available for advanced features")
else:
    WIN32_AVAILABLE = False


class FileOperations:
    """Production file system operations"""

    def __init__(self):
        self.is_windows = IS_WINDOWS
        self.win32_available = WIN32_AVAILABLE

    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed file/directory information"""
        try:
            path_obj = pathlib.Path(path)

            if not path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Path not found: {path}"
                }

            stat_info = path_obj.stat()

            info = {
                "status": "success",
                "path": str(path_obj.absolute()),
                "name": path_obj.name,
                "is_file": path_obj.is_file(),
                "is_dir": path_obj.is_dir(),
                "is_symlink": path_obj.is_symlink(),
                "size": stat_info.st_size,
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime
            }

            # Windows-specific attributes
            if self.is_windows and self.win32_available:
                try:
                    attrs = win32api.GetFileAttributes(str(path_obj))
                    info["attributes"] = {
                        "hidden": bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN),
                        "readonly": bool(attrs & win32con.FILE_ATTRIBUTE_READONLY),
                        "system": bool(attrs & win32con.FILE_ATTRIBUTE_SYSTEM),
                        "archive": bool(attrs & win32con.FILE_ATTRIBUTE_ARCHIVE),
                        "compressed": bool(attrs & win32con.FILE_ATTRIBUTE_COMPRESSED),
                        "encrypted": bool(attrs & win32con.FILE_ATTRIBUTE_ENCRYPTED)
                    }
                except Exception as e:
                    info["attributes_error"] = str(e)

            return info

        except Exception as e:
            logger.error(f"Get file info error: {e}")
            return {"status": "error", "message": str(e)}

    def set_file_attributes(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Set Windows file attributes

        Args:
            path: File path
            hidden: Set hidden attribute
            readonly: Set readonly attribute
            system: Set system attribute
            archive: Set archive attribute

        Returns:
            Dict with operation result
        """
        if not self.is_windows or not self.win32_available:
            return {
                "status": "error",
                "message": "Windows file attributes not available"
            }

        try:
            # Get current attributes
            current_attrs = win32api.GetFileAttributes(path)
            new_attrs = current_attrs

            # Modify attributes based on kwargs
            if "hidden" in kwargs:
                if kwargs["hidden"]:
                    new_attrs |= win32con.FILE_ATTRIBUTE_HIDDEN
                else:
                    new_attrs &= ~win32con.FILE_ATTRIBUTE_HIDDEN

            if "readonly" in kwargs:
                if kwargs["readonly"]:
                    new_attrs |= win32con.FILE_ATTRIBUTE_READONLY
                else:
                    new_attrs &= ~win32con.FILE_ATTRIBUTE_READONLY

            if "system" in kwargs:
                if kwargs["system"]:
                    new_attrs |= win32con.FILE_ATTRIBUTE_SYSTEM
                else:
                    new_attrs &= ~win32con.FILE_ATTRIBUTE_SYSTEM

            if "archive" in kwargs:
                if kwargs["archive"]:
                    new_attrs |= win32con.FILE_ATTRIBUTE_ARCHIVE
                else:
                    new_attrs &= ~win32con.FILE_ATTRIBUTE_ARCHIVE

            # Set new attributes
            win32api.SetFileAttributes(path, new_attrs)

            return {
                "status": "success",
                "message": "File attributes updated",
                "path": path
            }

        except Exception as e:
            logger.error(f"Set file attributes error: {e}")
            return {"status": "error", "message": str(e)}

    def list_directory(self, path: str, pattern: str = "*",
                      recursive: bool = False) -> Dict[str, Any]:
        """
        List directory contents

        Args:
            path: Directory path
            pattern: File pattern (e.g., "*.txt", "**/*.py")
            recursive: Recursively list subdirectories

        Returns:
            Dict with file list
        """
        try:
            path_obj = pathlib.Path(path)

            if not path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {path}"
                }

            if not path_obj.is_dir():
                return {
                    "status": "error",
                    "message": f"Not a directory: {path}"
                }

            # Get files
            if recursive:
                files = list(path_obj.rglob(pattern))
            else:
                files = list(path_obj.glob(pattern))

            entries = []
            for file_path in files:
                stat_info = file_path.stat()
                entries.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "is_file": file_path.is_file(),
                    "is_dir": file_path.is_dir(),
                    "size": stat_info.st_size,
                    "modified": stat_info.st_mtime
                })

            return {
                "status": "success",
                "directory": str(path_obj.absolute()),
                "pattern": pattern,
                "recursive": recursive,
                "entries": entries,
                "count": len(entries)
            }

        except Exception as e:
            logger.error(f"List directory error: {e}")
            return {"status": "error", "message": str(e)}

    def copy_file(self, source: str, destination: str,
                 overwrite: bool = False) -> Dict[str, Any]:
        """
        Copy file

        Args:
            source: Source file path
            destination: Destination path
            overwrite: Overwrite if destination exists

        Returns:
            Dict with operation result
        """
        try:
            source_path = pathlib.Path(source)
            dest_path = pathlib.Path(destination)

            if not source_path.exists():
                return {
                    "status": "error",
                    "message": f"Source not found: {source}"
                }

            if dest_path.exists() and not overwrite:
                return {
                    "status": "error",
                    "message": f"Destination exists: {destination}"
                }

            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, destination)

            return {
                "status": "success",
                "message": "File copied",
                "source": str(source_path.absolute()),
                "destination": str(dest_path.absolute()),
                "size": dest_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Copy file error: {e}")
            return {"status": "error", "message": str(e)}

    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move/rename file

        Args:
            source: Source file path
            destination: Destination path

        Returns:
            Dict with operation result
        """
        try:
            source_path = pathlib.Path(source)
            dest_path = pathlib.Path(destination)

            if not source_path.exists():
                return {
                    "status": "error",
                    "message": f"Source not found: {source}"
                }

            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(source, destination)

            return {
                "status": "success",
                "message": "File moved",
                "source": str(source_path.absolute()),
                "destination": str(dest_path.absolute())
            }

        except Exception as e:
            logger.error(f"Move file error: {e}")
            return {"status": "error", "message": str(e)}

    def delete_file(self, path: str, permanent: bool = False) -> Dict[str, Any]:
        """
        Delete file or directory

        Args:
            path: Path to delete
            permanent: Permanently delete (skip recycle bin on Windows)

        Returns:
            Dict with operation result
        """
        try:
            path_obj = pathlib.Path(path)

            if not path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Path not found: {path}"
                }

            # Use Windows recycle bin if available and not permanent
            if self.is_windows and not permanent:
                try:
                    from send2trash import send2trash
                    send2trash(str(path_obj))
                    return {
                        "status": "success",
                        "message": "Moved to recycle bin",
                        "path": str(path_obj.absolute())
                    }
                except ImportError:
                    logger.warning("send2trash not available, using permanent delete")

            # Permanent delete
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)

            return {
                "status": "success",
                "message": "Deleted permanently",
                "path": str(path_obj.absolute())
            }

        except Exception as e:
            logger.error(f"Delete file error: {e}")
            return {"status": "error", "message": str(e)}

    def create_directory(self, path: str, parents: bool = True) -> Dict[str, Any]:
        """
        Create directory

        Args:
            path: Directory path
            parents: Create parent directories if needed

        Returns:
            Dict with operation result
        """
        try:
            path_obj = pathlib.Path(path)

            if path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Directory already exists: {path}"
                }

            path_obj.mkdir(parents=parents, exist_ok=False)

            return {
                "status": "success",
                "message": "Directory created",
                "path": str(path_obj.absolute())
            }

        except Exception as e:
            logger.error(f"Create directory error: {e}")
            return {"status": "error", "message": str(e)}

    def search_files(self, directory: str, pattern: str = "*",
                    content_search: str = None, max_results: int = 100) -> Dict[str, Any]:
        """
        Search for files

        Args:
            directory: Directory to search in
            pattern: File name pattern
            content_search: Text to search for in file contents
            max_results: Maximum results to return

        Returns:
            Dict with search results
        """
        try:
            path_obj = pathlib.Path(directory)

            if not path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {directory}"
                }

            # Search by filename
            matches = []
            for file_path in path_obj.rglob(pattern):
                if len(matches) >= max_results:
                    break

                # Content search if specified
                if content_search and file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content_search.lower() in content.lower():
                                matches.append({
                                    "path": str(file_path),
                                    "name": file_path.name,
                                    "size": file_path.stat().st_size,
                                    "modified": file_path.stat().st_mtime,
                                    "content_match": True
                                })
                    except Exception:
                        pass  # Skip files that can't be read
                elif not content_search:
                    matches.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "is_file": file_path.is_file(),
                        "size": file_path.stat().st_size if file_path.is_file() else None,
                        "modified": file_path.stat().st_mtime
                    })

            return {
                "status": "success",
                "directory": str(path_obj.absolute()),
                "pattern": pattern,
                "content_search": content_search,
                "matches": matches,
                "count": len(matches),
                "truncated": len(matches) >= max_results
            }

        except Exception as e:
            logger.error(f"Search files error: {e}")
            return {"status": "error", "message": str(e)}

    def get_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Get disk usage statistics"""
        try:
            usage = shutil.disk_usage(path)

            return {
                "status": "success",
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": (usage.used / usage.total * 100) if usage.total > 0 else 0
            }

        except Exception as e:
            logger.error(f"Get disk usage error: {e}")
            return {"status": "error", "message": str(e)}
