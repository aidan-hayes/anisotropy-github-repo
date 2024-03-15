import numpy as np 
import matplotlib.pyplot as pt 
import shutil 
import glob, argparse, re
# Using text files from combine.py to double check the good and bad runs. 
if __name__== '__main__':
    p= argparse.ArgumentParser()
    p.add_argument('--choose', dest='choose',
        nargs='+',
        help= 'Chooses from selected rate files')
    p.add_argument('-f', '--file', dest='file',
        default='/data/user/zhardnett/',
        help='Output directory for files')
    args = p.parse_args()
    for choose in args.choose:
        # maybe /*2021* 
        ind_runs=[]
        miss_runs=[]
        arr=np.loadtxt(fname=f'IC86-{choose}_summary.txt', dtype=str, delimiter= '         -         -          - ')
        
        time=[date for date in arr if date.startswith('20') ]
        for i , dates in enumerate(time, start=1):
            ind_runs=arr[i:i+1]
            print(*ind_runs)
       
                
        



    #print( *time.index, sep="\n")
    #time_diff=[t for t in arr if t.endswith('root')]
        
        
       
    """
    # for checking plots 
   # def find_missing(): # add runs :
        #max = runs[0]
        #for i in run:
           # if i> max:
              #  max = i

       # min = run[0]
        #for i in run:
       # if i < min:
            #min  = i 
            missing = max +1 
            miss_runs=[]
        for v in run:
            max=max-1
            if max not in run:
                miss_runs.append(max)

    return miss_runs

    runs=[] #enter list 
    print('You Have Missing Runs. These Runs Are :',find_missing())
    print('Double Check Summary List :)')


    # ALso make notice of of time between livetime and root files  
"""




