
from config import Config


class Erc20Move:
    hash = ''
    ownerAddr = ''
    fromAddr = ''
    toAddr = ''
    value = 0
    tokenName = ''
    tokenSymbol = ''
    tokenDecimal = 0
    contractAddress = ''

    def __init__(self, ownerAddr) :
        self.ownerAddr = ownerAddr
    
    def isIn(self):
        return self.ownerAddr == self.toAddr
    
    def getDirection (self):
        return 'IN' if self.ownerAddr == self.toAddr else 'OUT'

    def getCsvHeader() -> str:
        return 'direct,fromAddr,toAddr,value,tokenSymbol,contractAddress'

    def toCSV(self):
        self.direct = 'IN' if self.ownerAddr == self.toAddr else 'OUT' 
        return f'{self.direct},{self.fromAddr},{self.toAddr},{self.value},{self.tokenSymbol},{self.contractAddress}'

class Transaction:
    ownerAddr = ''
    blockNumber = 0
    timeStamp = 0
    hash = ''
    blockHash = ''
    fromAddr = ''
    toAddr = ''
    value = 0
    gas:int = 0
    gasPrice:int = 0 
    isError: bool = False
    txreceipt_status: bool
    input = ''
    cumulativeGasUsed:int = 0
    gasUsed:int = 0

    lstErc20Move: list[Erc20Move] = []
    direct = ''
    def isIn(self):
        return self.ownerAddr == self.toAddr
    
    def __init__(self, ownerAddr) :
        self.ownerAddr = ownerAddr
        self.lstErc20Move = []
    
    def getDirection (self):
        return 'IN' if self.ownerAddr == self.toAddr else 'OUT'

    def addErcMove(self, m: Erc20Move):
        for m2 in self.lstErc20Move:
            if(m.contractAddress == m2.contractAddress and m.getDirection() == m2.getDirection()) :
                m2.value += m.value
                return 
        self.lstErc20Move.append(m)
    
    def containToken(self, token:str) -> bool:
        for m in self.lstErc20Move:
            if(m.tokenSymbol.upper() == token.upper()) :
                return True
        return False
    
    def searchMove(self, token:str) -> Erc20Move:
        for m in self.lstErc20Move:
            if(m.tokenSymbol.upper() == token.upper()) :
                return m
        return None
    
    def getCsvHeader():
        return f'blockNumber,timeStamp,hash,direct,fromAddr,toAddr,value,fee,isError,{Erc20Move('').getCsvHeader()},{Erc20Move('').getCsvHeader()}'
    
    def toCSV(self):
        self.direct = 'IN' if self.ownerAddr == self.toAddr else 'OUT' 
        fee = self.gasPrice * self.gasUsed / Config.nativeTokenDecimalLeft
        ms = ''
        for m in self.lstErc20Move:
            ms += f',{m.toCSV()}'

        return f'{self.blockNumber},{self.timeStamp},{self.hash},{self.direct},{self.fromAddr},{self.toAddr},{self.value},{fee},{self.isError},{self.lstErc20Move.__len__()}{ms}'





