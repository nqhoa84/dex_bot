 
class Config:
    API_KEY_ETH = 'DXWN7SXXQKZGW5YYCT41CFB2A67NB98WE8'
    API_KEY_LI = 'HIVJ6VGS9B6M34RA91S77EGJNTJIA3NUG8'
    API_KEY_BSC = 'KVSYTVNS7ZCISVCCZQDU4G1F3436XA3HMW' 
    API_KEY_POLYGON = 'ACEEHM6XGEQGD5UUKSIKXDNTSK81PZJJ2B'
    API_KEY_ARB = 'C7FSAD1E1SF97VH3IRIRCAYXGK9DQ89ZTE'
    API_KEY_BASE = 'TR3MJNFPQB1TN9U7N5ZVSTTP1UZDWTQAUD'

    END_POINT_ETH = 'https://api.etherscan.io/api'
    END_POINT_BSC = 'https://api.bscscan.com/api'
    END_POINT_POLYGON = 'https://api.polygonscan.com/api'
    END_POINT_ARB = 'https://api.arbiscan.io/api'
    END_POINT_BASE = 'https://api.basescan.org/api'
    END_POINT_LINEA = 'https://api.lineascan.build/api'

    END_POINT = END_POINT_POLYGON

    nativeTokenDecimalShift = 15
    
    # pow (10, 15) >> unit is mili Native token
    """
    pow (10, 15) >> unit is mili Native token
    """
    nativeTokenDecimalLeft = 1000000000000000
    
    nativeTokenSymbol = 'mNative'

    bonds:dict[str,str] = {'0x07E48b1c531cBF32222851D0B1f77fF58b13942d','RPG'}
    bondContracts:list[str] = ['0x07E48b1c531cBF32222851D0B1f77fF58b13942d'
                               ]
    
    #RPG bonds
    # watchAddress = '0x07E48b1c531cBF32222851D0B1f77fF58b13942d'.lower() #RPG bonds
    # lstWatchToken:list[str] = []

    # watchAddress = '0x96DC097012B3ba0f033f536EE8F9039712E4A02d'.lower() #bond 5
    # lstWatchToken:list[str] = ['ICHI']
    # watchAddress = '0xBA03189866FF1da827fCDd707c2d04b58AC34e1c'.lower() #bond 2
    # lstWatchToken:list[str] = ['ApeX','CGPT','PALM', 'AITECH', 'CHAPZ','HGPT','RPG'] #bond 2

    # API_KEY = API_KEY_LI
    # END_POINT = END_POINT_LINEA
    # watchAddress = '0x09590326021fE400dE3Ce8B54E55E534C8Fa9D60'.lower() # Bond 3
    # lstWatchToken:list[str] = ['SOPH'] 
    # startblock = 5013580 # 5013580 # linea Min block 
    # endblock = 	10524356

    # API_KEY = API_KEY_POLYGON
    # watchAddress = '0x09590326021fE400dE3Ce8B54E55E534C8Fa9D60'.lower() # Bond 3
    # lstWatchToken:list[str] = ['ELON', 'NOTES', 'KNIGHT', 'MV', 'ABOND', 'AMBO', 'BLANK', 'BOM', 'fxA3A', 'ORBS', 'UBU','IXT', 'NSDX','VEXT', 'FBX', 'WEFI', 'A51', 'BULL', 'NFTBS', 'THX'] 
    # startblock = 60923600 # polygon
    # endblock = 	 62830394


    # API_KEY = API_KEY_ARB
    # END_POINT = END_POINT_ARB
    # watchAddress = '0x09590326021fE400dE3Ce8B54E55E534C8Fa9D60'.lower() # Bond 3
    # lstWatchToken:list[str] = ['ENO'] 
    # startblock = 232344760 #232004300 # ARB min block
    # endblock = 	 253319799


    # API_KEY = API_KEY_BSC
    # END_POINT = END_POINT_BSC
    # watchAddress = '0xd4853Ca382B51f50A8dE3389efB319fff03690C5'.lower() # Bond 4
    # lstWatchToken:list[str] = ['HBR', 'WAM'] 
    # startblock = 34890820 #BOND 4 bsc min block
    # endblock = 	 42957197

    # API_KEY = API_KEY_ETH
    # END_POINT = END_POINT_ETH
    # watchAddress = '0xd4853Ca382B51f50A8dE3389efB319fff03690C5'.lower() # Bond 4
    # lstWatchToken:list[str] = ['']
    # startblock = 19501100 # eth
    # endblock = 	 20868307

    # API_KEY = API_KEY_POLYGON
    # END_POINT = END_POINT_POLYGON
    # watchAddress = '0xd4853Ca382B51f50A8dE3389efB319fff03690C5'.lower() # Bond 4
    # lstWatchToken:list[str] = ['']
    # startblock = 58980200 # thx min block
    # endblock = 	 61812999 

    # API_KEY = API_KEY_BSC
    # END_POINT = END_POINT_BSC
    # watchAddress = '0x96DC097012B3ba0f033f536EE8F9039712E4A02d'.lower() #bond 5
    # lstWatchToken:list[str] = ['']
    # startblock =  35865180 # BSC MIN BLOCK 35865189
    # endblock = 	42527204

    API_KEY = API_KEY_BASE
    END_POINT = END_POINT_BASE
    watchAddress = '0x96DC097012B3ba0f033f536EE8F9039712E4A02d'.lower() #bond 5
    lstWatchToken:list[str] = ['SOPH'] 
    startblock = 16811000 # base  MIN BLOCK
    endblock = 	 20870539

    

    
    