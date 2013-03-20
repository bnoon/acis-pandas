import pandas as pd
from ACISLoader import ACISLoader

data = ACISLoader(
    state=['DE','NJ'],
    date='20120101',
    elems='mint,maxt,pcpn')

for stn in data.items :
    print stn,data[stn].to_string(header=False)
