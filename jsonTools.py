"""
This is a collection of methods to modify json files. 

Some english calls match the japanese ones enough to zip the english lines in with the japanese offsets.
This will also help do other json modifications as needed.

"""

import os, sys, struct
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# import xmlModifierTools as xmlin

# flags
debug = True

# This should be the format moving forward
newjson = {
    "calls": {},
    "saves": {},
    "freqAdd": {},
    "prompts": {}
}

codecNames = {
    "メリル" : "MERYL",
    "キャンベル" : "CAMPBELL",
    "メイ・リン" : "MEI LING",
    "オタコン" : "OTACON",
    "マスター" : "MASTER",
    "ナスターシャ" : "NASTASHA",
    "ディープスロート" : "DEEPTHROAT",
    "STAFF" : "STAFF",
}

matchingCalls = {
    "0": "0",
    "505": "910", # Meryl call
    "26537": "42370",
    "293536": "283744", # 140.85
}

def replaceJsonText(callOffsetA: str, callOffsetB: str):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    global jsonContentA
    global jsonContentB
    global newjson
    
    newCallSubs = dict(zip(jsonContentB["calls"][callOffsetB].keys(), jsonContentA["calls"][callOffsetA].values()))
    jsonContentB[callOffsetB] = newCallSubs
    newjson["calls"].update({"0": newCallSubs}) 

def writeJsonToFile(outputFilename: str):
    """
    Writes the new json file to output
    """
    global newjson

    newCall = open(outputFilename, 'w')
    newCall.write(json.dumps(newjson))
    newCall.close

# test 

"""
if __name__ == '__main__':
"""
# This one is for the whole json with all call information
"""
    parser = argparse.ArgumentParser(description=f'Zip subtitles json offsets from another. \nUsage: main.py subs.json:callOffsetA offsets.json:callOffsetB [outputFilename.json]')

    # REQUIRED
    parser.add_argument('subsJson', type=str, help="json including the subtitles we want to zip, ex: filename.json:12345")
    parser.add_argument('offsetsJson', type=str, help="json including the offsets we want to zip, ex: filename.json:12345")
    # Optionals
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.json)")

    args = parser.parse_args()
    
    subsInFilename = args.subsJson.split(':')[0]
    offsetsInFilename = args.offsetsJson.split(':')[0]

    subsCall = args.subsJson.split(':')[1]
    offsetsCall = args.offsetsJson.split(':')[1]

    jsonContentA = json.load(open(subsInFilename, 'r'))
    jsonContentB = json.load(open(offsetsInFilename, 'r'))

    matchingCalls.update({subsCall: offsetsCall})
    
    for key in matchingCalls:
        # If we need to do only one, you can do {"0": "0"}
        replaceJsonText(key, matchingCalls.get(key))
    
    outputFilename = "recompiledCallBins/modifiedCall.json"
    writeJsonToFile(outputFilename)
"""

jsonA = open("recompiledCallBins/RADIO-usa-d1-Iseeva.json", 'r')
jsonB = open("recompiledCallBins/RADIO-jpn-d1-Iseeva.json", 'r')

outputFilename = 'recompiledCallBins/modifiedCalls.json'

inputJson = json.load(jsonA)
modJson = json.load(jsonB)

# Def put calls together
for call in inputJson['calls'].keys():
    newSubs: dict = inputJson['calls'][call]
    destCall = matchingCalls.get(call)
    if destCall is None:
        continue
    newOffsets: dict = modJson['calls'][destCall]
    newCall = dict(zip(newOffsets.keys(), newSubs.values()))
    newjson['calls'][destCall] = newCall

# Save file names (Dock, heliport, etc)
# is coming out as unicode for some reason...
newSaves: dict = next(iter(inputJson['saves'].values()))
for save in modJson['saves'].keys():
    newjson['saves'][save] = newSaves

# Save options (SAVE / DO NOT SAVE)
options: dict = next(iter(inputJson['prompts'].values()))
for opt in modJson['prompts'].keys():
    newjson['prompts'][opt] = options

for name in modJson['freqAdd'].keys():
    newjson['freqAdd'][name] = codecNames.get(modJson['freqAdd'].get(name))

"""matches = zip(inputJson['calls'].keys(), modJson['calls'].keys())
for item in matches:
    print(item)
   
zippedOffsets = {
    {'0': '0'},
    {'505': '910'},
    {'671': '1143'},
    {'3326': '5833'},
    {'11590': '20491'},
    {'26537': '42370'},
    {'26940': '43010'},
    {'35756': '58410'},
    {'38411': '59333'},
    {'41131': '63533'},
    {'43872': '67711'},
    {'69134': '100554'},
    {'69320': '101971'},
    {'94514': '105879'},
    {'97082': '109999'},
    {'122241': '113848'},
    {'126772': '118092'},
    {'129537': '122322'},
    {'179885': '177459'},
    {'182648': '181774'},
    {'229267': '261556'},
    {'271289': '272965'},
    {'282526': '278558'},
    {'287169': '283744'},
    {'293536': '285449'},
    {'294379': '288512'},
    {'295704': '291664'},
    {'298506': '295376'},
    {'301847': '297431'},
    {'302703': '298504'},
    {'303179': '300837'},
    {'304549': '303506'},
    {'305678': '308961'},
    {'308325': '309595'},
    {'308699': '311129'},
    {'309558': '315529'},
    {'311736': '333438'},
    {'321920': '345760'},
    {'328919': '346636'},
    {'329312': '353110'},
    {'332769': '354836'},
    {'333817': '357134'},
    {'335020': '360648'},
    {'337120': '364457'},
    {'338913': '370275'},
    {'342170': '373157'},
    {'343739': '373922'},
    {'344231': '382452'},
    {'348314': '384737'},
    {'349360': '387533'},
    {'350796': '392774'},
    {'353441': '404827'},
    {'360036': '411172'},
    {'363076': '420535'},
    {'367351': '424648'},
    {'369290': '435981'},
    {'376677': '437859'},
    {'377402': '438879'},
    {'378647': '440301'},
    {'379873': '442271'},
    {'380406': '442769'},
    {'381165': '443783'},
    {'382244': '444479'},
    {'382543': '444665'},
    {'383629': '500848'},
    {'384599': '501542'},
    {'384716': '502253'},
    {'432135': '503414'},
    {'432611': '507374'},
    {'433194': '511743'},
    {'433843': '516278'},
    {'436675': '521476'},
    {'439333': '522080'},
    {'442577': '523100'},
    {'446412': '523558'},
    {'446777': '528381'},
    {'447310': '537194'},
    {'448486': '541583'},
    {'451001': '542961'},
    {'456523': '553357'},
    {'458986': '578094'},
    {'459677': '613767'},
    {'466198': '655215'},
    {'489546': '705182'},
    {'516272': '746540'},
    {'549024': '759232'},
    {'591025': '764099'},
    {'623761': '835965'},
    {'631792': '838702'},
    {'634999': '842905'},
    {'699738': '846865'},
    {'701246': '850748'},
    {'703536': '853313'},
    {'705785': '857004'},
    {'707757': '862252'},
    {'709148': '864340'},
    {'711264': '864934'},
    {'713923': '865585'},
    {'714032': '871462'},
    {'714385': '871740'},
    {'714712': '872031'},
    {'717673': '872900'},
    {'717843': '873258'},
    {'718013': '873491'},
    {'718622': '874414'},
    {'718803': '874749'},
    {'718943': '875056'},
    {'719453': '876158'},
    {'719679': '876792'},
    {'719832': '878450'},
    {'720492': '878723'},
    {'720677': '878944'},
    {'721483': '880788'},
    {'721707': '881135'},
    {'721832': '882585'},
    {'722648': '885749'},
    {'722890': '886218'},
    {'723789': '886375'},
    {'725700': '886608'},
    {'726078': '886801'},
    {'726179': '887492'},
    {'726304': '973398'},
    {'726461': '975232'},
    {'726815': '976020'},
    {'770767': '978487'},
    {'807721': '979250'},
    {'808970': '980047'},
    {'809469': '980510'},
    {'811155': '1002600'},
    {'811467': '1004940'},
    {'811916': '1005403'},
    {'812065': '1010981'},
    {'831617': '1012874'},
    {'832981': '1013171'},
    {'833159': '1049352'},
    {'836088': '1085533'},
    {'836918': '1121714'},
    {'837068': '1157895'},
    {'867121': '1194076'},
    {'897174': '1230257'},
    {'927227': '1266438'},
    {'957280': '1302619'},
    {'987333': '1303528'},
    {'1017386': '1306954'},
    {'1047439': '1307107'},
    {'1077492': '1308686'},
    {'1077803': '1309090'},
    {'1079275': '1310166'},
    {'1079502': '1310397'},
    {'1080525': '1310526'},
    {'1080808': '1311009'},
    {'1081462': '1311570'},
    {'1081608': '1312516'},
    {'1081700': '1312937'},
    {'1081866': '1313084'},
    {'1082197': '1315869'},
    {'1082768': '1316466'},
    {'1083011': '1322167'},
    {'1083177': '1322481'},
    {'1084424': '1325742'},
    {'1084770': '1328330'},
    {'1087728': '1329057'},
    {'1087971': '1356954'},
    {'1089994': '1357344'},
    {'1091343': '1367614'},
    {'1091760': '1371192'},
    {'1111668': '1373669'},
    {'1111875': '1374442'},
    {'1119995': '1375262'},
    {'1121944': '1375619'},
    {'1123640': '1382995'},
    {'1123962': '1383704'},
    {'1124391': '1384423'},
    {'1124548': '1389728'},
    {'1128535': '1392298'},
    {'1128893': '1392479'},
    {'1129204': '1393925'},
    {'1129641': '1423837'},
    {'1130932': '1470339'},
    {'1131055': '1519040'},
    {'1131722': '1572335'},
    {'1152131': '1629598'},
    {'1191276': '1692839'},
    {'1234214': '1758627'},
    {'1283463': '1821547'},
    {'1323905': '1879728'},
    {'1371648': '1911349'},
    {'1416778': '1942970'},
    {'1467474': '1974591'},
    {'1510221': '2006212'},
    {'1532572': '2037833'},
    {'1554923': '2069454'},
    {'1577274': '2101075'},
    {'1599625': '2132696'},
    {'1621976': '2136524'},
    {'1644327': '2141301'},
    {'1666678': '2145475'},
    {'1689029': '2150117'},
    {'1690966': '2179852'},
    {'1693308': '2191515'},
    {'1695364': '2195443'},
    {'1697474': '2200316'},
    {'1717658': '2204609'},
    {'1725045': '2209223'},
    {'1727078': '2213285'},
    {'1729279': '2216663'},
    {'1731618': '2221409'},
    {'1734005': '2225332'},
    {'1735898': '2276631'},
    {'1737574': '2277523'},
    {'1739868': '2278723'},
    {'1741893': '2280299'},
    {'1773680': '2280829'}, 
} 
"""

writeJsonToFile(outputFilename)