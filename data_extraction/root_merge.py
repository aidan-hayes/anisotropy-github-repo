#!/usr/bin/env python

import re
from glob import glob

if __name__ == "__main__":

    prefix = '/data/user/eschmidt/stability/summarized_days'
    day_files = sorted(glob(f'{prefix}/*.txt'))
    prefix = '/data/user/fmcnally/anisotropy/stability/root_summaries'
    day_files += sorted(glob(f'{prefix}/*.txt'))
    out = '/data/user/fmcnally/anisotropy/stability'
    configs = sorted(set([re.findall('IC86-\d{4}',f)[0] for f in day_files]))

    for cfg in configs:

        print(f'Working on {cfg}...')

        cfg_files = [f for f in day_files if cfg in f]
        summary = []

        for cfg_file in cfg_files:
            with open(cfg_file, 'r') as f:
                summary += f.readlines()

        print(f'Writing to {out}/root-summary_{cfg}.txt')
        with open(f'{out}/root-summary_{cfg}.txt', 'w') as f:
            f.writelines(summary)
