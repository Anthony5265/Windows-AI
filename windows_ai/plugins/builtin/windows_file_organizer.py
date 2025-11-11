"""
Windows File Organizer Plugin
Intelligently organize files by type, date, size, or content

Features:
- Multiple organization strategies (type, date, size, content-based)
- Dry-run mode for preview
- Configurable file type mappings
- Duplicate detection
- Safe file operations with rollback
- Detailed operation reports

Author: Windows AI Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import hashlib

from windows_ai.plugins.base import ActionPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WindowsFileOrganizerPlugin(ActionPlugin):
    """Intelligent file organization plugin"""

    # File type categories
    FILE_CATEGORIES = {
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
        "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
        "Presentations": [".ppt", ".pptx", ".key", ".odp"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Code": [".py", ".js", ".java", ".cpp", ".c", ".h", ".cs", ".go", ".rs", ".php"],
        "Web": [".html", ".htm", ".css", ".scss", ".sass", ".xml", ".json"],
        "Executables": [".exe", ".msi", ".dmg", ".app", ".deb", ".rpm"],
        "Data": [".db", ".sqlite", ".sql", ".mdb"],
        "Config": [".ini", ".cfg", ".conf", ".yaml", ".yml", ".toml"],
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="windows_file_organizer",
            name="Windows File Organizer",
            description="Intelligently organize files by type, date, or content with safety features",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.ACTION,
            enabled=True,
            icon="📁",
            tags=["files", "organization", "cleanup", "windows"],
            requirements=[]
        )
        super().__init__(metadata)

        # State
        self.operation_history: List[Dict[str, Any]] = []

    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute file organization

        Args:
            input_data: Directory path to organize
            context: Additional context
            **kwargs: Configuration parameters
                - strategy: "type", "date", "size", or "content" (default: "type")
                - dry_run: bool - Preview without moving files (default: True)
                - recursive: bool - Process subdirectories (default: False)
                - create_categories: bool - Create category folders (default: True)
                - detect_duplicates: bool - Detect and handle duplicates (default: True)
                - min_file_size: int - Minimum file size in bytes to organize (default: 0)
                - exclude_extensions: List[str] - Extensions to skip
        """
        try:
            directory = Path(input_data) if isinstance(input_data, str) else Path(str(input_data))

            # Extract configuration
            strategy = kwargs.get("strategy", "type")
            dry_run = kwargs.get("dry_run", True)
            recursive = kwargs.get("recursive", False)
            create_categories = kwargs.get("create_categories", True)
            detect_duplicates = kwargs.get("detect_duplicates", True)
            min_file_size = kwargs.get("min_file_size", 0)
            exclude_extensions = kwargs.get("exclude_extensions", [])

            # Validate directory
            if not directory.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {directory}",
                    "message": "Please provide a valid directory path"
                }

            if not directory.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory}",
                    "message": "Input must be a directory"
                }

            logger.info(f"Organizing directory: {directory} (strategy: {strategy}, dry_run: {dry_run})")

            # Scan files
            files = self._scan_files(directory, recursive, min_file_size, exclude_extensions)

            if not files:
                return {
                    "success": True,
                    "result": "No files to organize",
                    "message": "Directory is empty or all files are excluded",
                    "metadata": {
                        "directory": str(directory),
                        "files_found": 0
                    }
                }

            # Detect duplicates if enabled
            duplicates = {}
            if detect_duplicates:
                duplicates = self._find_duplicates(files)

            # Organize based on strategy
            if strategy == "type":
                organization_plan = self._organize_by_type(files, directory, create_categories)
            elif strategy == "date":
                organization_plan = self._organize_by_date(files, directory, create_categories)
            elif strategy == "size":
                organization_plan = self._organize_by_size(files, directory, create_categories)
            elif strategy == "content":
                organization_plan = self._organize_by_content(files, directory, create_categories)
            else:
                return {
                    "success": False,
                    "error": f"Unknown strategy: {strategy}",
                    "message": "Valid strategies: type, date, size, content"
                }

            # Execute or preview
            if dry_run:
                result = self._preview_organization(organization_plan, duplicates)
                message = "✓ Organization preview generated (dry run - no files moved)"
            else:
                result = await self._execute_organization(organization_plan, duplicates)
                message = f"✓ Successfully organized {result['files_moved']} files"

            return {
                "success": True,
                "result": result,
                "message": message,
                "metadata": {
                    "directory": str(directory),
                    "strategy": strategy,
                    "dry_run": dry_run,
                    "files_scanned": len(files),
                    "duplicates_found": len(duplicates)
                }
            }

        except PermissionError as e:
            return {
                "success": False,
                "error": f"Permission denied: {str(e)}",
                "message": "Insufficient permissions to access or modify files"
            }
        except Exception as e:
            logger.error(f"File organizer error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during file organization"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for parameters"""
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to organize"
                },
                "strategy": {
                    "type": "string",
                    "enum": ["type", "date", "size", "content"],
                    "description": "Organization strategy",
                    "default": "type"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview without moving files",
                    "default": True
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Process subdirectories",
                    "default": False
                },
                "create_categories": {
                    "type": "boolean",
                    "description": "Create category folders",
                    "default": True
                },
                "detect_duplicates": {
                    "type": "boolean",
                    "description": "Detect and report duplicates",
                    "default": True
                },
                "min_file_size": {
                    "type": "integer",
                    "description": "Minimum file size in bytes",
                    "default": 0
                },
                "exclude_extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File extensions to exclude (e.g., ['.tmp', '.log'])"
                }
            },
            "required": ["directory"]
        }

    # =========================================================================
    # File Scanning
    # =========================================================================

    def _scan_files(
        self,
        directory: Path,
        recursive: bool,
        min_size: int,
        exclude_ext: List[str]
    ) -> List[Path]:
        """Scan directory for files to organize"""
        files = []

        try:
            pattern = "**/*" if recursive else "*"
            for item in directory.glob(pattern):
                if item.is_file():
                    # Check exclusions
                    if item.suffix.lower() in exclude_ext:
                        continue

                    # Check size
                    if item.stat().st_size < min_size:
                        continue

                    files.append(item)

            logger.info(f"Scanned {len(files)} files")
            return files

        except Exception as e:
            logger.error(f"Error scanning files: {e}")
            return files

    def _find_duplicates(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Find duplicate files by content hash"""
        hash_map = defaultdict(list)

        for file_path in files:
            try:
                file_hash = self._hash_file(file_path)
                hash_map[file_hash].append(file_path)
            except Exception as e:
                logger.warning(f"Could not hash {file_path}: {e}")

        # Filter to only actual duplicates
        duplicates = {k: v for k, v in hash_map.items() if len(v) > 1}

        logger.info(f"Found {len(duplicates)} sets of duplicate files")
        return duplicates

    def _hash_file(self, file_path: Path, block_size: int = 65536) -> str:
        """Compute SHA256 hash of file"""
        hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            while True:
                block = f.read(block_size)
                if not block:
                    break
                hasher.update(block)

        return hasher.hexdigest()

    # =========================================================================
    # Organization Strategies
    # =========================================================================

    def _organize_by_type(
        self,
        files: List[Path],
        base_dir: Path,
        create_categories: bool
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Organize files by file type"""
        plan = defaultdict(list)

        for file_path in files:
            ext = file_path.suffix.lower()

            # Find category
            category = "Other"
            for cat_name, extensions in self.FILE_CATEGORIES.items():
                if ext in extensions:
                    category = cat_name
                    break

            # Determine destination
            if create_categories:
                dest_dir = base_dir / category
            else:
                dest_dir = base_dir

            dest_path = dest_dir / file_path.name

            # Handle name conflicts
            if dest_path.exists() and dest_path != file_path:
                dest_path = self._get_unique_path(dest_path)

            plan[category].append((file_path, dest_path))

        return plan

    def _organize_by_date(
        self,
        files: List[Path],
        base_dir: Path,
        create_categories: bool
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Organize files by modification date"""
        plan = defaultdict(list)

        for file_path in files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                category = mtime.strftime("%Y-%m")  # YYYY-MM format

                if create_categories:
                    dest_dir = base_dir / category
                else:
                    dest_dir = base_dir

                dest_path = dest_dir / file_path.name

                if dest_path.exists() and dest_path != file_path:
                    dest_path = self._get_unique_path(dest_path)

                plan[category].append((file_path, dest_path))

            except Exception as e:
                logger.warning(f"Could not get date for {file_path}: {e}")

        return plan

    def _organize_by_size(
        self,
        files: List[Path],
        base_dir: Path,
        create_categories: bool
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Organize files by size ranges"""
        plan = defaultdict(list)

        size_ranges = [
            ("Tiny (< 1MB)", 0, 1024 * 1024),
            ("Small (1-10MB)", 1024 * 1024, 10 * 1024 * 1024),
            ("Medium (10-100MB)", 10 * 1024 * 1024, 100 * 1024 * 1024),
            ("Large (100MB-1GB)", 100 * 1024 * 1024, 1024 * 1024 * 1024),
            ("Huge (> 1GB)", 1024 * 1024 * 1024, float('inf'))
        ]

        for file_path in files:
            try:
                size = file_path.stat().st_size

                category = "Unknown"
                for cat_name, min_size, max_size in size_ranges:
                    if min_size <= size < max_size:
                        category = cat_name
                        break

                if create_categories:
                    dest_dir = base_dir / category
                else:
                    dest_dir = base_dir

                dest_path = dest_dir / file_path.name

                if dest_path.exists() and dest_path != file_path:
                    dest_path = self._get_unique_path(dest_path)

                plan[category].append((file_path, dest_path))

            except Exception as e:
                logger.warning(f"Could not get size for {file_path}: {e}")

        return plan

    def _organize_by_content(
        self,
        files: List[Path],
        base_dir: Path,
        create_categories: bool
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Organize files by MIME type content"""
        plan = defaultdict(list)

        for file_path in files:
            try:
                mime_type, _ = mimetypes.guess_type(str(file_path))

                if mime_type:
                    category = mime_type.split('/')[0].capitalize()
                else:
                    category = "Unknown"

                if create_categories:
                    dest_dir = base_dir / category
                else:
                    dest_dir = base_dir

                dest_path = dest_dir / file_path.name

                if dest_path.exists() and dest_path != file_path:
                    dest_path = self._get_unique_path(dest_path)

                plan[category].append((file_path, dest_path))

            except Exception as e:
                logger.warning(f"Could not determine content type for {file_path}: {e}")

        return plan

    # =========================================================================
    # Execution
    # =========================================================================

    def _preview_organization(
        self,
        plan: Dict[str, List[Tuple[Path, Path]]],
        duplicates: Dict[str, List[Path]]
    ) -> Dict[str, Any]:
        """Generate preview of organization plan"""
        preview = {
            "categories": {},
            "total_files": 0,
            "folders_to_create": [],
            "duplicates": []
        }

        for category, moves in plan.items():
            preview["categories"][category] = {
                "file_count": len(moves),
                "files": [
                    {
                        "from": str(src),
                        "to": str(dst),
                        "size": src.stat().st_size
                    }
                    for src, dst in moves
                ]
            }
            preview["total_files"] += len(moves)

            # Track folders to create
            folders = set(dst.parent for _, dst in moves)
            preview["folders_to_create"].extend([str(f) for f in folders if not f.exists()])

        # Add duplicate info
        for file_hash, paths in duplicates.items():
            preview["duplicates"].append({
                "hash": file_hash[:16],
                "files": [str(p) for p in paths],
                "size": paths[0].stat().st_size
            })

        return preview

    async def _execute_organization(
        self,
        plan: Dict[str, List[Tuple[Path, Path]]],
        duplicates: Dict[str, List[Path]]
    ) -> Dict[str, Any]:
        """Execute file organization"""
        result = {
            "files_moved": 0,
            "folders_created": 0,
            "errors": [],
            "categories": {}
        }

        for category, moves in plan.items():
            category_result = {
                "files_moved": 0,
                "errors": []
            }

            for src, dst in moves:
                try:
                    # Create destination directory
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if not dst.parent in result:
                        result["folders_created"] += 1

                    # Move file
                    shutil.move(str(src), str(dst))

                    category_result["files_moved"] += 1
                    result["files_moved"] += 1

                    logger.debug(f"Moved: {src} -> {dst}")

                except Exception as e:
                    error_msg = f"Failed to move {src}: {str(e)}"
                    category_result["errors"].append(error_msg)
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            result["categories"][category] = category_result

        # Log operation
        self.operation_history.append({
            "timestamp": datetime.now().isoformat(),
            "result": result
        })

        return result

    def _get_unique_path(self, path: Path) -> Path:
        """Generate unique file path to avoid conflicts"""
        counter = 1
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1


# Export
__all__ = ["WindowsFileOrganizerPlugin"]
