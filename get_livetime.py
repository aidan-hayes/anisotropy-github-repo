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

    # File location
    ana = '/data/ana/CosmicRay/Anisotropy/IceCube/twelve_year/livetime'
    grl = f'{ana}/goodrunlist.json'

    # Run to detector config dictionary
    with open(f'{ana}/run2cfg.json', 'r') as f:
        run2cfg = json.load(f)

    # Define start and end times for livetime
    t_start = 20100513
    t_end = 20230513

    # Extract detector livetime and bad runs from good run list
    print('Loading livetimes from i3live...')
    i3_livetime = get_livetime(grl, run2cfg, t_start, t_end)
    total_livetime = get_total_livetime(grl, run2cfg, t_start, t_end)

    # Run through each config, storing all livetime info
    for cfg, days in i3_livetime.items():

        # Store rates and dates for rate check, cfg_info for output
        t_good = 0
        n_days = 0

        # Run through every day present in the detector config
        for day, runs in days.items():

            # Update running totals for good and total livetime
            n_days += 1
            t_good += sum([t for r, t in runs.items()])

        # Print output
        #t_tot = n_days * 86400  # assumes complete days (OVERESTIMATE)
        t_tot = total_livetime[cfg]
        print(f'{cfg} : {t_good/86400:.2f} / {t_tot/86400:.2f}  ({t_good/t_tot*100:.2f}%)')



def load_grl(goodrunfile, t_start=None, t_end=None):

    with open(goodrunfile, 'r') as f:
        i3_data = json.load(f)
        i3_data = i3_data['runs']

    # Sort by run
    i3_data.sort(key=lambda row: row['run'])

    # Reduce to target range
    reduced_data = []
    for row in i3_data:
        day = row['good_tstart'].split(' ')[0]
        day_as_int = int(day.replace('-',''))
        if t_start != None:
            if day_as_int < t_start:
                continue
        if t_end != None:
            if day_as_int >= t_end:
                continue
        reduced_data += [row]

    return reduced_data


""" Extract livetimes from good run file """
def get_livetime(goodrunfile, run2cfg, t_start=None, t_end=None):

    i3_livetime = {}

    i3_data = load_grl(goodrunfile, t_start, t_end)

    for run_info in i3_data:

        # Instate each day as a key for the dictionary
        day = run_info['good_tstart'].split(' ')[0]
        run = run_info['run']

        # Ignore runs that are before/after the dates of the run dictionary
        try: cfg = run2cfg[str(run)]
        except KeyError:
            continue

        # Ignore bad runs
        if not run_info['good_i3']:
            continue

        if cfg not in i3_livetime.keys():
            i3_livetime[cfg] = {}
        if day not in i3_livetime[cfg].keys():
            i3_livetime[cfg][day] = {}

        # Deal with null livetimes
        if run_info['good_tstop'] == None:
            print('No good_tstop for a good run?. Not good...')
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


def get_total_livetime(goodrunfile, run2cfg, t_start=None, t_end=None):

    livetime = {}

    i3_data = load_grl(goodrunfile, t_start=t_start, t_end=t_end)

    # Store the start time for each run
    t = [run_info['good_tstart'].split('.')[0] for run_info in i3_data]
    t = [dt.strptime(t_i, '%Y-%m-%d %H:%M:%S') for t_i in t]
    # Calculate run time as the difference between start times
    run_times = [(t_f - t_i).seconds for t_i, t_f in zip(t[:-1], t[1:])]
    run_times = np.asarray(run_times)

    # Establish detector configurations for each run
    runs = [str(run_info['run']) for run_info in i3_data][:-1]
    valid_runs = sorted(run2cfg.keys())
    cfgs = [run2cfg[run] if run in valid_runs else 'IC86-??' for run in runs]
    cfgs = np.asarray(cfgs)

    # Calculate livetimes
    for cfg in sorted(set(cfgs)):
        livetime[cfg] = run_times[cfgs==cfg].sum()

    return livetime




if __name__ == "__main__":
    main()




