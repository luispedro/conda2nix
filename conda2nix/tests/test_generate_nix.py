from conda2nix.generate_nix import strip_version, as_dependencies, extract_build, normalize_build, extract_source


def test_strip_version():
    assert strip_version('python >=3.6') == 'python'
    assert strip_version('python') == 'python'
    assert strip_version('python 3.6') == 'python'
    assert strip_version('python 3.6.1') == 'python'
    assert strip_version('python 3.6.1 <3.7') == 'python'
    assert strip_version('python 3.6.1 <=3.7') == 'python'
    assert strip_version('python 3.6.1 !=3.7') == 'python'
    assert strip_version('python 3.6.1 ==3.7') == 'python'
    assert strip_version('python 3.6.1 >3.7') == 'python'
    assert strip_version('python 3.6.1 >=3.7') == 'python'

