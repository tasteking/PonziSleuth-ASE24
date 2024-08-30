"""
    get source code from etherscan by contract's address
"""

import requests
import time
import json
import os

api_key = os.getenv('ETHERSCAN_API_KEY')

def getcode(address):
    url = 'https://api.etherscan.io/api?module=contract&action=getsourcecode&address=' + address + '&apikey=' + api_key

    while(True):
        try:
            response = json.loads(requests.post(url).text)
            source_code = response['result'][0]['SourceCode']
            break

        except:
            time.sleep(1)
            continue

    if isinstance(source_code, str):
        if source_code.startswith('{{'):
            std =  source_code.replace('{{', '{').replace('}}', '}')
            return list(json.loads(std)['sources'].values())[0]['content']

        else:
            return source_code

    else:
        return source_code['source'].values()[0]['content']
