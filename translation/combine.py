import os

a = open('unique graphics', 'r')
b = open('kanji.txt', 'r')
c = open('Output.txt', 'w')

for lineA, lineB in zip(a, b):
    c.write(f'\t"{lineA.strip()}": "{lineB.strip()}",\n')

c.close()
