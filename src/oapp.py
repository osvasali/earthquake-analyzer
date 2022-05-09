#!/usr/bin/env python3
from flask import Flask, render_template, request
import json
import os
import csv
import wget
import numpy as np
import matplotlib.pyplot as plt
import geopandas
import contextily as cx
import pandas as pd

app = Flask(__name__)
eq_data = {'all_month':[]}

@app.route('/help', methods=['GET'])
def help() -> str:
    '''
    Information on how to interact with the application
    Returns: A string describing what paths to use for each function.
    '''
    return '''\nFIRST LOAD DATA USING THE FOLLOWING PATH: /load -X POST\n
    IF THERE ARE ERROR LOAD THE DATA ONCE MORE\n\n
    Navigation:\n
    Use the following routes to access the data:
      1.  /csv/ft/<feat_string>
          #posts data for a specific column in the csv
      2.  /csv/eq/<id_num>
          #posts data from all columns for one earthquake 
      3.  /countries
          #lists all countries
      4.  /csv/mag/<mag>
          #all the earthquakes for a given magnitude \n\n'''

@app.route('/data', methods=['POST', 'GET'])
def download_data():
    '''
    loads the data to dictionary of list of dict (easier to work w flask than list)
    returns json-formatted
    '''
    global eq_data
    #LOADS FROM URL NOW<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    if os.path.exists("all_month.csv"):
        os.remove("all_month.csv")
    
    all_month = wget.download("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv")
    
    if request.method == 'POST':
       # rd.flushdb()

        with open(all_month, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                eq_data['all_month'].append(dict(row))
            
        #for item in eq_data['all_month']:
        #    rd.hset(item['id'], mapping = item)

        return 'Data has been loaded.\n'

    elif request.method == 'GET':
        
        eq_list = []
        
        for item in rd.keys():
            eq_list.append(rd.hgetall(item))
        
        return (json.dumps(eq_list, indent = 2) + '\n')

    else:
        return "Only supports POST and GET methods.\n"

@app.route('/latlong/<err>', methods=['GET'])
def latlong(err: float):
    '''
    loads all_month.csv and extracts coordinates
    returns dictionary
    '''
    xy = {}
    longitude = []
    latitude = []
    #magError = []
    for x in eq_data['all_month']:
        if float(x['magError']) >= float(err):
            longitude.append(x['longitude'])
            latitude.append(x['latitude'])
        #magError.append(x['magError'])
    xy['longitude'] = longitude
    xy['latitude'] = latitude
    #xy['magError'] = magError

    #return (json.dumps(xy, indent = 1) + '\n')
    return xy

@app.route('/points', methods=['GET'])
def poiints():
    df = pd.DataFrame(latlong())
    df_geo = geopandas.GeoDataFrame(df, geometry = geopandas.points_from_xy(df.longitude,df.latitude))
    world_data = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    axis = world_data.plot(color = 'palegoldenrod', edgecolor = 'black')
    df_geo.plot(ax = axis, color = 'maroon', markersize=6, edgecolor='thistle', linewidth=0.1)
    plt.title('Earthquakes')
    plt.savefig('map.png',dpi=600)
    return 'map saved\n\n'



@app.route('/column/<feat_string>', methods=['GET'])
def specific_feature(feat_string: str):
    '''
    prints a given feature for all earthquakes
    we probably should make these return lists/strings/dicts in the future
    '''
    string_list = []
    for x in eq_data['all_month']:
        string_list.append('[ID ' + x['id'] + f']: ' + x[feat_string])
    return(f'All Earthquake {feat_string}s\n' + json.dumps(string_list, indent = 1)+ '\n')

@app.route('/eqid/<id_num>', methods=['GET'])
def specific_earthquake(id_num: str):
    '''
    prints all info abt a specific earthquake given # index
    really we should do one by ID maybe?
    '''
    for x in eq_data['all_month']:
        if x['id'] == id_num:
            return(f'Earthquake {id_num}\n' + json.dumps(x, indent = 1) + '\n')

@app.route('/mag/<mag>', methods=['GET'])
def big_earthquake(mag: int):
    '''
    prints earthquakes above some given magnitude
    '''
    magnitude_list = []
    for x in eq_data['all_month']:
        if float(x['mag']) >= int(mag):
            magnitude_list.append('[ID ' + x['id'] + ']: ' + x['mag'])
    return(f'Magnitudes above {mag}\n' + json.dumps(magnitude_list, indent = 1) + '\n')

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')
