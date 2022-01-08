import os
from os import path
import re

TEMPLATE = '''
{{ {dependencies} }}:

stdenv.mkDerivation rec {{
  pname = "{pname}";
  version = "{version}";

  {src}

  buildInputs = [ {buildInputs} ];
  nativeBuildInputs = [ {nativeBuildInputs} ];

  checkPhase = ''

  {checkPhase}

  '';

  buildPhase = ''

  {buildPhase}

  '';

  phases = [ "unpackPhase" "buildPhase" ];


  meta = with lib; {{
    description = "{description}";
    homepage = {homepage};
    platforms = platforms.all;
    maintainers = with maintainers; [ luispedro ];
  }};
}}
'''

TEMPLATE_SRC_GH = '''
  src = fetchFromGitHub {{
    repo = "{repo}";
    owner = "{owner}";
    rev = "{rev}";
    sha256 = "{sha256}";
  }};
'''

TEMPLATE_SRC_URL = '''
  src = fetchurl {{
    url = "{url}";
    {hash_method} = "{hash_value}";
  }};
'''

def norm_requirement(r):
    return re.split(r'[ <=>]',r)[0]

def all_requirements_of(ell):
    if not ell.get('requirements'):
        return
    for rs in ell.get('requirements', {}).values():
        if not rs:
            continue
        for r in rs:
            if r is None:
                continue
            yield norm_requirement(r)

requirements_available = set([
        'python',
        'pandas',
        'numpy',
        'scipy',
        'openssl',
        'libpng',
        'libuuid',
        'zlib',
        'bzip2',
        'perl',
        'pandoc',
        'cmake',
        ])
requirements_renamed = {
        'pip': 'python.pip',
        'setuptools': 'python.setuptools',
        'cython': 'python.cython',
        'biopython': 'python.biopython',
        }
requirements_stdenv = set([
        'autoconf',
        'automake',
        'gcc',
        'make',
        ])

def conda2nix_requirement(r):
    if r in requirements_stdenv:
        return ''
    if r in requirements_renamed:
        return requirements_renamed[r]
    if r in requirements_available:
        return r


def extract_source(src):
    if type(src) == list:
        src = src[0]
    url = src['url']
    for method in ['sha256', 'md5']:
        if method in src:
            hash_method = method
            hash_value = src[method]
            break
    else:
        raise KeyError(f'Could not find hash in {src}')
    return TEMPLATE_SRC_URL.format(url=url, hash_value=hash_value, hash_method=hash_method)

def as_dependencies(deps, sep, add_stdenv=False):
    if deps is None:
        return ''
    dependencies = [conda2nix_requirement(r)
                for r in deps]
    dependencies = [dep for dep in dependencies if dep]
    if add_stdenv:
        dependencies.append('stdenv')
        dependencies.append('lib')
        dependencies.append('fetchurl')
    return sep.join(dependencies)


def extract_build(pk):
    bfile = '../../recipes/{}/build.sh'.format(pk['package']['name'])
    if path.exists(bfile):
        with open(bfile) as ifile:
            return ifile.read()
    elif 'script' in pk['build']:
        script = pk['build']['script']
        if type(script) == str:
            return 'python ' + pk['build']['script']
        elif type(script) == list:
            return '\n'.join(script)
    raise KeyError(f'Could not extract buildPhase from {pk}')


def normalize_build(b):
    return b \
            .replace('${PREFIX}', '$out') \
            .replace('$PREFIX', '$out')

def generate_nix(pk, dirname):
    dependencies = as_dependencies(all_requirements_of(pk), ', ', True)
    buildInputs = as_dependencies(pk.get('requirements', {}).get('build', []), ' ')
    nativeBuildInputs = as_dependencies(pk.get('requirements', {}).get('run', []), ' ')
    buildPhase = normalize_build(extract_build(pk))

    pname = pk['package']['name']
    version = pk['package']['version']
    checkPhase = ''
    description = pk['about']['summary']
    homepage = pk['about']['home']
    src = extract_source(pk['source'])
    odir = f'{dirname}/{pk["package"]["name"]}'
    os.makedirs(odir, exist_ok=True)
    with open(f'{odir}/default.nix', 'wt') as out:
        out.write(TEMPLATE.format(**locals()))
    return pk['package']['name']

