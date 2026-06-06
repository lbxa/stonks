from data import default_cache_dir


def test_default_cache_dir_is_untracked_cache_path() -> None:
    assert str(default_cache_dir()) == ".cache/stonks"
