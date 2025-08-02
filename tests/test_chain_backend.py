from backends import ChainBackend, load_backend


def test_chain_backend_sequential():
    local = load_backend("local")
    remote = load_backend("remote")
    chain = ChainBackend([local, remote])
    # output of local becomes input for remote
    assert chain.generate("hi") == "[remote] [local] hi"
