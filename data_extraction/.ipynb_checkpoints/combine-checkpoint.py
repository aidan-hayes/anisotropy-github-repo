#!/usr/bin/env python


####################################################################
###    Time consuming (10min) code that takes multiple elements  ###
###    and combines them into summarized data. These elements    ###
###    include fits files, I3 livetime, root files,              ###
###    and I3 good run list. Before running this script,         ###
###    you need to create [config]_rate.txt and                  ###
###    sum_[config]_[day].txt. These txt files can be            ###
###    obtained through day_submitter.py and mapCheck.py.        ###
####################################################################


import numpy as np
import glob
import re
import healpy as hp
from datetime import datetime, time

# File locations
prefix = '/data/user/eschmidt/stability'  
files = sorted(glob.glob(f'{prefix}/summarized_days/*.txt'))
configs = sorted(set([re.findall('IC86-\d{4}', f)[-1] for f in files]))

# find bad runs from good run list
print('finding bad run list')

# list/dictionary initation
badruns = []
livetime = {}

# open I3 good run list 
file = f'{prefix}/goodrunlist/goodrunslist.txt'
f = open(file, "r")

# read data and separate each entry with keyword 'good_i3'
data = f.readlines()
check = sorted([ct for ct, d in enumerate(data) if 'good_i3' in d])

# go through each entry to determine whether they are good or bad runs
for r in check:
    # instate each day as a key for the dictionary
    day = data[r+2][27:37]
    if day not in livetime.keys():
        livetime[day] = {}
    # determine if a day's run if good/bad
    run = data[r+6][18:24]
    if data[r][22:-2] == 'false' or data[r+1][22:-2] == 'false':
        badruns.append(run)
    # set livetime to null if not calculatable
    if data[r+3][25:29] == 'null':
        livetime[day][run] = 'null'
        continue
    # obtain start/stop times from list
    start_t = datetime.strptime(data[r+2][29:46], '%y-%m-%d %H:%M:%S')
    stop_t = datetime.strptime(data[r+3][28:45], '%y-%m-%d %H:%M:%S')
    # check if run crosses over a day and create appropriate run times
    if start_t.day != stop_t.day:
        day_aft = data[r+3][26:36]
        livetime[day_aft] = {}
        midnight = datetime.combine(stop_t, time.min)
        run_sec_prev = (midnight - start_t).seconds
        run_sec_aft = (stop_t - midnight).seconds
        livetime[day][run] = run_sec_prev
        livetime[day_aft][run] = run_sec_aft
    # calculate run time for day 
    else:
        run_sec = (stop_t - start_t).seconds
        livetime[day][run] = run_sec
# organize badruns into reasonable list
badruns = sorted(set(badruns))
f.close()

# find bad days in fits files
print('finding bad days in fits')

# initiate lists
bad_avg = []
under_bad_avg = ['Under Average']
over_bad_avg = ['Over Average']

# run through each configurations to find bad days
for c in configs[1:]:
    under_bad_avg.append(c)
    over_bad_avg.append(c)
    # open rates file for the config
    file = f'{prefix}/rates/{c}_rate.txt'
    f = open(file, "r")
    data = f.readlines()
    # find comparison # by averaging first 7 days
    comp = np.average([float(data[x][13:][:-1]) for x in range(7)])
    for ct, day in enumerate(data):
        # obtain rate for each day
        rate = float(day[13:][:-1])
        # compare rate to see if it is above average
        if rate >= 1.05*comp:
            # for first 5 days, remove rate from comparison to improve comparison #
            if ct < 6:
                comp = ((ct + 7)*comp - rate) / (6 - float(ct))
            over_bad_avg.append(day[:10])
            bad_avg.append(day[:10])
            continue
        # compare rate to see if it is below average
        if rate <= 0.95*comp:
            # for first 5 days, remove rate from comparison to improve comparison #
            if ct < 6:
                comp = ((ct + 7)*comp - rate) / (6 - float(ct))
            under_bad_avg.append(day[:10])
            bad_avg.append(day[:10])
            continue
        # include rate in comparison for rolling average
        comp = (4*comp + rate) / 5
    f.close()  
    
# find nEvents and livetime for each day
print('finding livetime and nEvents in fits')
# obtain livetime for McNally's .npy file
fm_livetime = '/home/fmcnally/github/stability/livetime'
times = np.load(f'{fm_livetime}/livetime.npy', allow_pickle=True)
times = times.item()
fm_prefix = '/data/user/fmcnally/anisotropy/maps'
fits_data = {}

# run through each configuration
for c in configs:
    # Find the necessary dates for config
    valid_dates = sorted(times[c])
    rate_lst = []
    # Retrieve fits files
    fits_files = glob.glob(f'{fm_prefix}/{c}/*sid_????-??-??.fits')
    fits_files.sort()
    n = {}
    nfiles = len(fits_files)
    
    # run through each fits file
    for i, f in enumerate(fits_files):
        # read fits file
        map_i = hp.read_map(f, verbose=0)
        day = re.split('_|\.', f)[-2]
        # check for valid date
        if day not in valid_dates:
            print(f'Warning: {day} has no good runs in i3live!')
            continue
        # save information in dictionary
        n[day] = {'nEvents': map_i.sum(), 'livetime':times[c][day]}
    # save config data in fits_data
    fits_data[c] = n
    
# find nEvents and livetime for each root file
print('finding livetime and nEvents in root files')
year_data = {}
# run through config
for c in configs:
    data = []
    # find necessary config files
    cfg_files = sorted([f for f in files if c in f])
    # create data list from all config files
    for file in cfg_files:
        f = open(file, "r")
        data.append(f.readlines())
    # obtain relevant data by dividing up the lines
    data = [l[:-1].split(' - ') for line in data for l in line]
    day_data = {}
    for d in data: 
        # create days as keys in day_data
        if d[0] not in day_data.keys():
            day_data[d[0]] = {}
        # create run as keys in days
        if d[1] not in day_data[d[0]].keys():
            day_data[d[0]][d[1]] = {'nEvents' : d[2], 'livetime': d[3], 'g/b': 'g'}
        # combine livetime and nEvents for runs already in data
        else:
            day_data[d[0]][d[1]]['nEvents'] += d[2]
            day_data[d[0]][d[1]]['livetime'] += d[3]
        # note if run is bad
        if d[1] in badruns:
            day_data[d[0]][d[1]]['g/b'] = 'b'
    # include config info in year_data
    year_data[c] = day_data

# finalize list and day/run descriptions
print('finalizing list')
# create header for text
bad_info = ['\run - good/bad - livetime(fits) - livetime(root) - nEvents - rate']

# work through under/over_bad_avg separately
for comparison in [under_bad_avg, over_bad_avg]:
    
    # note what it is running over
    bad_info.extend(['',comparison[0]])
    # run through each day in under/over_bad_avg
    for day in comparison[1:]:
        # instate variables
        day_info = []
        run_day = 0
        n_day = 0
        # note if element is a new configuration
        if day in configs:
            config = day
            bad_info.extend(['', config])
            print(f'formatting {config}')
            continue
            
        # note if element doesn't have fits data
        if day not in fits_data[config].keys():
            print(f'Warning: {day} has no fits files')
            continue
        # obtain day's information
        bad_info.append(day)
        run_fits = int(fits_data[config][day]['livetime'])
        n_fits = int(fits_data[config][day]['nEvents'])
        # make and add fit's information into easily read text
        day_info.append(f'\t{"fits":<7} - {run_fits:<7} - {n_fits:<11} - {n_fits / run_fits}')
        
        # note if element doesn't have root data
        if day not in year_data[config].keys():
            print(f'Warning: {day} has no data files')
            continue
        # collect each day's multiple run information
        for key, value in year_data[config][day].items():
            run_fits = livetime[day][key]
            run_root = int(value['livetime'])
            n_root = int(value['nEvents'])
            run_day += run_root
            n_day += n_root
            # make run's information into easily read text
            day_info.append(f'\t{key}{value["g/b"]} - {run_fits:<7} - {run_root:<7} - {n_root:<11} - {n_root / run_root}')
        # add summarized root data into text
        bad_info.append(f'\t{"root":<7} - {run_day:<7} - {n_day:<11} - {n_day / run_day}')
        # add each run's data into text
        bad_info.extend(day_info)
        
# save text in summary text file
out = f'/data/user/ahayes/bad_days.txt'
np.savetxt(out, bad_info, fmt='%s') 

# separate into configurations
# repeat summarized data for all days in a config
print('analyzing configurations')

# run through each config
for c in configs:
    # create header for configuration text
    config_info = ['\trun(good/bad) - livetime(fits) - livetime(root) - nEvents - rate']
    
    # run through root information
    for day, value in year_data[c].items():
        # instate variables
        day_info = []
        run_day = 0
        n_day = 0
        
        # note if element doesn't have fits data
        if day not in fits_data[c].keys():
            print(f'Warning: {day} has no fits files')
            continue
        # obtain day's information
        config_info.append(day)
        run_fits = int(fits_data[c][day]['livetime'])
        n_fits = int(fits_data[c][day]['nEvents'])
        day_info.append(f'\t{"fits":<7} - {run_fits:<7} - {n_fits:<11} - {n_fits / run_fits}')
        
        # note if element doesn't have root data
        if day not in year_data[c].keys():
            print(f'Warning: {day} has no data files')
            continue
        # collect each day's multiple run information
        for runs, info in value.items():
            # Note if run is not in root files
            if runs not in livetime[day].keys():
                run_fits = 'N/A'
            else:
                run_fits = livetime[day][runs]
            run_root = int(info['livetime'])
            n_root = int(info['nEvents'])
            run_day += run_root
            n_day += n_root
            # make run's information into easily read text
            day_info.append(f'\t{runs}{info["g/b"]} - {run_fits:<7} - {run_root:<7} - {n_root:<11} - {n_root / run_root}')
        # add summarized root data into text
        config_info.append(f'\t{"root":<7} - {run_day:<7} - {n_day:<11} - {n_day / run_day}')
        # add each run's data into text
        config_info.extend(day_info)
    # save text in summary text file
    out = f'/data/user/ahayes/{c}_summary.txt'
    np.savetxt(out, config_info, fmt='%s') 
print('all done!')

'''
# relay more information about days
# find days in multiple configurations
print('finding cheating days')
cheats = []
cheat_day = []
# huge for loop that can be shortened but haven't gotten to yet
# will repeat days due to going through configs twice
for c in configs:
    for day, value in year_data[c].items():
        for con in configs:
            # Note if day is in multiple configs
            if day in year_data[con].keys() and c != con:
                cheat_day.append(f'{day} - {c} - {con}')
                for run in value.keys():
                    # Note if run is in multiple configs
                    if run in year_data[con][day].keys():
                        cheats.append(f'{run} - {day} - {c} - {con}')
print(cheats)
print(cheat_day)
'''

# relay more information about days
# find days in multiple configurations
# attempt to fix previous cheat code
configurations = configs
cheats = []
cheat_day = []
for c in configs:
    for day, value in fits_data[c].items():
        for con in configurations:
            # Note if day is in multiple configs
            if day in fits_data[con].keys() and c != con:
                cheat_day.append(f'{day} - {c} - {con}')
                for run in value.keys():
                    # Note if run is in multiple configs
                    if run in fits_data[con][day].keys():
                        cheats.append(f'{run} - {day} - {c} - {con}')
    configurations = configurations[1:]
    
print(cheats)
print(cheat_day)
print('all done!')