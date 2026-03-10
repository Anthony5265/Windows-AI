"""
Tests for the optimization module (profiling and tuning).
"""

import pytest
from optimization.profiling import profile_hardware
from optimization.tuning import Tuner, PROFILES, apply, revert


# ---------------------------------------------------------------------------
# Profiling tests
# ---------------------------------------------------------------------------

class TestProfileHardware:
    """Tests for profile_hardware()."""

    def test_profile_returns_dict(self):
        """profile_hardware() should return a dictionary."""
        result = profile_hardware()
        assert isinstance(result, dict)

    def test_profile_contains_required_keys(self):
        """Result must contain cpu, memory, disk, gpu, os, python keys."""
        result = profile_hardware()
        for key in ("cpu", "memory", "disk", "gpu", "os", "python"):
            assert key in result, f"Missing key: {key}"

    def test_cpu_profile_structure(self):
        """CPU profile should have expected fields."""
        result = profile_hardware()
        cpu = result["cpu"]
        assert isinstance(cpu, dict)
        assert "model" in cpu
        assert "physical_cores" in cpu
        assert "logical_cores" in cpu
        assert "frequency_mhz" in cpu
        assert "architecture" in cpu
        # Cores should be positive integers
        assert cpu["logical_cores"] >= 1
        assert cpu["physical_cores"] >= 1

    def test_memory_profile_structure(self):
        """Memory profile should have expected fields."""
        result = profile_hardware()
        memory = result["memory"]
        assert isinstance(memory, dict)
        assert "total_gb" in memory
        assert "available_gb" in memory
        assert "percent_used" in memory

    def test_disk_profile_structure(self):
        """Disk profile should have expected fields."""
        result = profile_hardware()
        disk = result["disk"]
        assert isinstance(disk, dict)
        assert "total_gb" in disk
        assert "free_gb" in disk
        assert "percent_used" in disk

    def test_gpu_profile_is_list(self):
        """GPU profile should be a list (empty if no GPU detected)."""
        result = profile_hardware()
        assert isinstance(result["gpu"], list)

    def test_os_profile_structure(self):
        """OS profile should have expected fields."""
        result = profile_hardware()
        os_info = result["os"]
        assert isinstance(os_info, dict)
        assert "system" in os_info
        assert "release" in os_info

    def test_python_profile_structure(self):
        """Python profile should have version and executable path."""
        result = profile_hardware()
        py_info = result["python"]
        assert isinstance(py_info, dict)
        assert "version" in py_info
        assert "executable" in py_info

    def test_profile_does_not_raise(self):
        """profile_hardware() must never raise even without optional deps."""
        # Should gracefully degrade
        result = profile_hardware()
        assert result is not None


# ---------------------------------------------------------------------------
# Tuning tests (extended from test_tuning.py)
# ---------------------------------------------------------------------------

class TestTuner:
    """Tests for the Tuner class."""

    def test_default_profile_is_balanced(self):
        """New tuner should start with balanced profile."""
        tuner = Tuner()
        assert tuner.current_settings == PROFILES["balanced"]

    def test_apply_performance_profile(self):
        """Apply performance profile changes settings."""
        tuner = Tuner()
        result = tuner.apply("performance")
        assert result == PROFILES["performance"]
        assert tuner.current_settings == PROFILES["performance"]

    def test_apply_eco_profile(self):
        """Apply eco profile changes settings."""
        tuner = Tuner()
        result = tuner.apply("eco")
        assert result == PROFILES["eco"]
        assert tuner.current_settings == PROFILES["eco"]

    def test_apply_invalid_profile_raises(self):
        """Applying an unknown profile should raise ValueError."""
        tuner = Tuner()
        with pytest.raises(ValueError, match="Unknown profile"):
            tuner.apply("nonexistent")

    def test_revert_restores_previous(self):
        """Revert should restore the previous settings."""
        tuner = Tuner()
        original = tuner.current_settings.copy()
        tuner.apply("performance")
        tuner.revert()
        assert tuner.current_settings == original

    def test_revert_without_apply_is_noop(self):
        """Revert without prior apply should be a no-op."""
        tuner = Tuner()
        original = tuner.current_settings.copy()
        tuner.revert()
        assert tuner.current_settings == original

    def test_multiple_apply_reverts(self):
        """Only the last apply is reverted (single-level undo)."""
        tuner = Tuner()
        tuner.apply("performance")
        tuner.apply("eco")
        # Revert should restore performance (the state before eco)
        tuner.revert()
        assert tuner.current_settings == PROFILES["performance"]

    def test_revert_clears_previous(self):
        """After revert, previous_settings should be None."""
        tuner = Tuner()
        tuner.apply("performance")
        tuner.revert()
        assert tuner.previous_settings is None

    def test_apply_returns_new_settings(self):
        """apply() should return the newly applied settings."""
        tuner = Tuner()
        result = tuner.apply("eco")
        assert result == PROFILES["eco"]


class TestProfileConstants:
    """Tests for PROFILES dictionary."""

    def test_profiles_has_three_entries(self):
        """Should have balanced, performance, and eco profiles."""
        assert set(PROFILES.keys()) == {"balanced", "performance", "eco"}

    def test_each_profile_has_cpu_and_gpu(self):
        """Each profile should define cpu and gpu settings."""
        for name, profile in PROFILES.items():
            assert "cpu" in profile, f"{name} profile missing 'cpu'"
            assert "gpu" in profile, f"{name} profile missing 'gpu'"


class TestModuleLevelFunctions:
    """Tests for module-level apply() and revert() convenience functions."""

    def test_module_apply(self):
        """Module-level apply() should work like Tuner.apply()."""
        result = apply("eco")
        assert result == PROFILES["eco"]
        # Clean up
        revert()

    def test_module_revert(self):
        """Module-level revert() should work like Tuner.revert()."""
        apply("performance")
        result = revert()
        assert result == PROFILES["balanced"]
