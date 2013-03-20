import pandas as pd
from ACISLoader import ACISLoader

monthly_data = ACISLoader(
    sid='304174',sdate='2012-01',edate='2012-12',
    elems=[
        dict(name='mint',interval='mly',reduce='mean'),
        dict(name='maxt',interval='mly',reduce='mean'),
        dict(name='pcpn',interval='mly',reduce='sum'),
        ],
    )

print monthly_data['304174'].to_string()
