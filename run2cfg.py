#!/usr/bin/env python

##=========================================================================##
## Associates runs with detector configuration by scanning level2 directories

import numpy as np
import re
import json

from glob import glob


if __name__ == "__main__":

    out = '/data/user/zhardnett/stability'
    d = {}

    # Collect all files from relevant years
    years = [i for i in range(2011, 2024)]
    configs = [f'IC86.{yy}' for yy in years[:-1]]

    for yy in years:

        print(f'Working on {yy}...')
        prefix = f'/data/exp/IceCube/{yy}/filtered/level2'

        files = glob(f'{prefix}/????/**/*', recursive=True)

        print(f'Number of total files: {len(files)}')
        for cfg in configs:
            files_i = [f for f in files if cfg in f]
            runs = sorted(set([re.findall('Run\d{8}',f)[-1] for f in files_i]))
            runs = [r[-6:] for r in runs]       # Only save the relevant number
            if len(runs) != 0:
                print(f'Runs for {cfg} : {len(runs)}')

            out_cfg = cfg.replace('.','-')
            for run in runs:
                d[run] = out_cfg

        print()

    print('File collection complete! Saving...')
    np.save(f'{out}/run2cfg.npy', d)
    with open(f'{out}/run2cfg.json', 'w') as f:
        json.dump(d, f)
