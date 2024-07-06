import uvicorn
import json
import os
import logging
import traceback
from tqdm import tqdm

from fastapi import FastAPI
from pydantic import BaseModel

import pandas as pd
from langchain_community.document_loaders import Docx2txtLoader

import openai

with open('config.json', 'r') as f:
        conf = json.load(f) 
 
log = logging.getLogger("uvicorn.error")

openai.api_type = conf["openai.api_type"]
openai.api_key = conf["openai.api_key"]
openai.api_base = conf["openai.api_base"]
openai.api_version = conf["openai.api_version"]
deployment_id = conf["deployment_id"]
model = conf["model"]
port = conf["port"]

doc_promt_template = """Here is the contract text containing various terms and constraints for work execution (e.g., budget constraints, types of allowable work, etc.).
Extract all key terms from the contract and structure them in a JSON format. 
Terms may be related to different sections and subsections of the contract, which should be reflected in your JSON.
Respond only with a JSON message.
Contract text:
"""

csv_prompt_template = """You have task descriptions and cost.
You have key contract conditions in JSON format.
Please analyze task descriptions and costs for compliance with the contract conditions. 
If the task description or task cost violates one or more conditions, specify condition and the reason for the violation.
If it is unclear from the task description whether it may contradict the contract terms, ask clarifying question.
    
task descriptions and costs in list of dicts format: {task_descriptions}
contract terms in JSON format: {conditions}

Answer in JSON format - dict of tasks of dict of contradicted contract conditions with reasons of contradiction or clarifying question. Respond only with a JSON message.
"""

class RequestItem(BaseModel):
    results_dir: str
    contract_path: str
    csv_path: str


app = FastAPI(version="1.0")


@app.post('/',)
def post_request(request: RequestItem):
    data = request.dict()
    contract_path = data['contract_path']
    csv_path = data['csv_path']
    results_dir = data['results_dir']
    result_json_path = os.path.join(results_dir, "contract_terms.json")
    result_csv_path = os.path.join(results_dir, "csv_analysis.json")
    
    loader = Docx2txtLoader(contract_path)
    
    data = loader.load()
    content = data[0].page_content
    
    prompt = f'{doc_promt_template}\n{content}'
    
    result = {}
    
    result['json'] = result_json_path
    result['status'] = 'OK'
    
    try:
        chat_completion = openai.ChatCompletion.create(deployment_id=deployment_id, 
                                                       model=model, 
                                                       messages=[{"role": "user", "content": prompt}])
        conditions = chat_completion.choices[0].message.content
        jsn = json.loads(conditions)
        with open(result_json_path, 'w', encoding ='utf8') as json_file:
            json.dump(jsn, json_file, ensure_ascii = True, indent=4)        
    except Exception as e:
        log.error(str(e))
        log.error(traceback.format_exc())
        result['status'] = 'ERROR'
        result['json'] = str(e)

    try:
        file_type = csv_path.split('.')[-1].lower()
        if file_type in {'xls', 'xlsx'}:
            df = pd.read_excel(csv_path)
        else:
            df = pd.read_csv(csv_path)
        df['Task Description']
        df['Amount']
    except Exception as e:
        log.error(str(e))
        log.error(traceback.format_exc())
        result['csv'] = 'ERROR:' + str(e)
        return json.dumps(result) 

    task_descriptions = [{"task description": row['Task Description'], "cost": row['Amount']} for _, row in df.iterrows()]
    prompt = csv_prompt_template.format(**{'task_descriptions': task_descriptions,
                                           'conditions': conditions})
    try:
        chat_completion = openai.ChatCompletion.create(deployment_id=deployment_id, 
                                                       model=model, 
                                                       messages=[{"role": "user", "content": prompt}])
        jsn = chat_completion.choices[0].message.content
        jsn = json.loads(jsn)
        with open(result_csv_path, 'w', encoding ='utf8') as json_file:
            json.dump(jsn, json_file, ensure_ascii = True, indent=4)        
    except Exception as e:
        log.error(str(e))
        log.error(traceback.format_exc())
        result['status'] = 'OK'
        result['csv'] = str(e)
        return json.dumps(result)

    result['csv'] = result_csv_path
    return json.dumps(result)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", log_level='trace', port=port, workers=3)