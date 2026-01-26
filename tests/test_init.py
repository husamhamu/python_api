from blazing.routes.pokemon import get_integer

def test_get_integer():
    assert 42 == get_integer()