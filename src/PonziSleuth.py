"""
    Workflow
"""

import os
import csv
import json
import time
import llm
import datetime
import argparse

from solc_select.solc_select import(
    install_artifacts,
    installed_versions,
    switch_global_version
)

from crytic_compile import InvalidCompilation, compile_all
from compile_unit import SimplifiedSlither, get_solc_version
from etherscan import getcode

def cli_args():
    parser = argparse.ArgumentParser(
        description='help',
        usage='\n  PonziSleuth -p(-f) /path/to/file(/filename) -m model -t temperature'
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '-f', '--filename',
        type=str,
        help='Sol abs path'
    )

    group.add_argument(
        '-p', '--path',
        type=str,
        help='Sol file dir path'
    )

    group.add_argument(
        '-a', '--address',
        type=str,
        help='Address of contract'
    )

    group.add_argument(
        '-c', '--csv',
        type=str,
        help='Contracts verified by csv'
    )

    parser.add_argument(
        '-g', '--granularity',
        type=str,
        default='function',
        help='Slice granularity'
    )

    parser.add_argument(
        '-m', '--model',
        type=str,
        help='select LLM'
    )

    parser.add_argument(
        '-t', '--temperature',
        type=float,
        default=0.5,
        help='model temperature'
    )

    parser.add_argument(
        '-r', '--raw',
        action='store_true',
        default=False,
        help='Wether slice source code.'
    )

    parser.add_argument(
        '-s', '--single',
        action='store_true',
        default=False,
        help='Wether use two step prompt'
    )

    parser.add_argument(
        '-n', '--number',
        type=int,
        default=0,
        help='Number of contracts to detect'
    )
        
    parser.add_argument(
        '-x', '--repeat',
        type=int,
        default=5,
        help='Repeat times of a same prompt'
    )

    return parser.parse_args()

# parse cli arguments
args = cli_args()
filename: str = args.filename
address: str = args.address
path: str = args.path
csv_path: str = args.csv
granularity: str = args.granularity
abalation: bool = args.raw
prompt: bool = args.single
number: int = args.number
model: str = args.model
temperature: float = args.temperature

if model == 'gpt-3.5-turbo-1106':
    in_rate = 0.001
    out_rate = 0.002

elif model == 'gpt-4-1106-preview':
    in_rate = 0.01
    out_rate = 0.03

else:
    in_rate = 0.0
    out_rate = 0.0

fieldnames = ['address', 'decision', 'time', 'token', 'pay']
versions = ['0.8.24', '0.8.23', '0.8.22', '0.8.21', '0.8.20', '0.8.19', '0.8.18', '0.8.17', '0.8.16', '0.8.15', '0.8.14', '0.8.13', '0.8.12', '0.8.11', '0.8.10', '0.8.9', '0.8.8', '0.8.7', '0.8.6', '0.8.5', '0.8.4', '0.8.3', '0.8.2', '0.8.1', '0.8.0', '0.7.6', '0.7.5', '0.7.4', '0.7.3', '0.7.2', '0.7.1', '0.7.0', '0.6.12', '0.6.11', '0.6.10', '0.6.9', '0.6.8', '0.6.7', '0.6.6', '0.6.5', '0.6.4', '0.6.3', '0.6.2', '0.6.1', '0.6.0', '0.5.17', '0.5.16', '0.5.15', '0.5.14', '0.5.13', '0.5.12', '0.5.11', '0.5.10', '0.5.9', '0.5.8', '0.5.7', '0.5.6', '0.5.5', '0.5.4', '0.5.3', '0.5.2', '0.5.1', '0.5.0', '0.4.26', '0.4.25', '0.4.24', '0.4.23', '0.4.22', '0.4.21', '0.4.20', '0.4.19', '0.4.18', '0.4.17', '0.4.16', '0.4.15', '0.4.14', '0.4.13', '0.4.12', '0.4.11', '0.4.10', '0.4.9', '0.4.8', '0.4.7', '0.4.6', '0.4.5', '0.4.4', '0.4.3', '0.4.2', '0.4.1', '0.4.0']

def analyse_all(
        filename: str,
        args: argparse.Namespace
    ):
    slither_instances: list[SimplifiedSlither] = []
    dot = ''
    snippet = ''
    try:
        compilations = compile_all(filename, **vars(args))

    except Exception as e:
        raise e

    try:
        for compilation in compilations:
            slither_instances.append(
                SimplifiedSlither(
                    compilation,
                    ast_format='--ast-compact-json',
                    **vars(args)
                )
            )

    except Exception as e:
        raise e

    for slither_instance in slither_instances:
        for d in slither_instance.taint_analyse_to_dots:
            dot += d

        for s in slither_instance.snippets:
            snippet += s

    return dot, snippet

def record(arg: str, addresses: list, prefix: str):
    i = 0
    # create record files
    if prompt:
        if abalation:
            csv_filename = model + '_' + arg + '_raw_code' + '.csv'
            json_filename = model + '_' + arg + '_raw_code' + '.json'

        else:
            csv_filename = model + '_' + arg + '_code_snippet' + '.csv'
            json_filename = model + '_' + arg + '_code_snippet' + '.json'

    else:
        csv_filename = model + '_' + arg + '.csv'
        json_filename = model + '_' + arg + '.json'

    csv_path = os.path.join(os.getcwd(), 'result', csv_filename)
    json_path = os.path.join(os.getcwd(), 'result', json_filename)

    try:
        csv_file = open(csv_path, 'r')
        csv_file.close()
        json_file = open(json_path, 'r')
        csv_file.close()

    except:
        csv_file = open(csv_path, 'a')
        json_file = open(json_path, 'a')
        w = csv.DictWriter(csv_file, fieldnames=fieldnames)
        w.writeheader()
        csv_file.close()
        json.dump({}, json_file, indent=4)
        json_file.close()

    # iteration
    for addr in addresses:
        if i >= number and number > 0:
            break

        filename = addr + '.sol'
        file_path = os.path.join(prefix, filename)
        csv_file = open(csv_path, 'r')
        reader = csv.reader(csv_file)
        col = [row[0] for row in reader]
        
        if addr in col or filename in col:
            csv_file.close()
            continue

        # begin
        print(f'----- testing: {addr} -----')
        start = time.time()
        try:
            with open(file_path) as f:
                text = f.read()

        except:
            text = getcode(addr)
            with open(file_path, 'w') as f:
                f.write(text)

        if abalation:
            dot = ''
            snippet = '```solidity\n' + text + '\n```'

        else:
            version = get_solc_version(text)
            try:
                index= versions.index(version)
            
            except:
                index = 1
            
            break_flag = False
            while(index >= 0):
                if not version in installed_versions():
                    try:
                        install_artifacts(version)
                    
                    except Exception as e:
                        ex = e
                        #print(f' {version} compiler install failed')
                        index -= 1
                        version = versions[index]
                        continue

                switch_global_version(version, True)
                #print(f'solidity version: {version}')
                #print('taint analyse ...')

                # taint analyze
                try:
                    dot, snippet = analyse_all(file_path, args)
                    print('taint analyse done!')
                    break

                except Exception as e:
                    if isinstance(e, InvalidCompilation):
                        ex = e
                        #print('CompileError: ', e)
                        #print('Try more compiler ...')
                        index -= 1
                        version = versions[index]
                        continue
                    
                    elif isinstance(e, RecursionError):
                        ex = e
                        #print('AnalyseError: ', e)
                        break_flag = True
                        break
                    
                    else:
                        ex = e
                        #print('UnknownError: ', e)
                        #print('Try more compiler ...')
                        index -= 1
                        version = versions[index]
                        continue

            if index < 0 or break_flag:
                print('CompileFailed...')
                csv_file = open(csv_path, 'a')
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writerow({'address': addr, 'decision': ex.args[0].replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' '), 'time': 0, 'token': 0, 'pay': 0})
                csv_file.close()
                continue
        # llm
        if snippet == '```solidity\n```': 
            snippet = '```solidity\n' + text + '\n```'

        if dot == 'digraph {\n\tmsg.sender;\n\tmsg.value;\n}':
            # dot = 'In this contract, msg.sender and msg.value are not assigned to any other variables. So we can not generate a graph of dependency from this contract.\n'
            dot = ''
        
        decisions = []
        analysis = 'None'
        for x in range(repeat):
            detector = llm.Inopz(dot, snippet, model, temperature, prompt)
            
            try:
                decision, analysis, prompt_tokens, completion_tokens = detector.analyse()
                decisions.append(str(x) + ':' + str(decision))

            except Exception as e:
                print('ModelError: ', e)
                decisions.append(str(x) + ':fail')
                analysis = 'failure: ' + str(e.args[0])
                prompt_tokens = 0 
                completion_tokens = 0
                span = 0

        end = time.time()
        span = int((end - start)/repeat)
        tokens = prompt_tokens + completion_tokens
        pay = (prompt_tokens * in_rate + completion_tokens * out_rate) / 1000
        #
        csv_file = open(csv_path, 'a')
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow({'address': addr, 'decision': str(decisions), 'time': span, 'tokens':tokens, 'pay': pay})
        csv_file.close()
        #
        json_file = open(json_path, 'r')
        json_dict = json.load(json_file)
        json_file.close()
        json_dict.update({addr: analysis})
        json_file = open(json_path, 'w')
        json.dump(json_dict, json_file, indent=4)
        json_file.close()
        #
        i += 1
        if 'gpt' in model:
            time.sleep(5)

def singal(addr: str, file_path: str):
    if file_path != None:
        with open(file_path) as f:
            text = f.read()

    elif addr != None:
        text = getcode(addr)
        file_path = os.path.join(os.getcwd(), 'ContractFiles', addr + '.sol')
        with open(file_path, 'w') as f:
            f.write(text)

    else:
        pass

    version = get_solc_version(text)
    index= versions.index(version)
    break_flag = False
    while(index >= 0):
        if not version in installed_versions():
            try:
                install_artifacts(version)
            
            except Exception as e:
                print(f' {version} compiler install failed')
                index -= 1
                version = versions[index]
                continue

        switch_global_version(version, True)
        print(f'solidity version: {version}')
        print('taint analyse ...')

        # compile
        try:
            dot, snippet = analyse_all(file_path, args)
            # print('taint analyse done!')
            break

        except Exception as e:
            if isinstance(e, InvalidCompilation):
                # print('CompileError: ', e)
                # print('Try more compiler ...')
                index -= 1
                version = versions[index]
                continue

            elif isinstance(e, RecursionError):
                # print('AnalyseError: ', e)
                break_flag = True
                break

            else:
                # print('UnknownError: ', e)
                # print('Try more compiler ...')
                index -= 1
                version = versions[index]
                continue

    if index < 0 or break_flag:
        print('CompileFailed...')

    else:
        # PonziSleuth
        if snippet == '```solidity\n```': 
            snippet = '```solidity\n' + text + '\n```'

        if dot == 'digraph {\n\tmsg.sender;\n\tmsg.value;\n}':
            # dot = 'In this contract, msg.sender and msg.value are not assigned to any other variables. So we can not generate a graph of dependency from this contract.\n'
            dot = ''

        detector = llm.Sleuth(dot, snippet, model, temperature, prompt)
        try:
            detector.analyse()

        except Exception as e:
            print('ModelError: ', e)


def main():
    # process path
    if path != None:
        addresses = [f.split('.')[0] for f in os.listdir(path)]
        prefix = path
        record(os.path.split(path)[1], addresses, prefix)

    # process csv
    elif csv_path != None:
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            addresses = [row[1] for row in reader]
        
        addresses.pop(0)
        prefix = os.path.join(os.getcwd(), 'ContractFiles')
        record(os.path.split(csv_path)[1].split('.')[0], addresses, prefix)
    
    # process singal
    elif filename != None:
        singal(None, filename)

    # process address
    elif address != None:
        singal(address, None)

    # others
    else:
        print('Argments error. Use \'-h\' for help.')
