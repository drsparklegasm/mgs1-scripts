#!/bin/python3
# Types Reference 
"""
bytestream.read(n)  # where n is the number of bytes to read. 
                    # Yields a bytes type. 

"""

import io, struct

filename = "/home/solidmixer/projects/mgs1-undub/RADIO-usa.DAT"
#filename = "RADIO-jpn.DAT"

offset = 0
# offset = 293536 # Freq 140.85

radioFile = open(filename, 'rb')
output = open("output.txt", 'w')

offset = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = radioData.__len__()

"""
a = b'whatsthedealio'

# print(type(a)) // Bytes

print(a[1]) # prints decimal value
print(str(a[1])) # prints STRING of decimal value
print(a[1].to_bytes()) ##  yields b'h' 
print(a.hex()) # count of bits

print(a[0].to_bytes().hex()) ## shows the actual hex you want

b = "Be careful, Snake. That air lock is set\r\nwith infrared sensors."
print(b)

"""
"""
a = radioData[11] # This is an INT
print(type(a))
print(a.to_bytes()) # you can use .to_bytes() to show the byte hex
"""

header = radioData[0:12]
print(type(header.hex()))
print(header.hex()) # Will work if there are no incorrect bytes

