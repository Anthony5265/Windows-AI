from optimization.tuning import Tuner, PROFILES


def test_apply_and_revert_profile():
    tuner = Tuner()
    original = tuner.current_settings.copy()
    tuner.apply("performance")
    assert tuner.current_settings == PROFILES["performance"]
    tuner.revert()
    assert tuner.current_settings == original


def test_revert_without_apply_is_noop():
    tuner = Tuner()
    original = tuner.current_settings.copy()
    tuner.revert()
    assert tuner.current_settings == original
