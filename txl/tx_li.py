from datetime import datetime
import requests
from pathlib import Path
from transaction import Erc20Move, Transaction 
from config import Config
import time

gConfig = Config()

gPhishingListContracts = []

def isPhishing(tx):
    # return tx['value'] == '0' or tx['contractAddress'].lower() in gPhishingListContracts
    return tx['contractAddress'].lower() in gPhishingListContracts

def fileExists(filePath) :
    return Path(filePath).exists()

def listAll(fileName, wallAddr, startblock, endblock):
    url = 'https://api.lineascan.build/api'
    offset = 9900
    paras = {'module':'account', 'action':'txlist',
            # 'contractaddress':'0xc9849e6fdb743d08faee3e34dd2d1bc69ea11a51',
            'address':wallAddr, 
            'page':'1', 'offset':offset, 'startblock': startblock, 'endblock':endblock,
            'apikey' : gConfig.API_KEY, 'sort':'desc'
            } 
    r = requests.post(url, data=paras) 
    result = r.json()

    if(result.get('status') != '1'):
        raise("ERROR GETTING LIST OF ALL TXs")

     
    finalLst = {}

    dicInternal = lstInternalTxs(wallAddr, startblock, endblock, offset)
    dicErc20 = lstErc20Txs(wallAddr, startblock, endblock, offset)

    for tx in result['result']: 
        if (isPhishing(tx)) : continue
        txHash = str(tx['hash'])
        
        timeStamp = tx['timeStamp'] 

        # tokenDecimal = int(tx['tokenDecimal'])
        value = int(tx['value']) / pow(10, gConfig.nativeTokenDecimalShift)
        txFrom = tx['from'].lower()
        txTo = tx['to'].lower()
        direct = 'IN' if txTo == wallAddr else 'OUT'
        if(txHash in finalLst):
            finalLst[txHash] += f',{direct},{txFrom},{txTo},{value},Native'
        else:

            finalLst[txHash] = f'{tx['blockNumber']},{timeStamp},{txHash},{direct},{txFrom},{txTo},{value},Native,{tx['cumulativeGasUsed']},{tx['gasPrice']},{tx['gasUsed']}' 

            if(txHash in dicInternal):
                interTx = dicInternal[txHash]
                interDirect = 'IN' if interTx['to'] == wallAddr else 'OUT'
                inVal = int(interTx['value']) / pow(10, gConfig.nativeTokenDecimalShift)
                finalLst[txHash] += f',{interDirect},{interTx['from']},{interTx['to']},{inVal},Native,{interTx['contractAddress']}'

            if(txHash in dicErc20):
                interTx = dicErc20[txHash]
                interDirect = 'IN' if interTx['to'] == wallAddr else 'OUT'
                inVal = int(interTx['value']) 
                finalLst[txHash] += f',{interDirect},{interTx['from']},{interTx['to']},{inVal},{interTx['tokenSymbol']},{interTx['contractAddress']}'
    
    
    mode = 'a' if Path(fileName).exists() else 'w'
    f = open(fileName, mode, encoding="utf-8")
    f.writelines('blockNumber,timeStamp,txHash,direct,txFrom,txTo,value,tokenSymbol,contractAddress,gas,gasPrice,gasUsed,direct2,txFrom2,txTo2,value2,tokenSymbol2,contractAddress2')
    
    for tx in finalLst.values() : 
        f.write('\n')
        f.writelines(tx)

    f.close()

     

def lstXxx20Txs(fileName, wallAddr, startblock, endblock, offset):
    url = 'https://api.lineascan.build/api'
    paras = {'module':'account', 'action':'tokentx',
            # 'contractaddress':'0xc9849e6fdb743d08faee3e34dd2d1bc69ea11a51',
            'address':wallAddr, 
            'page':'1', 'offset':offset, 'startblock': startblock, 'endblock':endblock,
            'apikey' : gConfig.API_KEY, 'sort':'desc'
            } 
    r = requests.post(url, data=paras)

    print(r.status_code)
    result = r.json()

    if(result.get('status') == '1'):
        finalLst = {}

        dicInternal = lstInternalTxs(wallAddr, startblock, endblock, offset)

        for tx in result['result']: 
            if (isPhishing(tx)) : continue
            txHash = str(tx['hash'])
            
            timeStamp = tx['timeStamp']
            value = int(tx['value'])
            if (value == '0'):  continue
            # tokenDecimal = int(tx['tokenDecimal'])
            # value = int(tx['value']) / pow(10, tokenDecimal + tokenDecimalShift)
            txFrom = tx['from'].lower()
            txTo = tx['to'].lower()
            direct = 'IN' if txTo == wallAddr else 'OUT'
            if(txHash in finalLst):
                finalLst[txHash] += f',{direct},{txFrom},{txTo},{value},{tx['tokenSymbol']},{tx['contractAddress']}'
            else:

                finalLst[txHash] = f'{tx['blockNumber']},{timeStamp},{txHash},{direct},{txFrom},{txTo},{value},{tx['tokenSymbol']},{tx['contractAddress']},{tx['gas']},{tx['gasPrice']},{tx['gasUsed']}' 

                if(txHash in dicInternal):
                    interTx = dicInternal[txHash]
                    interDirect = 'IN' if interTx['to'] == wallAddr else 'OUT'
                    inVal = int(interTx['value']) / pow(10, gConfig.nativeTokenDecimalShift)
                    finalLst[txHash] += f',{interDirect},{interTx['from']},{interTx['to']},{inVal},Native,{interTx['contractAddress']}'
        
        
        mode = 'a' if Path(fileName).exists() else 'w'

        f = open(fileName, mode, encoding="utf-8")
        f.writelines('blockNumber,timeStamp,txHash,direct,txFrom,txTo,value,tokenSymbol,contractAddress,gas,gasPrice,gasUsed,direct2,txFrom2,txTo2,value2,tokenSymbol2,contractAddress2')
        
        for tx in finalLst.values() : 
            f.write('\n')
            f.writelines(tx)

        f.close()

    else:
        print('call to LINEA SCAN: ERROR')

def lstInternalTxs(wallAddr, startblock, endblock, offset) -> dict[str, Erc20Move]:
    url = 'https://api.lineascan.build/api'
    paras = {'module':'account', 'action':'txlistinternal',
            # 'contractaddress':'0xc9849e6fdb743d08faee3e34dd2d1bc69ea11a51',
            'address':wallAddr, 
            'page':'1', 'offset':offset, 'startblock': startblock, 'endblock':endblock,
            'apikey' : gConfig.API_KEY 
            } 
    r = requests.post(url, data=paras)
    result = r.json()

    if(True or result.get('status') == '1'):
        finalDictionary:dict[str, Erc20Move] = {}
        for tx in result['result']: 
            if (isPhishing(tx)) : continue
            txHash = str(tx['hash'])
            
            if(txHash in finalDictionary):
                continue
            else:
                move = Erc20Move(wallAddr)
                move.hash = txHash
                move.fromAddr = tx['from']
                move.toAddr = tx['to']
                move.value = int(tx['value']) / gConfig.nativeTokenDecimalLeft
                move.tokenSymbol = gConfig.nativeTokenSymbol
                finalDictionary[txHash] = move 
        return finalDictionary
    else:
        raise Exception("call to LINEA SCAN: ERROR")
        print('call to LINEA: ERROR')


def lstErc20Txs(wallAddr, startblock, endblock, offset) -> list[Erc20Move]:
    url = 'https://api.lineascan.build/api' 
    paras = {'module':'account', 'action':'tokentx',
            # 'contractaddress':'',
            'address':wallAddr, 
            'page':'1', 'offset':offset, 'startblock': startblock, 'endblock':endblock,
            'apikey' : gConfig.API_KEY, 'sort':'desc'
            } 
    r = requests.post(url, data=paras)
    result = r.json()

    if(result.get('status') != '1'):
        raise('ERROR GETTING LIST OF ERC20 TOKEN')
    finalDictionary:dict[str, Erc20Move] = {}
    re:list[Erc20Move] = []
    for tx in result['result']: 
        if (isPhishing(tx)) : continue
        txHash = str(tx['hash']) 
        if (txHash.endswith('b080333287d3dd710735425b2a8859156fd916c7d47fe951a312')) : 
            print('have b080333287d3dd710735425b2a8859156fd916c7d47fe951a312')
        move = Erc20Move(wallAddr)

        move.hash = txHash
        move.fromAddr = tx['from']
        move.toAddr = tx['to']
        move.tokenDecimal = int(tx['tokenDecimal'])
        move.value = int(tx['value']) / pow(10, move.tokenDecimal)
        move.contractAddress = tx['contractAddress']
        move.tokenSymbol = tx['tokenSymbol']
        move.tokenName = tx['tokenName']
        re.append(move)

    return re
    # finalDictionary = {}
    # for tx in result['result']: 
    #     if (isPhishing(tx)) : continue
    #     txHash = str(tx['hash'])
        
    #     if(txHash in finalDictionary):
    #         continue
    #     else:
    #         finalDictionary[txHash] = tx  
    # return finalDictionary


def lstNormalTxs(wallAddr, startblock, endblock, offset) -> dict[str,Transaction]:
    url = 'https://api.lineascan.build/api' 
    paras = {'module':'account', 'action':'txlist',
            # 'contractaddress':'',
            'address':wallAddr, 
            'page':'1', 'offset':offset, 'startblock': startblock, 'endblock':endblock,
            'apikey' : gConfig.API_KEY, 'sort':'desc'
            } 
    r = requests.post(url, data=paras)
    result = r.json()

    # if(result.get('status') != '1'):
    #     raise('ERROR GETTING LIST OF ERC20 TOKEN')
    finalDictionary:dict[str, Transaction] = {} 
    for tx in result['result']: 
        # if (isPhishing(tx)) : continue 

        move = Transaction(wallAddr)
        move.blockNumber = tx['blockNumber']
        move.timeStamp = tx['timeStamp'] 
        move.hash = str(tx['hash'])
        move.fromAddr = tx['from']
        move.toAddr = tx['to'] 
        move.value = int(tx['value']) / gConfig.nativeTokenDecimalLeft
        move.gas = int(tx['gas'])
        move.gasPrice = int(tx['gasPrice'])
        move.gasUsed = int(tx['gasUsed'])
        move.cumulativeGasUsed = int(tx['cumulativeGasUsed'])
        
        finalDictionary[move.hash]= move

    return finalDictionary 

def main():  
    wallAddr = Config.watchAddress
    startblock = Config.startblock 
    endblock = 	 Config.endblock
    offset = 9999

    fileName = f'LI_{wallAddr[39:]} {datetime.now().strftime('%Y%m%d %H_%M')} {startblock}_{endblock} .csv' 

    while (startblock <= endblock):
        print(f'{datetime.now().strftime('%Y_%m_%d %H_%M_%S')}.csv' )
        listAndSaveTxs(fileName, wallAddr, startblock, startblock + 1000000, offset)
        startblock += 1000001
        time.sleep(1)

    # return

    return 

def listAndSaveTxs(fileName, wallAddr, startblock, endblock, offset):
    dicNormal: dict[str, Transaction] = lstNormalTxs(wallAddr, startblock, endblock, offset) 
    print(f'from block {startblock} >> {endblock}: {dicNormal.__len__()} NORMAL txs')

    dicInternal: dict[str, Erc20Move] = lstInternalTxs(wallAddr, startblock, endblock, offset) 
    print(f'from block {startblock} >> {endblock}: {dicInternal.__len__()} INTERNAL txs')

    lstErc:list[Erc20Move] = lstErc20Txs(wallAddr, startblock, endblock, offset)
    print(f'from block {startblock} >> {endblock}: {lstErc.__len__()} ERC20 txs')

    for m in dicInternal.values():
        if(m.hash in dicNormal) : continue
        else:
            t = Transaction(wallAddr)
            t.hash = m.hash
            dicNormal[t.hash] = t

    for m in lstErc:
        if(m.hash in dicNormal) : continue
        else:
            t = Transaction(wallAddr)
            t.hash = m.hash
            dicNormal[t.hash] = t

    for ta in dicNormal.values():
        if (ta.hash.endswith('b080333287d3dd710735425b2a8859156fd916c7d47fe951a312')) : 
            print('have b080333287d3dd710735425b2a8859156fd916c7d47fe951a312')
        if(ta.hash in dicInternal):
            mi = dicInternal[ta.hash]
            ta.addErcMove(mi)
        for m in lstErc:
            if(m.hash != ta.hash): continue
            ta.addErcMove(m)

    exportListTx2File(fileName, dicNormal.values())

    if(gConfig.lstWatchToken is None or gConfig.lstWatchToken.__len__() == 0): return

    for token in gConfig.lstWatchToken:
        lstTxforToken = []
        for tx in dicNormal.values():
            if(tx.containToken(token)):
                 lstTxforToken.append(tx)
        if(lstTxforToken.__len__() > 0):
            exportListTx2File(fileName.replace('.csv', f'_{token}.csv'), lstTxforToken)

    

    # for t in dicNormal.values():
    #     print(t.toCSV())

def exportListTx2File(fileName, lstTx:list[Transaction]):
    mode = 'a' if Path(fileName).exists() else 'w' 
    f = open(fileName, mode, encoding="utf-8")
    if(mode == 'w') :
        header = f'blockNumber,timeStamp,hash,direct,fromAddr,toAddr,value,fee,isError,Count Move,direct1,fromAddr1,toAddr1,value1,tokenSymbol1,contractAddress1,direct2,fromAddr2,toAddr2,value2,tokenSymbol2,contractAddress2,direct3,fromAddr3,toAddr3,value3,tokenSymbol3,contractAddress3'
        f.writelines(header)
    
    for tx in lstTx: 
        f.write('\n')
        f.writelines(tx.toCSV())

    f.close()
    print(f'check your csv file {fileName}')


if __name__ == '__main__':
    print(datetime.now())
    print (Config.API_KEY + '     ----- linea')
    print (Config.lstWatchToken)
    print(Config.nativeTokenDecimalLeft)
    print(Config.nativeTokenSymbol)
    main()
    
