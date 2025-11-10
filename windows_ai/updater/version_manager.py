"""
Version Management for Windows AI Auto-Update System

Handles version parsing, comparison, and validation following semantic versioning.
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class VersionType(Enum):
    """Version type classification"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"


@dataclass
class Version:
    """
    Semantic version representation

    Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    Example: 1.2.3-beta.1+build.123
    """
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        """String representation"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __eq__(self, other: object) -> bool:
        """Equality comparison"""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other: object) -> bool:
        """Less than comparison"""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major.minor.patch
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

        # Handle prerelease versions
        # No prerelease > has prerelease (1.0.0 > 1.0.0-beta)
        if self.prerelease is None and other.prerelease is not None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True

        # Both have prerelease - compare lexicographically
        if self.prerelease is not None and other.prerelease is not None:
            return self._compare_prerelease(self.prerelease, other.prerelease) < 0

        return False

    def __le__(self, other: object) -> bool:
        """Less than or equal comparison"""
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        """Greater than comparison"""
        if not isinstance(other, Version):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        """Greater than or equal comparison"""
        return not self < other

    @staticmethod
    def _compare_prerelease(a: str, b: str) -> int:
        """
        Compare prerelease versions
        Returns: -1 if a < b, 0 if a == b, 1 if a > b
        """
        # Split by dots
        a_parts = a.split('.')
        b_parts = b.split('.')

        for i in range(max(len(a_parts), len(b_parts))):
            # If one version has fewer parts, it's considered less
            if i >= len(a_parts):
                return -1
            if i >= len(b_parts):
                return 1

            a_part = a_parts[i]
            b_part = b_parts[i]

            # Try to compare as numbers
            try:
                a_num = int(a_part)
                b_num = int(b_part)
                if a_num != b_num:
                    return -1 if a_num < b_num else 1
            except ValueError:
                # Compare as strings if not both numbers
                if a_part != b_part:
                    return -1 if a_part < b_part else 1

        return 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build,
            "version_string": str(self)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Version":
        """Create from dictionary"""
        return cls(
            major=data["major"],
            minor=data["minor"],
            patch=data["patch"],
            prerelease=data.get("prerelease"),
            build=data.get("build")
        )


class VersionManager:
    """
    Manages version parsing, comparison, and validation
    """

    # Semantic versioning regex
    SEMVER_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )

    @classmethod
    def parse(cls, version_string: str) -> Version:
        """
        Parse version string into Version object

        Args:
            version_string: Version string (e.g., "1.2.3", "1.0.0-beta.1")

        Returns:
            Version object

        Raises:
            ValueError: If version string is invalid
        """
        # Remove 'v' prefix if present
        if version_string.startswith('v'):
            version_string = version_string[1:]

        match = cls.SEMVER_PATTERN.match(version_string)
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")

        return Version(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=match.group('prerelease'),
            build=match.group('build')
        )

    @classmethod
    def is_valid(cls, version_string: str) -> bool:
        """
        Check if version string is valid

        Args:
            version_string: Version string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            cls.parse(version_string)
            return True
        except ValueError:
            return False

    @classmethod
    def compare(cls, version1: str, version2: str) -> int:
        """
        Compare two version strings

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2

        Raises:
            ValueError: If either version string is invalid
        """
        v1 = cls.parse(version1)
        v2 = cls.parse(version2)

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0

    @classmethod
    def is_newer(cls, version: str, base_version: str) -> bool:
        """
        Check if version is newer than base_version

        Args:
            version: Version to check
            base_version: Base version to compare against

        Returns:
            True if version > base_version
        """
        return cls.compare(version, base_version) > 0

    @classmethod
    def is_compatible(cls, version: str, required_version: str) -> bool:
        """
        Check if version is compatible with required version

        Compatible means:
        - Same major version
        - Minor version >= required minor version

        Args:
            version: Version to check
            required_version: Required version

        Returns:
            True if compatible
        """
        v = cls.parse(version)
        req = cls.parse(required_version)

        # Different major version = incompatible
        if v.major != req.major:
            return False

        # Same major, check minor
        if v.minor < req.minor:
            return False

        # If same major and minor, check patch
        if v.minor == req.minor and v.patch < req.patch:
            return False

        return True

    @classmethod
    def get_update_type(cls, current: str, new: str) -> VersionType:
        """
        Determine update type between two versions

        Args:
            current: Current version
            new: New version

        Returns:
            VersionType (MAJOR, MINOR, PATCH, or PRERELEASE)
        """
        curr = cls.parse(current)
        new_ver = cls.parse(new)

        if new_ver.major > curr.major:
            return VersionType.MAJOR
        elif new_ver.minor > curr.minor:
            return VersionType.MINOR
        elif new_ver.patch > curr.patch:
            return VersionType.PATCH
        else:
            return VersionType.PRERELEASE

    @classmethod
    def increment_version(
        cls,
        version: str,
        update_type: VersionType,
        prerelease: Optional[str] = None
    ) -> str:
        """
        Increment version based on update type

        Args:
            version: Current version
            update_type: Type of update (MAJOR, MINOR, PATCH)
            prerelease: Optional prerelease identifier

        Returns:
            New version string
        """
        v = cls.parse(version)

        if update_type == VersionType.MAJOR:
            v.major += 1
            v.minor = 0
            v.patch = 0
        elif update_type == VersionType.MINOR:
            v.minor += 1
            v.patch = 0
        elif update_type == VersionType.PATCH:
            v.patch += 1

        v.prerelease = prerelease
        v.build = None

        return str(v)

    @classmethod
    def filter_versions(
        cls,
        versions: list[str],
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        include_prerelease: bool = False
    ) -> list[str]:
        """
        Filter list of versions based on criteria

        Args:
            versions: List of version strings
            min_version: Minimum version (inclusive)
            max_version: Maximum version (inclusive)
            include_prerelease: Include prerelease versions

        Returns:
            Filtered and sorted list of versions
        """
        filtered = []

        for version in versions:
            try:
                v = cls.parse(version)

                # Skip prerelease if not included
                if not include_prerelease and v.prerelease:
                    continue

                # Check min version
                if min_version and cls.parse(min_version) > v:
                    continue

                # Check max version
                if max_version and cls.parse(max_version) < v:
                    continue

                filtered.append(version)

            except ValueError:
                # Skip invalid versions
                continue

        # Sort versions
        filtered.sort(key=lambda x: cls.parse(x))

        return filtered

    @classmethod
    def get_latest_version(
        cls,
        versions: list[str],
        include_prerelease: bool = False
    ) -> Optional[str]:
        """
        Get latest version from list

        Args:
            versions: List of version strings
            include_prerelease: Include prerelease versions

        Returns:
            Latest version string or None if list is empty
        """
        filtered = cls.filter_versions(
            versions,
            include_prerelease=include_prerelease
        )

        return filtered[-1] if filtered else None
