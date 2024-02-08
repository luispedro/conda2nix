import multiprocessing
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
        'pandas',
        'ldc']: return x
    return x
#    raise ValueError(x)

def pin_subpackage(x, exact=False, max_pin=None, allow_no_other_outputs=True):
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
        'PYTHON': 'python',
        }


def normalize_package(pk):
    if pk.get('requirements') is None:
        pk['requirements'] = {}
    for r in ['host', 'build', 'run']:
        if pk.get('requirements').get(r) is None:
            pk['requirements'][r] = []
    return pk

VARS = {
        'osx': False,
        'osx-amd64': False,
        'osx-arm64': False,
        'arm64': False,
        'win': False,

        'amd64': True,
        'x86_64': True,
        'unix': True,
        'linux': True,
        'linux64': True,

        'py3k': True,
        'py2k': False,
        'py': 311,
        'py27': False,
        'py34': False,
        'py35': False,
        'py36': False,

        'perl': 5.26,
        'mpi': 'mpi',
        'cdt_name': 'cdt',
        }

def is_line_linux(ell):
    import re
    if m := re.search('# +\[(.+)\]\s*$', ell):
        cond = m.group(1)
        try:
            return eval(cond, {}, VARS)
        except:
            print(ell)
            raise
    return True

def only_linux_lines(s):
    lines = [ell for ell in s.split('\n') if is_line_linux(ell)]
    return '\n'.join(lines)

def load_recipe(r):
    with open(path.join(r, 'meta.yaml'), 'rt') as ifile:
        t = jinja2.Template(only_linux_lines(ifile.read()))
    return normalize_package(
                yaml.safe_load(
                    ''.join(t.generate(**template_kwargs))))

def load_all(basedir, include_r=False):
    recipes = os.listdir(basedir)

    loaded = []
    with multiprocessing.Pool() as p:
        for r in recipes:
             if not include_r and (r.startswith('r-') or r.startswith('bioconductor-')):
                 continue
             if not path.exists(path.join(basedir, r, 'meta.yaml')):
                 continue

             loaded.append(
                     p.apply_async(
                         load_recipe,
                         args=(path.join(basedir, r),)
                         ))
        p.close()
        p.join()
    loaded = [ell.get() for ell in loaded]
    return {
            r['package']['name']: r
            for r in loaded
            }


