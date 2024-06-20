from datetime import datetime
import requests
from pathlib import Path
from transaction import Erc20Move, Transaction 
from config import Config

gConfig = Config()

gPhishingListContracts = ['0xd6cbfe031449ad5619e4baf3c54deaee151dcc13'
                          ,'0xA37f0DffDcb8Ba0906519848B820CE75915C2f74'
                          ,'0x4d1F040a6e1Ad9E2D320DEbBB1EFD03E36dAF2ce'
                          ,'0x329a2ac897a23302cce1640e73a8b8d2530e2aae'
                          ,'0xa01fc068860bddee18a8de04a9092ba608610a79','0xeC7e05fA10d111A56DEE0F603b343B8896913528'
                          ,'0x2fb883dd6b8c573f77331df8c459a1015d9c2f5f','0x65dc37b398fb7674495c8485fc4f4fafad116f27'
                          ]

def isPhishing(tx):
    # return tx['value'] == '0' or tx['contractAddress'].lower() in gPhishingListContracts
    return tx['contractAddress'].lower() in gPhishingListContracts

def fileExists(filePath) :
    return Path(filePath).exists()

def listAll(fileName, wallAddr, startblock, endblock):
    url = 'https://api.bscscan.com/api'
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
    url = 'https://api.bscscan.com/api'
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
        print('call to bscscan: ERROR')

def lstInternalTxs(wallAddr, startblock, endblock, offset) -> dict[str, Erc20Move]:
    url = 'https://api.bscscan.com/api'
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
                move.fromAddr = tx['from']
                move.toAddr = tx['to']
                move.value = int(tx['value']) / gConfig.nativeTokenDecimalLeft
                # move.contractAddress = tx['contractAddress']
                move.tokenSymbol = gConfig.nativeTokenSymbol
                finalDictionary[txHash] = move 
        return finalDictionary
    else:
        raise Exception("call to bscscan: ERROR")
        print('call to bscscan: ERROR')


def lstErc20Txs(wallAddr, startblock, endblock, offset) -> list[Erc20Move]:
    url = 'https://api.bscscan.com/api' 
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
    url = 'https://api.bscscan.com/api' 
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

    fileName = f'{datetime.now().strftime('%Y_%m_%d %H_%M_%S')}.csv' 

    wallAddr = '0xd4853Ca382B51f50A8dE3389efB319fff03690C5'.lower()
    # wallAddr = '0x96DC097012B3ba0f033f536EE8F9039712E4A02d'.lower()
    startblock = 34000000
    endblock = 	 39999999
    offset = 9999

    dicNormal: dict[str, Transaction] = lstNormalTxs(wallAddr, startblock, endblock, offset) 
    print(f'from block {startblock} >> {endblock}: {dicNormal.__len__()} NORMAL txs')

    dicInternal: dict[str, Erc20Move] = lstInternalTxs(wallAddr, startblock, endblock, offset) 
    print(f'from block {startblock} >> {endblock}: {dicInternal.__len__()} INTERNAL txs')

    lstErc:list[Erc20Move] = lstErc20Txs(wallAddr, startblock, endblock, offset)
    print(f'from block {startblock} >> {endblock}: {lstErc.__len__()} ERC20 txs')

    for m in lstErc:
        # if(m.hash == '0x4e47998828c23e04c97b6e941ec8b68fe6a8417ed1df1c9e9bfb13abb8b2b7bb')
        #    print('check')
        if(m.value == 0): continue
        if(not m.hash in dicNormal): 
            print(f'{m.hash} NOT in normal list')
        else:
            ta = dicNormal[m.hash]
            ta.addErcMove(m)

            if(m.hash in dicInternal):
                mi = dicInternal[m.hash]
                ta.addErcMove(mi)


    mode = 'a' if Path(fileName).exists() else 'w'
    f = open(fileName, mode, encoding="utf-8")
    header = f'blockNumber,timeStamp,hash,direct,fromAddr,toAddr,value,fee,isError,direct,fromAddr,toAddr,value,tokenSymbol,contractAddress,direct2,fromAddr2,toAddr2,value2,tokenSymbol2,contractAddress2,direct3,fromAddr3,toAddr3,value3,tokenSymbol3,contractAddress3'
    f.writelines(header)
    
    for tx in dicNormal.values() : 
        f.write('\n')
        f.writelines(tx.toCSV())

    f.close()
    print(f'check your csv file {fileName}')

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
    header = f'blockNumber,timeStamp,hash,direct,fromAddr,toAddr,value,fee,isError,direct,fromAddr,toAddr,value,tokenSymbol,contractAddress,direct2,fromAddr2,toAddr2,value2,tokenSymbol2,contractAddress2,direct3,fromAddr3,toAddr3,value3,tokenSymbol3,contractAddress3'
    f.writelines(header)
    
    for tx in lstTx: 
        f.write('\n')
        f.writelines(tx.toCSV())

    f.close()
    print(f'check your csv file {fileName}')


if __name__ == '__main__':
    print(datetime.now())
    main()
    
