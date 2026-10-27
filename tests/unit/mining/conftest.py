import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: runs a short real training loop (a few seconds on CPU)")

@pytest.fixture()
def synthetic_dir(tmp_path):
    pytest.importorskip("torch")
    from src.mining.synthetic import make_synthetic_dataset
    make_synthetic_dataset(tmp_path / "syn", per_split={"train": 24, "val": 8, "test": 8}, size=32, seed=1)
    return tmp_path / "syn"