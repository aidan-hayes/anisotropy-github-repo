#!/usr/bin/env python

import argparse
import numpy as np
from datetime import datetime

if __name__ == "__main__":

    p = argparse.ArgumentParser()
    p.add_argument('-c', '--config', dest='config',
            nargs='+',
            help='Detector configuration (IC86-2011, IC86-2012, ...)')
    p.add_argument('-e', '--everything', dest='everything',
            default=False, action='store_true',
            help='Create plots for all detector configurations')
    args = p.parse_args()

    if args.everything:
        args.config = [f'IC86-{yy}' for yy in range(2011, 2022)]

    prefix = '/data/user/eschmidt/stability'

    # open I3 good run list 
    file = f'{prefix}/goodrunlist/goodrunslist.txt'
    f = open(file, "r")

    # read data and separate each entry with keyword 'good_tstart'
    data = f.readlines()
    check = sorted([ct for ct, d in enumerate(data) if 'good_tstart' in d])

    # run through each configuration
    for c in args.config:
        # obtain rates
        c_rate = open(f'{prefix}/rates/{c}_rate.txt', "r")
        c_info = c_rate.readlines()
        info = [c[:10] for c in c_info]

        # determine necessary lines for the current configuration
        c_check = sorted([d for d in check if data[d][27:37] in info])
       
        livetime = []
        # run through the configuration's lines
        for r in c_check:
            # check if the run has a null time    
            if data[r+1][25:29] == 'null':
                livetime.append(f'{day} - {run} - null')
                continue
            # obtain start/stop times from list
            start_t = datetime.strptime(data[r][29:46], '%y-%m-%d %H:%M:%S')
            stop_t = datetime.strptime(data[r+1][28:45], '%y-%m-%d %H:%M:%S')

            # calculate livetime for each run in standard time and seconds
            run_time = str(stop_t - start_t)
            run_sec = (stop_t - start_t).seconds
            day = data[r][27:37]
            run = data[r+4][18:24]
            # save information in list
            livetime.append(f'{day} - {run} - {run_time} - {run_sec}')

        # save text file with information
        np.savetxt(f'{prefix}/run_time/runt_{c}.txt', livetime, fmt='%s')  
    f.close()