import solcx.version
from web3 import Web3

from web3.contract.contract import Contract

from solc_select.solc_select import(
    install_artifacts,
    installed_versions,
    switch_global_version
)

import os
import json
import time
import regex
import solcx
import argparse
import ContractAnalyzer
import TransactionSequenceGeneration

def cli_args():
    parser = argparse.ArgumentParser(
        description='help',
        usage='\n  input sol file dir path'
    )

    parser.add_argument(
        '-p', '--path',
        type=str,
        help='Sol file dir path'
    )

    return parser.parse_args()

def compare_version(version_1, version_2):
    v1 = version_1.split('.')
    v2 = version_2.split('.')
    if int(v1[1]) > int(v2[1]):
        return version_1
    elif int(v1[1]) == int(v2[1]) and int(v1[2]) > int(v2[2]):
        return version_1
    else:
        return version_2

def get_solc_version(code):
    min_version = '0.4.11'
    try:
        versions = regex.finditer(r'pragma\ssolidity\s*\D*(\d+\.\d+\.\d+)', code)
    except:
        print('use minimum version that works')
        return min_version

    for version in versions:
        min_version = compare_version(min_version, version.groups()[0])

    return min_version

def deploy(filename: str, file_path: str, w3: Web3):
    try:
        with open(file_path) as f:
            text = f.read()
        
        version = get_solc_version(text)
        if not version in installed_versions():
            install_artifacts(version)
        
        switch_global_version(version, True)

        if not version in [v.public for v in solcx.get_installed_solc_versions()]:
            solcx.install_solc(version)

        constructor = TransactionSequenceGeneration.getTransactionSequence(filename, ContractAnalyzer.analyze_contract(file_path), 3)

        contract_id, contract_interface = solcx.compile_files(
            source_files = file_path,
            output_values = ['abi', 'bin'],
            solc_version = version
        ).popitem()
        with open(filename + '.abi', "w") as f:
            f.write(json.dumps(contract_interface['abi'], indent=4))
        
        tx_hash = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin']).constructor(**constructor['randomParameterValues']).transact({'from': w3.eth.default_account, 'gas': 10000000})

        return tx_hash, contract_interface['abi']
    
    except Exception as e:
        print(e)
        return False

if __name__ == '__main__':
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    args = cli_args()
    path: str = args.path
    with open('path_to_json', 'r') as f:
        addr_contract: dict = json.loads(f.read())

    if w3.is_connected():
        # account that send tx
        account = w3.eth.accounts[0]

        print('------ test net has been connected ------')
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            prefix = filename.split('.')[0]
            tx_hash, abi = deploy(prefix, file_path, w3)
            time.sleep(2)
            try:
                address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
                print(f' ------ Deploy Done ------\nDeployed from {w3.eth.default_account} to: {address}')
                with open('/root/contract.json', 'w') as f:
                    addr_contract[prefix] = {'address': address, 'txn': []}
                    f.write(json.dumps(addr_contract, indent=4))

                # example of sending tx

                # contract: Contract = w3.eth.contract(address=address, abi=abi)
                # tx = contract.functions[name_of_method_to_call](*args_of_method).transact({'from': account, 'gas': 2000000, 'gasPrice': '10000000'})

                ############ send tx zone ############
                contract = w3.eth.contract(address=address, abi=abi)
                # load and build tx args
                with open(f"{prefix}.json", "r") as f:
                    tranSeq = json.loads(f.read())[prefix]

                for seq in tranSeq:
                    for tranItem in seq:
                        # full_name = tranItem["full_name"]
                        name = tranItem['name']
                        params = tranItem['parameters']
                        randomValueArray = [tranItem['randomParameterValues'][k] for k in params]

                        if tranItem['payable']:
                            caller = {
                                'from': account,
                                'value': tranItem['value'],
                                'gas': 2000000,
                                'gasPrice': '10000000'
                            }
                            tx_hash = contract.functions[name](**randomValueArray).transact(caller)
                        
                        else:
                            caller = {
                                'from': account,
                                'gas': 2000000,
                                'gasPrice': '10000000'
                            }
                            tx_hash = contract.functions[name](**randomValueArray).transact(caller)
                    
                        with open('/root/contract.json', 'w') as f:
                            addr_contract[prefix]['txn'].append(tx_hash)
                            f.write(json.dumps(addr_contract, indent=4))

                        time.sleep(1)

            except Exception as e:
                print(' ------ Deploy Fail ------ ')
                print(e.args[0])

    else:
        print('------ test net connecting failed ------')