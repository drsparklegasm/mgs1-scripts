import RadioDatTools as rDat

rDat.getRadioData('RADIO-usa.DAT')
frequency = rDat.getFreq(0)
print(frequency)