from web3 import Web3
import json
import random
import secrets
import time

random.seed(time.time())


def getRandInt(length: int):
    return random.randint(-50,50)


def getRandUint(length: int):
    return random.randint(0,50)


def getRandFix():
    random_float = random.uniform(0.0, 1.0)
    random_fixed = hex(int(random_float * 2**128))
    return random_fixed


def getRandUfixed():
    random_float = random.uniform(-1.0, 0.0)
    random_fixed = hex(int(random_float * 2**128))
    return random_fixed


def getRandBool():
    randomBool = random.choice([True, False])
    randomBool_solidity = str(randomBool).lower()
    return randomBool_solidity


def getRandAddress():
    return Web3.to_checksum_address("0x" + secrets.token_hex(20))


def getRandString():
    randomString = secrets.token_urlsafe(32)
    randomString_solidity = '"' + randomString + '"'
    return randomString_solidity


def getRandByteArray():
    random_bytes = secrets.token_bytes(32)
    return "0x" + random_bytes.hex()


def getRandArray():
    random_array = [random.randint(0, 100) for i in range(5)]
    return "[" + ", ".join(map(str, random_array)) + "]"


def getRandStruct():
    return


def getRandMapping():
    return


def getRandEnum():
    return


def getF_all(contractInfo: dict) -> dict:
    F_all = {}
    for functions in contractInfo.items():
        for function, functionInfo in functions.items():
            F_all[function] = functionInfo
    # print(F_all)
    return F_all


def getF_kws(F_all: dict) -> dict:
    F_kws = {}
    keywords = [
        "enter",
        "init",
        "invest",
        "fallback"
    ]
    for function in F_all:
        if function in keywords:
            F_kws[function] = F_all[function]
    return F_kws


def getF_payable(F_all: dict) -> dict:
    F_payable = {}
    for function in F_all:
        if F_all[function]["payable"] == True:
            F_payable[function] = F_all[function]
    return F_payable


def getF_writable(F_all: dict) -> dict:
    F_writable = {}
    for function in F_all:
        if len(F_all[function]["writes"]) > 0:
            F_writable[function] = F_all[function]
    return F_writable


def randomChoose(F_kws: dict, F_all: dict, p=0.6):
    if len(F_kws) <= 0:
        return False

    random.seed(time.time())
    randomNum = random.random()
    res = {}
    if randomNum < p:
        res = F_kws[random.choice(list(F_kws.keys()))]
        while res["visibility"] == "private":
            res = F_kws[random.choice(list(F_kws.keys()))]

    else:
        res = F_all[random.choice(list(F_all.keys()))]
        while res["visibility"] == "private":
            res = F_all[random.choice(list(F_all.keys()))]

    return res


def generateTransaction(func: dict, payableCount: int):
    tx = func.copy()
    if tx["payable"]:
        tx["value"] = random.randint(payableCount, payableCount + 10)

    randomParam = {} 
    params: dict = tx["parameters"] 
    for p in params.keys(): 
        if params[p] == "address":
            randomParam[p] = getRandAddress()

        elif params[p][0: 3] == "int":
            randomParam[p] = getRandInt(eval(params[p][3:]))

        elif params[p][0: 4] == "uint":
            randomParam[p] = getRandUint(eval(params[p][4:]))

        elif params[p] == "fixed":
            randomParam[p] = getRandFix()

        elif params[p] == "ufixed":
            randomParam[p] = getRandUfixed()

        elif params[p] == "bool":
            randomParam[p] = getRandBool()

        elif params[p] == "bytes":
            randomParam[p] = getRandByteArray()

        elif params[p] == "array":
            randomParam[p] = getRandArray()

        elif params[p] == "struct":
            randomParam[p] = getRandStruct()

        elif params[p] == "enum":
            randomParam[p] = getRandEnum()

        elif params[p] == "mapping":
            randomParam[p] = getRandMapping()

    tx["randomParameterValues"] = randomParam 

    return tx 


def getDependency(F_all: dict, functionName: str) -> dict:
    deps = {} 
    writes = F_all[functionName]["writes"] 
    for function in F_all: 
        if len(set(F_all[function]["reads"]) & set(writes)) > 0:
            deps[function] = F_all[function]

    return deps 


def removeUncallable(F_all: dict):
    toBeRemoved = [] 
    for func in F_all: 
        if func == 'constructor' or F_all[func]["visibility"] == "private":
            toBeRemoved.append(func)
    for func in toBeRemoved: 
        del F_all[func] 

    return F_all


def transacSeqGenerator(F_all: dict, Max: int):
    F_kws = getF_kws(F_all) 
    F_payable = getF_payable(F_all) 
    F_writable = getF_writable(F_all) 
    payableCount = 0 
    g = 0 
    SeedPool = [] 
    while g < Max: 
        txs = [] 

        while len(txs) < len(F_all): 
            func = randomChoose(F_kws, F_all)
            if not func: 
                func = randomChoose(F_payable, F_all)
                if not func:  
                    func = randomChoose(F_writable, F_all)
                    if not func:
                        break
            tx = generateTransaction(func, payableCount) 
            if func["payable"]: 
                payableCount += 10
            txs.append(tx) 
            while len(txs) < len(F_all): 
                dep = getDependency(F_all, txs[-1]["name"]) 
                if dep != {}: 
                    func_dep = randomChoose(
                        dep, F_all) 
                else: 
                    func_dep = randomChoose(F_all, F_all)
                tx = generateTransaction(
                    func_dep, payableCount) 
                if func_dep["payable"]: 
                    payableCount += 10
                txs.append(tx) 
        SeedPool.append(txs) 
        g += 1
    return SeedPool 


def getTransactionSequence(filename: str, contractsInfo: dict, Max: int):
    seedPool = {}
    constructor = contractsInfo['constructor']
    callable_functions = removeUncallable(contractsInfo) 

    seedPool[filename] = transacSeqGenerator(
        callable_functions,
        Max
    )

    construct = generateTransaction(constructor, 0)

    with open(filename + '.json', "w") as f:
        f.write(json.dumps(seedPool, indent=4))

    return construct