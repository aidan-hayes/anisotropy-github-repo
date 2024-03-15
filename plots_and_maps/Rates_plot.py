import healpy as hp
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as date 
import glob, argparse, re

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--All', dest='All',
        default=False, action='store_true', 
        help='Plots all the rates from given text file')
    p.add_argument('--choose', dest='choose',
        nargs='+',
        help= 'Chooses from selected rate files')
    p.add_argument('-f', '--file', dest='file',
        default='/data/user/zhardnett/',
        help='Output directory for files')
    args = p.parse_args()


    if args.All:
        fig, ax = plt.subplots()
        new_arr=[]
        for all_years in range(2011,2022):
            arr = np.loadtxt(fname=f'IC86-{all_years}_rate.txt' , dtype=str ,delimiter=' : ')
            x=arr[:,0] 
            y=arr[:,1].astype(float) #changes the type
            ydiff=int(all_years)-2011
            new_arr=[]
            for i in x:
                yy=int(i[:4])
                y_shift=yy-ydiff
                i= i.replace(str(yy),str(y_shift))
                new_arr+=[datetime.strptime(i,"%Y-%m-%d").date()]
            ax.plot(y,label=all_years)
        
        ax.xaxis.set_major_formatter(date.DateFormatter("%Y-%m-%d"))
        locator= date.MonthLocator()
        fmt = date.DateFormatter('%m')
        X=plt.gca().xaxis
        X.set_major_locator(locator)
        X.set_major_formatter(fmt)   
        plt.xticks(rotation = 45) 
        plt.ylim(1700,2400)
        plt.xlabel("Time (Months) ")
        plt.ylabel('Rates (events per second)')
        box=ax.get_position()
        ax.set_position([box.x0 , box.y0 , box.width * 0.8, box.height])
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.title("Rate Configurations ")
        file_plot=f'{args.file}/Rates_Comparison from 2011 to 2021.png'
        plt.savefig(file_plot)
            
        
    if args.choose:
        fig, ax = plt.subplots()
        t= np.linspace(0,500,200)
        for choose in args.choose:
            arr = np.loadtxt(fname=f'IC86-{choose}_rate.txt' , dtype=str ,delimiter=' : ')
            x=arr[:,0]
            y=arr[:,1].astype(float) #changes the type
            ydiff=int(choose)-2011
            new_arr=[]
            for i in x:
                yy=int(i[:4])   ###change
                y_shift=yy-ydiff
                i= i.replace(str(yy),str(y_shift))
                new_arr+=[datetime.strptime(i,"%Y-%m-%d").date()]
                
            plt.plot(new_arr,y,label=choose)
           
            
                
       
        ax.xaxis.set_major_formatter(date.DateFormatter("%Y-%m-%d"))
        locator= date.MonthLocator()
        fmt = date.DateFormatter('%m')
        
        X=plt.gca().xaxis
        X.set_major_locator(locator)
        X.set_major_formatter(fmt)
        plt.xticks(rotation = 45) 
        plt.ylim(1700,2350)
        box=ax.get_position()
        ax.set_position([box.x0 , box.y0 , box.width * 0.8, box.height])
        
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
       
        plt.xlabel("Time (Months) ")
        plt.ylabel('Rates (events per second)')
        

        plt.legend()
        plt.title("Rate Configurations ")
        
        file_plot=f'{args.file}/Rates_Comparison_IC86-{choose}.png'
        plt.savefig(file_plot)
        

        #print(new_arr)
            



   
   
