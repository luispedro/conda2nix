from collections import Counter
import pandas as pd
import re
import os

from conda2nix.load_conda import load_all
from conda2nix.generate_nix import generate_nix, all_requirements_of, conda2nix_requirement


def main():
    metas = load_all('bioconda-recipes/recipes', include_r=False)

    print(f'Loaded {len(metas)} recipes')

    pkg_status = {}
    missing_deps = []

    for pk,met in metas.items():
        rs = list(all_requirements_of(met))
        ns = []
        have_all = True
        for r in rs:
            n = conda2nix_requirement(r)
            if n is not None or r in metas:
                continue
            else:
                missing_deps.append(r)
                have_all = False

        if have_all:
            try:
                generate_nix(met, 'nixpkgs/')
                pkg_status[pk] = 'OK'
            except Exception as e:
                if 'md5' in met.get('source', {}):
                    pkg_status[pk] = 'MD5-ONLY'
                else:
                    pkg_status[pk] = 'NIX-ERROR'
        else:
            pkg_status[pk] = 'MISSING-DEP'


    with open('nixpkgs/all-packages.nix', 'wt') as all_packages:
        all_packages.write('with (import <nixpkgs> {});\n')
        all_packages.write('\n{\n')
        for p in sorted([p for p,st in pkg_status.items() if st == 'OK']):
            all_packages.write(f'  {p} = pkgs.callPackage ./{p} {{ }};\n\n')
        all_packages.write('\n}\n')

    pkg_status_counts = Counter(pkg_status.values())
    missing_deps = pd.Series(Counter(missing_deps)).sort_values()[::-1]
    missing_deps[:20]

    print(f'''
Generated nix scripts

- {pkg_status_counts['OK']} generated OK
- {pkg_status_counts['MD5-ONLY']} only have MD5 hash
- {pkg_status_counts['NIX-ERROR']} had an error in nix generation
- {pkg_status_counts['MISSING-DEP']} have at least one missing dependency for a total of {len(missing_deps)} unique missing dependencies.

''')
    pd.DataFrame({'status' : pkg_status}).to_csv('package-status.tsv', sep='\t')
    pd.DataFrame({'count': missing_deps}).to_csv('missing-dependencies.tsv', sep='\t')


if __name__ == '__main__':
    main()

