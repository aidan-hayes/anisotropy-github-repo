import shutil
#for count in range(2011,2021):
   # with open(f'IC86-{count}_rate.txt') as infile:
        #for line in infile:
            #print(line)

Yearfiles= [f'IC86-{count}_rate.txt' for count in range(2011,2022)]
with open ('Rates.txt','wb') as main:
    for files in Yearfiles:
        with open(files, 'rb') as others:
            shutil.copyfileobj(others,main)
check = open('Rates.txt','r')
print(check.read())
check.close()
    