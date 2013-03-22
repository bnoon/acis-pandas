import numpy as np
import urllib2
import json

import pandas as pd
from pandas import DataFrame, Panel

interval_map = dict(dly=(0,0,1), mly=(0,1), yly=(1,))

def check_params(params) :
    single_filter = set(('sid','uid'))
    multi_filter = set(('sids','uids','state','county','climdiv','huc','cwa','bbox'))
    errors, options = [], {}
    p_dict = dict([(k.lower(),v) for k,v in params.items()])
    p_keys = set(p_dict.keys())
    
    # check that station selection is set
    if single_filter & p_keys : multi = False
    elif multi_filter & p_keys : multi = True
    else : errors.append('must select stations')
    options['multi'] = multi
    
    # date range
    if 'date' in p_keys :
        sdate = edate = p_dict['date']
        options['one_date'] = True
    elif len(set(('sdate','edate')) & p_keys) == 2 :
        sdate, edate = p_dict['sdate'], p_dict['edate']
    else :
        errors.append('Missing date range')
    
    if 'elems' in p_keys :
        def parse_interval(yr,mn=0,dy=0) :
            if dy > 0 :
                if yr+mn > 0 : raise ValueError()
                if dy > 1 : return '%dD'%(dy)
                return 'D'
            if mn > 0 :
                if yr > 0 : return '%dM'%(yr*12 + mn)
                elif mn > 1 : return '%dM'%(mn)
                return 'M'
            else :
                if yr > 1 : return '%dA'%(yr)
                return 'A'
        if isinstance(p_dict['elems'], basestring) :
            base_ts = 'D'
        else :
            base_ts = None
            for e_idx, elem in enumerate(p_dict['elems']) :
                need_reduce = False
                e_interval = elem.get('interval','dly')
                if isinstance(e_interval,basestring) and e_interval in interval_map :
                    e_interval = interval_map[e_interval]

                if not isinstance(e_interval,(list,tuple)) :
                    errors.append('Invalid interval elem_%d'%(e_idx))
                    continue
                try :
                    e_ts = parse_interval(*e_interval)
                except (ValueError, TypeError) :
                    errors.append('Invalid interval elem_%d'%(e_idx))
                    continue
                if base_ts is None : base_ts = e_ts
                elif base_ts != e_ts :
                    errors.append('All elems must use the same interval')
                    break
    else : errors.append('Missing elems')
    options['date_freq'] = base_ts
    
    if errors : raise ValueError('\n'.join(errors))
    return p_dict, options
    
def make_request(params, multi) :
    api_name = 'MultiStnData' if multi else 'StnData'
    req = urllib2.Request('http://data.rcc-acis.org/'+api_name,
        json.dumps(params),
        {'Content-Type':'application/json'})
    try :
        response = urllib2.urlopen(req)
    except urllib2.HTTPError as e :
        if e.code == 400 and e.msg == 'Bad Request' :
            raise ValueError('Invalid parameters')
        raise
    return json.loads(response.read())

def make_labels(elems) :
    labels = []
    counts = {}
    if isinstance(elems,basestring) :
        elems = elems.split(',')
    for elem in elems :
        if isinstance(elem,basestring) :
            name = elem
        elif isinstance(elem,int) :
            name = str(elem)
        elif isinstance(elem,dict) :
            if 'label' in elem : name = elem.pop('label')
            elif 'name' in elem : name = elem['name']
            elif 'vX' in elem : name = str(elem['vX'])
            else : name = 'elem'
        else : raise ValueError("Invalid elem in elems")
        cnt = counts.setdefault(name,0)
        if cnt == 0 : labels.append(name)
        else : labels.append('%s_%d'%(name,cnt))
        counts[name] += 1
    return labels

def ACISLoader(**params) :
    # validate params
    #   validate elems
    #   calculate timeseries
    cvt_missing = params.pop('missing','M')
    cvt_trace = params.pop('trace','T')
    cvt_subseq = params.pop('subseq','S')
    if 'accum' in params :
        if params['accum'] == True : cvt_accum = lambda a : float(a[:-1])
        else : cvt_accum = lambda a : params['accum']
    p_dict, options = check_params(params)
    columns = make_labels(p_dict['elems'])
    raw = make_request(p_dict, options['multi'])
    
    if 'error' in raw : raise TypeError(raw['error'])
    
    if options['multi'] :
        sdate = p_dict.get('sdate',p_dict['date'])
        if isinstance(sdate,(list,tuple)) : sdate = '-'.join(map(str,sdate))
        raw, datum_slice = raw['data'], slice(0,None)
    else :
        sdate = raw['data'][0][0]
        raw, datum_slice = [raw], slice(1,None)

    all_data, all_meta = {},{}

    dates = None
    one_date = 'one_date' in options
    for stn_raw in raw :
        stn_data = dict([(key,[]) for key in columns])
        meta = stn_raw['meta']
        sid = meta['sids'][0].split(' ')[0]
        if one_date : raw_data = [stn_raw['data']]
        else : raw_data = stn_raw['data']
        if dates is None :
            dates = pd.date_range(sdate,periods=len(raw_data),freq=options['date_freq'])
        for datum in raw_data :
            for i,e in enumerate(datum[datum_slice]) :
                try :
                    stn_data[columns[i]].append(float(e))
                except ValueError :
                    if e == 'M' : stn_data[columns[i]].append(cvt_missing)
                    elif e == 'T' : stn_data[columns[i]].append(cvt_trace)
                    elif e == 'S' : stn_data[columns[i]].append(cvt_subseq)
                    elif e.endswith('A') : stn_data[columns[i]].append(cvt_accum(e))
                    else : stn_data[columns[i]].append(e)
        df = DataFrame(stn_data, index=dates)
        all_data[sid] = df
        all_meta[sid] = meta
    panel = Panel.from_dict(all_data)
    # Make a pd.DataFrame for meta
    # Indexed by first ID in sids. Should uid be used?
    sids = [k for k in all_meta]
    panel.meta = DataFrame([all_meta[k] for k in sids], index=sids)

    return panel

