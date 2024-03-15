#!/usr/bin/env python

from npx4.pysubmit import pysubmit
import argparse
import glob
import re
import os

if __name__ == "__main__":

    p = argparse.ArgumentParser(
            description='Cluster submission for timegaps.py. Creates histogram of all the time gaps in a day, finds the largest time gap of the day and the cumulative time gap')
    p.add_argument('--test', dest='test',
            default=False, action='store_true',
            help='Option for running off cluster to test')
    p.add_argument('-y', '--year', dest='year',
            type=int,
            help='Detector season (e.g., 2011 = IC86-2011)')
    p.add_argument('--mid', dest='mid',
            default=False, action='store_true',
            help='Runs 24H run num')
    p.add_argument('-o', '--outDir', dest='outDir',
            default='/data/user/eschmidt/stability/summarized_days',
            help='Output directory')
    args = p.parse_args()

    # Collect all files from specified year
    prefix = '/data/ana/CosmicRay/Anisotropy/IceCube'
    if args.year >= 2016:
        files = glob.glob(f'{prefix}/IC86-{args.year}/*/*.root')
    else:
        files = glob.glob(f'{prefix}/IC86-{args.year}/*.root')
    files.sort()


    # Group all files according to a given date or run
    batches = set([re.findall('\d{4}-\d{2}-\d{2}', f)[-1] for f in files])
    batches = sorted(batches)

    # Environment for script
    cvmfs = '/cvmfs/icecube.opensciencegrid.org/py3-v4.1.1/icetray-start'
    meta = 'icetray/stable'
    header = [f'#!/bin/sh {cvmfs}', f'#METAPROJECT {meta}']
    # ROOT tools not automatically loaded
    header += ['export PYTHONPATH="$PYTHONPATH:${SROOT}/lib"']
    # Request increased memory: 8 GB, overkill (shouldn't need more than 4)
    sublines = ["request_memory = 2000"]  

    # Run over all (d)ates or (r)uns
    for dr in batches:

        # Limit to relevant files
        dr_files = sorted([f for f in files if dr in f])

        # Prepare output filenames
        # Assumes all dates/runs belong to just one detector configuration
        config = re.findall('IC86-\d{4}', dr_files[0])[-1]
        out = f'{args.outDir}/num_{config}_{dr}.txt'

        # Run
        dr_files = ' '.join(dr_files)
        if args.mid:
                cmd = f'{os.getcwd()}/day_run_num.py -i {dr_files} -o {out} -y {args.year}'
        
        out = f'{args.outDir}/sum_{config}_{dr}.txt'
        cmd = f'{os.getcwd()}/day_run_num_24H.py -i {dr_files} -o {out} -y {args.year}'

        
        print(cmd)
        pysubmit(cmd, test=args.test, header=header, sublines = sublines)
