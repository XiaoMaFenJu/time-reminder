from app.blackhole import growth_progress
from app.config import Config


def test_blackhole_threshold_growth_and_reset():
    assert growth_progress(True, True, 60, 60) is None
    assert 0 < growth_progress(True, True, 61, 60) < 1
    assert growth_progress(True, True, 510, 60) == 0.5
    assert growth_progress(True, True, 960, 60) == 1
    assert growth_progress(True, True, 1200, 60) == 1
    assert growth_progress(True, False, 1200, 60) is None
    assert growth_progress(False, True, 1200, 60) is None


def test_blackhole_setting_is_backward_compatible():
    assert not Config.from_dict({}).blackhole_enabled
    assert Config.from_dict({'blackhole_enabled': True}).blackhole_enabled
