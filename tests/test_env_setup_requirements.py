import pytest
from installer import env_setup


def test_parse_requirements_extras_markers():
    grouped = env_setup._parse_requirements(["demo[extra1,extra2]>=1; sys_platform=='win32'"])
    parsed = grouped["demo"][0]
    assert parsed.extras == {"extra1", "extra2"}
    assert str(parsed.specifier) == ">=1"
    assert parsed.marker == 'sys_platform == "win32"'


def test_resolve_conflicts_merges_extras_and_markers():
    reqs = [
        "demo[one]; sys_platform=='win32'",
        "demo[two]; sys_platform=='linux'",
    ]
    packages, conflicts = env_setup.resolve_conflicts(reqs)
    assert conflicts == {}
    expected_marker = 'sys_platform == "linux" or sys_platform == "win32"'
    assert packages == [f"demo[one,two]; {expected_marker}"]
