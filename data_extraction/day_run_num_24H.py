#!/usr/bin/env python
import argparse
import numpy as np
import ROOT

# Super complicated calculation to convert MJD time to yr-month-day
def conv_MJD(day):
    q = float(day)+2400001
    w = int((q - 1867216.25) / 36524.25)
    x = int(w/4)
    b = int(q+1+w-x+1524)
    c = int((b-122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b-d) / 30.6001)
    f = int(30.6001 * e)
    day = int(b - d - f)
    if day < 10:
        day = f'0{day}'
    month = int(e - 1)
    if month > 12:
        month -= 12
    if month < 10:
        month = f'0{int(month)}'
    year = c - 4716
    if month == '01' or month == '02':
        year += 1
    return(f'{int(year)}-{month}-{day}')


if __name__ == "__main__":

    p = argparse.ArgumentParser(
            description='Finds the number of events in each run of a detector year')
    p.add_argument('-i', '--infiles', dest='infiles',
            nargs='+',
            help='File(s) to retrieve the information from')
    p.add_argument('-o', '--out', dest='out',
            help='Name of output text file to store info')
    p.add_argument('-y', '--year', dest='year',
            type=int, default=2015,
            help='Detector season (e.g., 2011 = IC86-2011)')
    args = p.parse_args()

    # Collect all files from specified year
    prefix = '/data/ana/CosmicRay/Anisotropy/IceCube'

    run_nums = []
    file_dict = {}
    
    # Run through each input file
    for infile in args.infiles:

        # Open root file and retrieve nEvents
        f = ROOT.TFile(infile)
        t = f.CutDST
        rootEvents = t.GetEntries()  

        print('obtaining events now')

        # run through each event
        for i in range(rootEvents):
            t.GetEntry(i)
            # note day, run, and time
            date = int(t.ModJulDay)
            run = t.RunId
            time = t.ModJulDay
            # use days as keys in file's dictionary
            if date not in file_dict.keys():
                file_dict[date] = {}
            # use run # as keys in day's dictionary 
            if run not in file_dict[date].keys():
                file_dict[date][run] = {'nEvents' : 0, 'max_time': time, 'min_time': time}
            # count each Event per run
            file_dict[date][run]['nEvents'] += 1
            # compare event time to min/max time to determine run's min/max time
            if time > file_dict[date][run]['max_time']:
                file_dict[date][run]['max_time'] = time
            if time < file_dict[date][run]['min_time']:
                file_dict[date][run]['min_time'] = time
                
    day_info = []
    # interate through dictionary to calculate livetime, nEvents, and day
    for d, r in file_dict.items():
        for runs, info in file_dict[d].items():
            livetime = (info["max_time"] - info["min_time"])*86400
            day_info.append(f'{conv_MJD(d)} - {runs} - {info["nEvents"]} - {int(livetime)}')
            #livetime = (file_dict[date][runs]["max_time"] - file_dict[date][runs]["min_time"])*86400
            #day_info.append(f'{conv_MJD(d)} - {runs} - {file_dict[d][runs]["nEvents"]} - {int(livetime)}')
    # save information in text file
    np.savetxt(args.out, day_info, fmt='%s')
    