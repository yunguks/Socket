import cv2
import sys
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

def find_bin(list_k):
    keys = list(list_k.keys())
    #print(f'keys = {keys}')
    
    key_max = round(np.max(keys),1)
    key_min = round(np.min(keys),1)
    #print(f'max = {key_max}, min = {key_min}')
    
    bin = int((key_max-key_min)*10)
    return bin

def upper(k,upper):
    pix_num = sum(k.values())
    upper_number = pix_num-(pix_num*upper/100)
    
    count = 0
    temp = 0
    
    for i in k.keys():
        count +=k[i]
        if upper_number <= count:
            temp = i
            break
    return temp

if __name__=='__main__':
    if len(sys.argv) < 2 and len(sys.argv) > 3:
        print("Usage : lepton_processing.py (experement number) [,(try number)]")
        exit(1)
    dirname = "/home/pi/Socket/images/" + sys.argv[1]

    if sys.argv[1] == '3' or sys.argv[1] == '4':
        if len(sys.argv) != 3:
            print("Expirement 3,4 must need try number")
            exit(1)
        dirname += "/" + sys.argv[2]

    if os.path.isdir(dirname) == False:
        print(dirname,"is not exist")
        exit(1)

    file_list = []
    for file in os.listdir(dirname):
        file_list.append(file[:11])
    file_list = sorted(set(file_list))
    #print(file_list)

    os.chdir(dirname)

    for file in file_list[0:2]:
        csvname = dirname + '/' + file + '_crop.csv'
        filename = file +'_plt.png'
        print(f'csv name : {csvname}')
        #try:
        df = pd.read_csv(csvname,header=None)
        value, counts = np.unique(df,return_counts=True)
        result = dict(zip(value,counts))
        result.pop('0')
        #print(result)
        print(f'number of pixel = {sum(result.values())}')
        print(f'Temperature of 10% : {upper(result,10)}')
        print(f'Temperature of 30% : {upper(result,30)}')
        print(f'Temperature of 50% : {upper(result,50)}')

        bin = find_bin(result)
        plt.figure(figsize=(20,10))
        plt.bar(list(result.keys()),result.values(),width=0.3)
        plt.title("Temperature distribution")
        plt.xlabel('Temperature',fontsize=10)
        plt.ylabel('Count',fontsize=10)
        plt.savefig(filename)
        #except:
        #    print(f'{csvname} is no Exist')