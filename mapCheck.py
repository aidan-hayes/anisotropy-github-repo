#!/usr/bin/env python

import glob, argparse, re
import healpy as hp
import numpy as np
import matplotlib.pyplot as plt
import itertools
import pandas as pd 
from datetime import datetime
import matplotlib.dates as date 

if __name__ == "__main__":

    p = argparse.ArgumentParser()
    p.add_argument('-c', '--config', dest='config',
            nargs='+',
            help='Detector configuration (IC86-2011, IC86-2012, ...)')
    p.add_argument('--rate', dest='rate',
            default=False, action='store_true',
            help='Plots counts divided by daily livetime (excludes bad runs)')
    p.add_argument('--everything', dest='everything',
            default=False, action='store_true',
            help='Create plots for all detector configurations')
    p.add_argument('-o', '--outdir', dest='outdir',
            default='/data/user/zhardnett/Detector_Check',
            help='Output directory for files')
    p.add_argument('-v', '--verbose', dest='verbose',
            default=False, action='store_true',
            help='Print out count/rate information for each day')
    p.add_argument('-t','--together', dest='together',
             default=False,action='store_true',
            help="Combine two selected configurations and plot them",
                  )
   
    

    args = p.parse_args()

    prefix = '/data/user/fmcnally/anisotropy/maps'
    
    if args.everything:
        args.config = [f'IC86-{yy}' for yy in range(2011, 2022)]

    # obtain livetime from McNally's log
    livetime = '/home/fmcnally/github/stability/livetime'
    times = np.load(f'{livetime}/livetime.npy', allow_pickle=True)
    times = times.item()
    fig, ax = plt.subplots() 
    
    # Iterate over all config and method combinations
    for c in args.config:
        print(f'Working on {c}')

        # obtain dates from configuration
        valid_dates = sorted(times[c])
        rate_lst = []
        # find relevant files
        files = glob.glob(f'{prefix}/{c}/*sid_????-??-??.fits')
        files.sort()

        # initiate variables
        n = []
        nfiles = len(files)
        ## Argument to add all files in dictionary 
   
        x=[]
        
        # go through each file
        for i, f in enumerate(files):
            # Progress tracker if not printing daily counts
            if not args.verbose:
                print(f'Reading file {i} of {nfiles}...', end='\r')
            # read map to get event count (n_i)
            map_i = hp.read_map(f, verbose=0)
            n_i = map_i.sum()
            day = re.split('_|\.', f)[-2]
            # warn if day doesn't have good runs
            if day not in valid_dates:
                print(f'Warning: {day} has no good runs in i3live!')
                continue
           
               
            x += [datetime.strptime(day,"%Y-%m-%d").date()]
                
                 
                
        
           
        
            
           
            # calculate rate if necessary
            if args.rate or args.together:
                n_i /= times[c][day]
            # add rate to list
            n += [n_i]
            # provide n_i if necessary
            if args.verbose:
                print(f'{day} : {n_i}')
            # add information to rate_lst
            rate_lst.append(f'{day} : {n_i}') 
           
       
       
        
        ax.xaxis.set_major_formatter(date.DateFormatter("%Y-%m-%d"))
        locator= date.MonthLocator()
        fmt = date.DateFormatter('%Y-%m')
        plt.plot(n,label=c)
        plt.xticks(rotation = 45) 
        ax.set_xlabel('x-axis', fontsize = 2)
        X=plt.gca().xaxis
        X.set_major_locator(locator)
        X.set_major_formatter(fmt)
        plt.xticks(rotation = 45) 
        plt.ylim(1700,2350)
        plt.show()
        
        
        
    
    plt.xlabel('Time (Months)' )
    plt.ylabel('Rate (events per second)')
    plt.legend()
    plt.title("Rate Configurations ")    


        # save information to text files
    out = f'{args.outdir}/Map_Check/{c}_nEvents.txt'
    if args.rate:
        out = out.replace('_nEvents.txt', '_rate.txt')
    np.savetxt(out, np.array(rate_lst), fmt='%s')   
       
  
          
    #save plot to png file (keep outside the for loop :') )

    out = f'{args.outdir}/Map_Check/_{c}.png'
    plt.savefig(out)
    if args.together:
        out = out.replace('.png', '_combine.png')
        plt.savefig(out)

   
    


    


    


