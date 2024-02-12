import os
from os import path
import shutil
import re

PYTHON_PACKAGE_TEMPLATE = '''
{{ {dependencies} }}:

python3Packages.buildPythonPackage rec {{
  pname = "{pname}";
  version = "{version}";

  {src}

  buildInputs = [ {buildInputs} ];
  nativeBuildInputs = [ {nativeBuildInputs} ];
  doCheck = false;

  meta = with lib; {{
    description = "{description}";
    homepage = "{homepage}";
    platforms = platforms.all;
    maintainers = with maintainers; [ luispedro ];
  }};
}}
'''

NIX_TEMPLATE = '''
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
  {patches}
'''

PRE_BUILD_SH = '''
set -e

PKG_NAME={pname}
PKG_VERSION={version}
PKG_BUILDNUM=0

source $stdenv/setup

PREFIX=$out
mkdir -p $out
mkdir -p $out/bin

unpackPhase
cd $sourceRoot
export SRC_DIR="$(pwd)"

'''

def is_python_build(pk):
    import re
    build_script = pk['build'].get('script')
    if build_script is None: return False
    return build_script.startswith('python -m pip install')


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
        'python': 'python3',
        'pip': 'python3Packages.pip',
        'setuptools': 'python3Packages.setuptools',
        'cython': 'python3Packages.cython',
        'biopython': 'python3Packages.biopython',
        'pandas' : 'python3Packages.pandas',
        'numpy' : 'python3Packages.numpy',
        'scipy' : 'python3Packages.scipy',
        'scikit-learn': 'python3Packages.scikit-learn',
        'matplotlib-base': 'python3Packages.matplotlib',
        'matplotlib': 'python3Packages.matplotlib',
        'six': 'python3Packages.six',
        'pyyaml': 'python3Packages.pyyaml',
        'requests': 'python3Packages.requests',
        'tqdm': 'python3Packages.tqdm',
        'seaborn': 'python3Packages.seaborn',
        'joblib': 'python3Packages.joblib',

        'mysql-connector-c': 'libmysqlconnectorcpp',
        'wget': 'wget',
        'pigz': 'pigz',

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


def extract_source(src, patch_files):
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
    if patch_files:
        patches = 'patches = [ ' + ' '.join([f'./{p}' for p in patch_files]) + ' ];'
    else:
        patches = ''
    return TEMPLATE_SRC_URL.format(
                        url=url,
                        hash_value=hash_value,
                        hash_method=hash_method,
                        patches=patches)

def strip_version(r):
    return re.split(r'[ <=>]',r)[0]

def as_dependencies(deps, sep, is_top=False):
    if deps is None:
        return ''
    deps = [strip_version(r) for r in deps]
    dependencies = [conda2nix_requirement(r)
                for r in deps]
    dependencies = [dep for dep in dependencies if dep]
    if is_top:
        dependencies = [dep.split('.')[0] for dep in dependencies]
        dependencies.append('stdenv')
        dependencies.append('lib')
        dependencies.append('zlib')
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
            base = pk['build']['script']
        elif type(script) == list:
            base = '\n'.join(script)
    if base is None:
        raise KeyError(f'Could not extract buildPhase from {pk}')
    pre_build = PRE_BUILD_SH.format(
            pname=pk['package']['name'],
            version=pk['package']['version'])
    return pre_build + base


def normalize_build(b):
    return b

def generate_nix(pk, dirname):
    dependencies = as_dependencies(all_requirements_of(pk), ', ', True)
    buildInputs = as_dependencies(pk.get('requirements', {}).get('build', []), ' ')
    nativeBuildInputs = as_dependencies(
                pk.get('requirements', {}).get('run', [])
                + pk.get('requirements', {}).get('host', [])
                , ' ')
    build_sh = normalize_build(extract_build(pk))

    pname = pk['package']['name']
    version = pk['package']['version']
    checkPhase = ''
    description = pk['about']['summary'] \
                .replace('"', r'\"') \
                .replace('$', r'\$')
    homepage = pk['about']['home']
    odir = f'{dirname}/{pk["package"]["name"]}'
    patch_files = pk.get('source', {}).get('patches', [])

    src = extract_source(pk['source'], patch_files)
    os.makedirs(odir, exist_ok=True)

    if is_python_build(pk):
        with open(f'{odir}/default.nix', 'wt') as out:
            out.write(PYTHON_PACKAGE_TEMPLATE.format(**locals()))
    else:
        build_sh = normalize_build(extract_build(pk))
        with open(f'{odir}/default.nix', 'wt') as out:
            out.write(NIX_TEMPLATE.format(**locals()))
        for p in patch_files:
            shutil.copy(f'bioconda-recipes/recipes/{pname}/{p}', f'{odir}/{p}')
        with open(f'{odir}/build.sh', 'wt') as out:
            out.write(build_sh)
    return pk['package']['name']

