#!/bin/python3
# Types Reference 
"""
bytestream.read(n)  # where n is the number of bytes to read. 
                    # Yields a bytes type. 

"""

import io, struct

a = b'whatsthedealio'

# print(type(a)) // Bytes

print(a[1]) # prints decimal value
print(str(a[1])) # prints STRING of decimal value
print(a[1].to_bytes()) ##  yields b'h' 
print(a.hex()) # count of bits

print(a[0].to_bytes().hex()) ## shows the actual hex you want

b = "Be careful, Snake. That air lock is set\r\nwith infrared sensors."
print(b)