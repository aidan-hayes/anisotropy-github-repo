#!/usr/bin/env python

from npx4.pysubmit import pysubmit
import argparse
from glob import glob
import re
import os


if __name__ == "__main__":

    p = argparse.ArgumentParser(
            description='Cluster submission for root_extractor.py')
    p.add_argument('--test', dest='test',
            default=False, action='store_true',
            help='Option for running off cluster to test')
    p.add_argument('-y', '--year', dest='year',
            type=int,
            help='Detector season (e.g., 2011 = IC86-2011)')
    p.add_argument('-o', '--outDir', dest='outDir',
            default='/data/user/zhardnett/root_summaries',
            help='Output directory')
    args = p.parse_args()


    # Collect all files from specified year
    prefix = '/data/ana/CosmicRay/Anisotropy/IceCube'
    files = glob(f'{prefix}/IC86-{args.year}/**/*.root', recursive=True)
    files.sort()

    # Group all files according to a given date
    dates = sorted(set([re.findall('\d{4}-\d{2}-\d{2}', f)[-1] for f in files]))
    if args.test:
        dates = dates[:2]

    # Environment for script
    cvmfs = '/cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/icetray-start'
    meta = 'icetray/stable'
    header = [f'#!/bin/sh {cvmfs}', f'#METAPROJECT {meta}']
    # ROOT tools not automatically loaded
    header += ['export PYTHONPATH="$PYTHONPATH:${SROOT}/lib"']
    # Request increased memory: 8 GB, overkill (shouldn't need more than 4)
    sublines = ["request_memory = 2000"]  

    # Run over all dates
    for date in dates:

        # Limit to relevant files
        files_i = sorted([f for f in files if date in f])
        if files_i == []:
            print(f'No files found for {date}! Skipping...')
            continue

        # Run
        files_i = ' '.join(files_i)
        out = f'{args.outDir}/sum_IC86-{args.year}_{date}.txt'
        cmd = f'{os.getcwd()}/root_extractor.py -i {files_i} -o {out}'

        if os.path.isfile(out) and not args.overwrite:
            print(f'Files {out} already exists! Skipping...')
            continue

        pysubmit(cmd, test=args.test, header=header, sublines=sublines)

