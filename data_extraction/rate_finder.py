#!/usr/bin/env python

########################################################################
###    Code meant to summarize all data-checking results. Combines   ###
###    information from I3 livetime, root files, and fits files to   ###
###    output rates and store a summary of every run.                ###
########################################################################


import numpy as np
import re, os
import json
import healpy as hp
from datetime import datetime as dt
from glob import glob
from pathlib import Path


def main():

    # Run over all detector configurations by default
    configs = [f'IC86-{yy}' for yy in range(2011,2023)]

    # File locations
    # NOTE: these may need to be updated to your own paths
    stability = '/data/user/zhardnett/stability'
    map_dir = '/data/user/fmcnally/anisotropy/maps'
    out_dir = '/data/user/zhardnett/stability'

    # Run to detector config dictionary
    with open(f'{stability}/run2cfg.json', 'r') as f:
        run2cfg = json.load(f)

    # Extract detector livetime and bad runs from good run list
    print('Loading livetimes from i3live...')
    goodrunfile = '/home/zhardnett/goodrunslist.txt'
    i3_livetime = get_livetime(goodrunfile, run2cfg)
    badruns = get_bad_runs(goodrunfile)

    # Load map counts for all detector configurations
    print('Loading fits data...')
    fits_data = fits_scanner(map_dir, stability)

    # Load counts and livetimes from root files
    print('Loading root data...')
    root_data = root_scanner(stability)

    # String formatting for day and run output
    def day_formatter(t, n, root_fits):
        return f'\t{root_fits:<7} - {t:<7} - {n:<11} - {n/t:.2f}'

    h = f'\trun     - {"t (i3)":<7} - {"t (root)":<7} - {"nEvents":<10} - rate'
    def run_formatter(run, t_i3, t, n):
        gb = 'b' if run in badruns else 'g'
        return f'\t{run}{gb} - {t_i3:<7} - {t:<7} - {n:<11} - {n/t:.2f}'


    # Save rates from root and fits files
    rates = {'root':{c:{} for c in configs}, 'fits':{c:{} for c in configs}}

    # Run through each config, storing all root|fits info
    for cfg in configs:

        # Store rates and dates for rate check, cfg_info for output
        cfg_info = []

        # Run through every day present in root files
        for day, runs in root_data[cfg].items():

            # Note if element doesn't have fits data
            if day not in fits_data[cfg].keys():
                print(f'Warning: {day} ({cfg}) has no fits files!')
                continue

            # Root summary for the day
            cfg_info += [f'\n{day}']
            t_root = sum([run['livetime'] for r, run in runs.items()])
            n_root = sum([run['nEvents'] for r, run in runs.items()])
            cfg_info += [day_formatter(t_root, n_root, 'root')]
            rates['root'][cfg][day] = n_root/t_root

            # NOTE: Looks like runs are grouped strangely in /data/ana
            # DST root files? e.g., 2022-05-14 in IC86-2022
            # Follow up with JCDV
            if day not in i3_livetime[cfg].keys():
                print(f'Skipping {day} in {cfg}')
                continue

            # Fits/i3 summary for the day
            t_i3 = sum([t_run for r, t_run in i3_livetime[cfg][day].items()
                    if r not in badruns]) 
            n_fits = fits_data[cfg][day]
            cfg_info += [day_formatter(t_i3, n_fits, 'fits')]
            rates['fits'][cfg][day] = n_fits/t_i3

            # Individual run summaries
            cfg_info += [h]
            for run, info in runs.items():

                # Note if run is not in root files
                try: t_i3 = i3_livetime[cfg][day][run]
                except KeyError:
                    t_i3 = 'N/A'

                t_root = info['livetime']
                n_root = info['nEvents']
                cfg_info += [run_formatter(run, t_i3, t_root, n_root)]

        # Save text in summary text file
        out = f'{out_dir}/{cfg}_summary.txt'
        np.savetxt(out, cfg_info, fmt='%s')


    # Save rate information
    out = f'{out_dir}/rates.json'
    with open(out, 'w') as f:
        json.dump(rates, f)

    print(f'Finished! Summary output saved to {out_dir}')


""" Extract livetimes from good run file """
def get_livetime(goodrunfile, run2cfg):

    i3_livetime = {}

    # Load I3 good run list from json file
    with open(goodrunfile, 'r') as f:
        i3_data = json.load(f)
        i3_data = i3_data['runs']

    for run_info in i3_data:

        # Instate each day as a key for the dictionary
        day = run_info['good_tstart'].split(' ')[0]
        run = run_info['run']

        # Ignore runs that are before/after the dates of the run dictionary
        try: cfg = run2cfg[str(run)]
        except KeyError:
            continue

        if cfg not in i3_livetime.keys():
            i3_livetime[cfg] = {}
        if day not in i3_livetime[cfg].keys():
            i3_livetime[cfg][day] = {}

        # Deal with null livetimes
        if run_info['good_tstop'] == None:
            #i3_livetime[cfg][day][run] = 'null'
            i3_livetime[cfg][day][run] = np.nan
            continue

        # Obtain start/stop times from list, removing fractions of seconds
        t_i = run_info['good_tstart'].split('.')[0]
        start_t = dt.strptime(t_i, '%Y-%m-%d %H:%M:%S')
        t_f = run_info['good_tstop'].split('.')[0]
        stop_t = dt.strptime(t_f, '%Y-%m-%d %H:%M:%S')

        # Check if run crosses over a day and adjust start/stop times
        if start_t.day != stop_t.day:
            day_aft = stop_t.strftime('%Y-%m-%d')
            if day_aft not in i3_livetime[cfg].keys():
                i3_livetime[cfg][day_aft] = {}
            midnight = dt.combine(stop_t, dt.min.time())
            i3_livetime[cfg][day][run] = (midnight - start_t).seconds
            i3_livetime[cfg][day_aft][run] = (stop_t - midnight).seconds

        # If no crossover, the run is fully contained in a day
        else:
            i3_livetime[cfg][day][run] = (stop_t - start_t).seconds

    return i3_livetime


""" Extract bad runs from good run file """
def get_bad_runs(goodrunfile):

    badruns = []

    # Load I3 good run list from json file
    with open(goodrunfile, 'r') as f:
        i3_data = json.load(f)
        i3_data = i3_data['runs']

    for run_info in i3_data:
        if run_info['good_i3'] == False:
            badruns.append(run_info['run'])

    return sorted(set(badruns))


""" Checks modified times from a file list against the last update"""
def is_modified(filelist, storage, update=False):

    filelist.sort()
    mtimes = []
    for f in filelist:
        path = Path(f)
        mtimes += [f'{f} : {path.stat().st_mtime}\n']

    if not os.path.isfile(storage):
        print(f'File {storage} not found! Creating...')
        with open(storage, 'w') as f:
            f.writelines(mtimes)
        return True

    if update:
        with open(storage, 'w') as f:
            f.writelines(mtimes)
        return False

    with open(storage, 'r') as f:
        old_mtimes = f.readlines()
        if old_mtimes != mtimes:
            return True

    return False


def fits_scanner(map_dir, summary_dir):

    # Find nEvents for each day
    fits_files = sorted(glob(f'{map_dir}/IC86-????/*sid_????-??-??.fits'))
    configs = sorted(set([re.findall('IC86-\d{4}', f)[0] for f in fits_files]))

    # Run through each configuration
    for cfg in configs:

        # Retrieve fits files
        fits_data = {}
        cfg_files = [f for f in fits_files if cfg in f]

        # Update summary dictionaries and modified times if needed
        mod_file = f'{summary_dir}/mtimes_{cfg}.txt'
        if is_modified(cfg_files, mod_file):

            # Run through each fits file
            print(f'Map summary file for {cfg} is out of date! Updating...')
            for fits in cfg_files:

                # Read fits file
                map_i = hp.read_map(fits, verbose=0)
                date = re.split('_|\.', fits)[-2]

                # Save information in dictionary
                fits_data[date] = int(map_i.sum())

            outfile = f'{summary_dir}/mapcounts_{cfg}.json'
            with open(outfile, 'w') as f:
                json.dump(fits_data, f)

            # Update modified times
            is_modified(cfg_files, mod_file, update=True)

    fits_data = {}
    for cfg in configs:
        with open(f'{summary_dir}/mapcounts_{cfg}.json', 'r') as f:
            fits_data[cfg] = json.load(f)

    return fits_data



def root_scanner(summary_dir):

    # Find nEvents and livetime for each root file
    root_data = {}

    root_summary = sorted(glob(f'{summary_dir}/root-summary_*.txt'))

    # Run through config
    for summary in root_summary:

        # Identify detector configuration and create storage
        cfg = re.findall('IC86-\d{4}', summary)[-1]
        root_data[cfg] = {}

        # Import run summaries
        with open(summary, 'r') as f:
            cfg_data = f.readlines()

        # obtain relevant data by dividing up the lines
        cfg_data = [line.strip().split(' - ') for line in cfg_data]

        for day, run, ct, t in cfg_data:

            # Use integer values for runs
            run = int(run)

            # create days as keys
            if day not in root_data[cfg].keys():
                root_data[cfg][day] = {}

            # create run as keys in days
            if run not in root_data[cfg][day].keys():
                root_data[cfg][day][run] = {'nEvents':0, 'livetime':0}

            # combine livetime and nEvents for runs already in data
            root_data[cfg][day][run]['nEvents'] += int(ct)
            root_data[cfg][day][run]['livetime'] += int(t)

    return root_data


if __name__ == "__main__":
    main()




