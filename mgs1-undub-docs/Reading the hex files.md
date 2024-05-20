( This is an early attempt, leaving here for posterity)

Dialogue has some patterns. 

At the start of a line of dialogue is:
`39 C3 00 00`

At the end of each dialogue segment is this:
`2E 00 00 FF`

Line breaks are as follows:
`80 23 80 4E`

Shift-JIS for SNAKE
スネーク
`83 5D / 83 93 / 83 4B`
`1000 0011 0101 1101 / 1000 0011 1001 0011 / 1000 0011 0100 1011`


"This is snake"
59 F8 00 00 (intro) 81 13 81 21 81 49 82 19 82 2D D0 06 82 0F D0 17 (outtro) D0 03 00 FF

"This is snake"

| Characters | Hex     | bytes (Radio.dat)     | Hex (Shift JIS) | Bytes (Shift JIS)     |
| ---------- | ------- | --------------------- | --------------- | --------------------- |
| Ko         | `81 13` | `1000 0001 0001 0011` |                 |                       |
| Chi        | `81 21` | `1000 0001 0010 0001` |                 |                       |
| Ra         | `81 49` | `1000 0001 0100 1001` |                 |                       |
| Su         | `82 19` | `1000 0010 0001 1001` | `83 5D`         | `1000 0011 0101 1101` |
| Ne         | `82 2D` | `1000 0010 0010 1101` | `83 93`         | `1000 0011 1001 0011` |
| --         | `D0 06` |                       |                 |                       |
| ku         | `82 0F` | `1000 0010 0000 1111` | `83 4B`         | `1000 0011 0100 1011` |
| .          | `D0 17` |                       |                 |                       |
|            |         |                       |                 |                       |


Su - Ne - --- - Ku
8219 822D D006 820F


This appears a lot so it's probably right. Actually i can trace it to Campbells other message


https://discord.com/channels/421360471610884096/421367125756608532/1171586160263438366

Tasks 
1. Create a script to extract the binary
2. use the cipher to translate them into their japanese character set
3. include the offsets so that we can get back to finding them
4. Translate it to english to know which spots are being replaced
5. ???

