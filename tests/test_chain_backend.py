import pytest
try:
    from backends import ChainBackend, load_backend
except ImportError:
    pytest.skip("backends module not available in this environment", allow_module_level=True)


def test_chain_backend_sequential():
    local = load_backend("local")
    remote = load_backend("remote")
    chain = ChainBackend([local, remote])
    # output of local becomes input for remote
    assert chain.generate("hi") == "[remote] [local] hi"
