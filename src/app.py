#!/usr/bin/env python3
from flask import Flask, request
import json
import csv
from jobs import rd, q, add_job, get_job_by_id
app = Flask(__name__)
eq_data = {'all_month':[]}

@app.route('/data', methods=['POST', 'GET'])
def download_data():
    '''
    loads the data to dictionary of list of dict (easier to work w flask than list)
    returns json-formatted
    '''
    global eq_data
    
    if request.method == 'POST':
        rd.flushdb()

        with open('all_month.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                eq_data['all_month'].append(dict(row))
            
        for item in eq_data['all_month']:
            rd.hset(item['id'], mapping = item)

        return 'Data has been loaded.\n'

    elif request.method == 'GET':
        
        eq_list = []
        
        for item in rd.keys():
            eq_list.append(rd.hgetall(item))
        
        return (json.dumps(eq_list, indent = 2) + '\n')

    else:
        return "Only supports POST and GET methods.\n"

@app.route('/feature/<feat_string>', methods=['GET'])
def specific_feature(feat_string: str):
    '''
    prints a given feature for all earthquakes
    we probably should make these return lists/strings/dicts in the future
    '''
    string_list = []
    for item in rd.keys():
        string_list.append('[ID ' + rd.hget(item, 'id') + ']: ' + rd.hget(item, feat_string))
    return(f'All Earthquake {feat_string}s\n' + json.dumps(string_list, indent = 1)+ '\n')

@app.route('/earthquake/<id_num>', methods=['GET'])
def specific_earthquake(id_num: str):
    '''
    prints all info abt a specific earthquake given # index
    really we should do one by ID maybe?
    '''
    for item in rd.keys():
        if rd.hget(item, 'id') == id_num:
            return(f'Earthquake {id_num}\n' + json.dumps(rd.hgetall(item), indent = 1) + '\n')

@app.route('/magnitude/<mag>', methods=['GET'])
def big_earthquake(mag: int):
    '''
    prints earthquakes above some given magnitude
    '''
    magnitude_list = []
    for item in rd.keys():
        if float(rd.hget(item, 'mag')) >= int(mag):
            magnitude_list.append('[ID ' + rd.hget(item, 'id') + ']: ' + rd.hget(item, 'mag'))
    return(f'Magnitudes above {mag}\n' + json.dumps(magnitude_list, indent = 1) + '\n')

@app.route('/delete/<id_num>', methods =['DELETE'])
def delete_feature(id_num: str):
    feature_list = []
    for item in rd.keys():
        if rd.hget(item, 'id') == id_num:
            rd.delete(item)
            return (f'Earthquake {id_num} DELETED.\n')

@app.route('/update/<id_num>/<feature_string>/<new_value>', methods =['UPDATE'])
def update_feature(id_num: str, feature_string:str, new_value:str):
    feature_list = []
    for item in rd.keys():
        if rd.hget(item, 'id') == id_num:
            rd.hset(item, feature_string, new_value)
            return (f'Earthquake {id_num}-> {feature_string} UPDATED to {new_value}.\n')

@app.route('/jobs', methods=['POST', 'GET'])
def jobs_api():
    """
    API route for creating a new job to do some analysis. This route accepts a JSON payload
    describing the job to be created.
    """
    if request.method == 'POST':
        try:
            job = request.get_json(force=True)
        except Exception as e:
            return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})
    
        return json.dumps(add_job(job['start'], job['end']), indent=2) + '\n'

    elif request.method == 'GET':
        return """
  To submit a job, do the following:
  curl localhost:5028/jobs -X POST -d '{"start":1, "end":2}' -H "Content-Type: application/json"
"""

@app.route('/jobs/<job_uuid>', methods=['GET'])
def get_job_result(job_uuid):
    """
    API route for checking on the status of a submitted job
    """
    return json.dumps(get_job_by_id(job_uuid), indent=2) + '\n'



if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')
