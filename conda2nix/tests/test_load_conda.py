from conda2nix.load_conda import is_line_linux

def test_is_line_linux():
    assert is_line_linux('')
    assert is_line_linux('    hello')
    assert is_line_linux('  # [linux]')
    assert not is_line_linux('  # [osx]')
    assert not is_line_linux('  # [osx and py3k]')
    assert is_line_linux('  # [linux and py3k]')
