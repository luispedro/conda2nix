from os import path
import yaml
import os
import jinja2

compiler = {
        'c': 'gcc',
        'cxx': 'gcc',
        }.get

def pin_compatible(x, max_pin=None):
    if x in [
        'llvm-openmp',
        'zlib',
        'xerces-c',
        'boost-cpp',
        'boost',
        'eigen',
        'glpk',
        'hdf5',
        'bzip2',
        'qt',
        'libsvm',
        'coinmp',
        'sqlite',
        'scipy',
        'perl',
        'pysam',
        'h5py',
        'glib',
        'numpy',
        'ldc']: return x
    raise ValueError(x)

def pin_subpackage(x, exact=False, max_pin=None):
    return x

def environ(x):
    return x

def cdt(x):
    return x

template_kwargs = {
        'compiler' : compiler,
        'pin_compatible' : pin_compatible,
        'pin_subpackage': pin_subpackage,
        'environ': environ,
        'cdt': cdt,
        'os': os,
        }


def normalize_package(pk):
    if pk.get('requirements') is None:
        pk['requirements'] = {}
    for r in ['host', 'build', 'run']:
        if pk.get('requirements').get(r) is None:
            pk['requirements'][r] = []
    return pk

def load_recipe(r):
    with open(path.join(r, 'meta.yaml'), 'rt') as ifile:
        t = jinja2.Template(ifile.read())
    return normalize_package(yaml.safe_load(''.join(t.generate(**template_kwargs))))

def load_all(basedir, include_r=False):
    recipes = os.listdir(basedir)
    metas = {}

    for r in recipes:
         if not include_r and (r.startswith('r-') or r.startswith('bioconductor-')):
             continue
         if not path.exists(path.join(basedir, r, 'meta.yaml')):
             continue
         r = load_recipe(path.join(basedir, r))
         metas[r['package']['name']] = r
    return metas


