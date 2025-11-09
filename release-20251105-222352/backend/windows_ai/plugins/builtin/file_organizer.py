"""
File Organizer Plugin

AI-powered file organization using intelligent categorization.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import shutil
import logging
import mimetypes

from windows_ai.plugins.base import ActionPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class FileOrganizerPlugin(ActionPlugin):
    """
    Organizes files into categorized folders based on file type and content.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="file_organizer",
            name="File Organizer",
            description="Organize files into categorized folders automatically",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.ACTION,
            icon="📁",
            tags=["files", "organization", "automation"]
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.category_rules = {
            # Documents
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
            # Spreadsheets
            "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
            # Presentations
            "Presentations": [".ppt", ".pptx", ".key", ".odp"],
            # Images
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            # Videos
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            # Audio
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            # Code
            "Code": [".py", ".js", ".java", ".cpp", ".c", ".h", ".html", ".css", ".ts"],
            # Archives
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            # Executables
            "Executables": [".exe", ".msi", ".dmg", ".app", ".deb", ".rpm"],
        }

    async def initialize(self) -> bool:
        """Initialize the file organizer plugin"""
        self._initialized = True
        logger.info("File Organizer plugin initialized")
        return True

    def _get_file_category(self, file_path: Path) -> str:
        """
        Determine the category for a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Category name
        """
        extension = file_path.suffix.lower()

        for category, extensions in self.category_rules.items():
            if extension in extensions:
                return category

        return "Other"

    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Organize files in a directory.

        Args:
            input_data: Path to directory or file to organize
            context: Additional context
            **kwargs: Additional parameters
                - create_folders: bool - Whether to create category folders (default: True)
                - dry_run: bool - Just show what would happen (default: False)

        Returns:
            Organization results
        """
        create_folders = kwargs.get("create_folders", True)
        dry_run = kwargs.get("dry_run", False)

        try:
            source_path = Path(input_data)

            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {source_path}",
                    "message": "Invalid path"
                }

            organized_files = []
            errors = []

            # Handle single file
            if source_path.is_file():
                files_to_organize = [source_path]
                target_dir = source_path.parent
            else:
                # Handle directory
                files_to_organize = [f for f in source_path.iterdir() if f.is_file()]
                target_dir = source_path

            for file_path in files_to_organize:
                try:
                    category = self._get_file_category(file_path)
                    category_dir = target_dir / category

                    if not dry_run and create_folders:
                        category_dir.mkdir(exist_ok=True)

                    new_path = category_dir / file_path.name

                    if not dry_run:
                        # Move the file
                        shutil.move(str(file_path), str(new_path))

                    organized_files.append({
                        "file": file_path.name,
                        "from": str(file_path),
                        "to": str(new_path),
                        "category": category
                    })

                except Exception as e:
                    logger.error(f"Error organizing {file_path}: {e}")
                    errors.append({
                        "file": str(file_path),
                        "error": str(e)
                    })

            return {
                "success": True,
                "result": {
                    "organized_count": len(organized_files),
                    "error_count": len(errors),
                    "files": organized_files,
                    "errors": errors,
                    "dry_run": dry_run
                },
                "message": f"Organized {len(organized_files)} files into {len(set(f['category'] for f in organized_files))} categories",
                "metadata": {
                    "source": str(source_path),
                    "categories_used": list(set(f["category"] for f in organized_files))
                }
            }

        except Exception as e:
            logger.error(f"File organization error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error organizing files"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "input_data": {
                    "type": "string",
                    "description": "Path to directory or file to organize"
                },
                "create_folders": {
                    "type": "boolean",
                    "description": "Whether to create category folders",
                    "default": True
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without actually moving files",
                    "default": False
                }
            },
            "required": ["input_data"]
        }
