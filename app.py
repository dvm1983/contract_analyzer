import streamlit as st
import os
import requests
import json

import time
import random
import socket
import hashlib

import zipfile

random.seed()

def guid():
    t = time.time()*1e3
    r = random.random()*1e10
    try:
        a = socket.gethostbyname(socket.gethostbyname())
    except:
        a = random.random()*1e10
    data = str(t) + ' ' + str(r) + ' ' + str(a)
    data = hashlib.md5(data.encode()).hexdigest()
    return str(data)

uid = guid()

with open('config.json', 'r') as f:
        conf = json.load(f) 
 
tmp_dir = os.path.join(conf["tmpdir"], uid)
os.makedirs(tmp_dir, exist_ok=True)

service = f'http://127.0.0.1:{conf["port"]}'

contract_path = None
csv_path = None

uploaded_files = st.file_uploader("Upload contract and csv file", accept_multiple_files=True)
if len(uploaded_files) != 0:
    for uploaded_file in uploaded_files:
        path = os.path.join(tmp_dir, uploaded_file.name)
        with open(path,"wb") as f:
            f.write(uploaded_file.getbuffer())
            file_type = path.split('.')[-1].lower()
            if file_type in {'csv', 'xls', 'xlsx'}:
                csv_path = path
            elif file_type in {'doc', 'docx'}:
                contract_path = path
            
if st.button("Process files") and contract_path is not None and csv_path is not None:
    
    request_data = {'results_dir': tmp_dir,
                    'contract_path': contract_path, 
                    'csv_path': csv_path}
    request_data = json.dumps(request_data)
    response = requests.post(service, data=request_data).text
    response = json.loads(response)
    response = json.loads(response) 
    result_json_path = response['json']
    result_csv_path = response['csv']
    
    results_zip_path = os.path.join(tmp_dir, 'results.zip')
    with zipfile.ZipFile(results_zip_path, 'w') as myzip:
        for f in [x for x in [result_json_path, result_csv_path] if os.path.exists(x)]:   
            myzip.write(f)
    
    if response['status'] == 'OK':
        with open(results_zip_path, 'rb') as f:
            st.download_button('Download results', f, file_name='results.zip')
        st.write(f"Contract analysis results:")
        with open(result_csv_path, 'r') as f:
            analysis_results = json.load(f)
        st.json(analysis_results)
    else:
        st.write(f"ERROR while processing: {response['json']}")