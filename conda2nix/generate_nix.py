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

  builder = ./build.sh;

  phases = [ "unpackPhase" "buildPhase" ];


  meta = with lib; {{
    description = "{description}";
    homepage = "{homepage}";
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

PRE_BUILD_SH = '''
set -e

source $stdenv/setup

PREFIX=$out
mkdir $out

unpackPhase
cd $sourceRoot

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
        'openssl',
        'libpng',
        'libuuid',
        'zlib',
        'bzip2',
        'perl',
        'pandoc',
        'cmake',
        'htslib',
        ])
requirements_renamed = {
        'pip': 'python3Packages.pip',
        'setuptools': 'python3Packages.setuptools',
        'cython': 'python3Packages.cython',
        'biopython': 'python3Packages.biopython',
        'pandas' : 'python3Packages.pandas',
        'numpy' : 'python3Packages.numpy',
        'scipy' : 'python3Packages.scipy',
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
    if type(url) == list:
        url = url[0]
    for method in ['sha256']:
        if method in src:
            hash_method = method
            hash_value = src[method]
            break
    else:
        raise KeyError(f'Could not find hash in {src}')
    return TEMPLATE_SRC_URL.format(url=url, hash_value=hash_value, hash_method=hash_method)

def as_dependencies(deps, sep, is_top=False):
    if deps is None:
        return ''
    dependencies = [conda2nix_requirement(r)
                for r in deps]
    dependencies = [dep for dep in dependencies if dep]
    if is_top:
        dependencies = [dep.split('.')[0] for dep in dependencies]
        dependencies.append('stdenv')
        dependencies.append('lib')
        dependencies.append('fetchurl')
    return sep.join(set(dependencies))


def extract_build(pk):
    bfile = 'bioconda-recipes/recipes/{}/build.sh'.format(pk['package']['name'])
    base = None
    if path.exists(bfile):
        with open(bfile) as ifile:
            base = ifile.read()
    elif 'script' in pk['build']:
        script = pk['build']['script']
        if type(script) == str:
            base = 'python ' + pk['build']['script']
        elif type(script) == list:
            base = '\n'.join(script)
    if base is None:
        raise KeyError(f'Could not extract buildPhase from {pk}')
    return PRE_BUILD_SH + base


def normalize_build(b):
    return b

def generate_nix(pk, dirname):
    dependencies = as_dependencies(all_requirements_of(pk), ', ', True)
    buildInputs = as_dependencies(pk.get('requirements', {}).get('build', []), ' ')
    nativeBuildInputs = as_dependencies(pk.get('requirements', {}).get('run', []), ' ')
    build_sh = normalize_build(extract_build(pk))

    pname = pk['package']['name']
    version = pk['package']['version']
    checkPhase = ''
    description = pk['about']['summary'] \
                .replace('"', r'\"') \
                .replace('$', r'\$')
    homepage = pk['about']['home']
    src = extract_source(pk['source'])
    odir = f'{dirname}/{pk["package"]["name"]}'
    os.makedirs(odir, exist_ok=True)
    with open(f'{odir}/default.nix', 'wt') as out:
        out.write(TEMPLATE.format(**locals()))
    with open(f'{odir}/build.sh', 'wt') as out:
        out.write(build_sh)
    return pk['package']['name']

