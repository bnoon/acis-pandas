import pandas as pd
from ACISLoader import ACISLoader

daily_data = ACISLoader(
    sid='304174',sdate='20120101',edate='20120131',
    elems='mint,maxt,pcpn')

print daily_data['304174'].to_string()
