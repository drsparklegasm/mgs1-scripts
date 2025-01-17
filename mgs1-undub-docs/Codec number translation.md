# Codec number translation

140.15 == 36BF
140.85 == 3705
140.96 == 3710
141.12 == 3720
141.80 == 3674
141.52 == 3748

# Face Codes (for reference):
Snake/scuba  ==  59F8
Campbell == 3320

## Command codes
01 == Line of dialogue
02 == ???
03 === Initialize ? Per code, animation
04 ADD CONTACT
05 Memory save
06 Audio
07 Prompt
08 SAVE ?
009 ?????
10 IF ...
11 ELSE
12 ELSEIF

30 SWITCH ?
40 EVAL
80 SCRIPT 

FF End or \n in code ?

# ORDER OF OPERATIONS (Opening codec 140.85)

1. Frequency -- 2 bytes, then 00 00 
6 bytes ?
Checksum of conversation (2 bytes) 
    Start includes these bytes
    End goes all the way to the start of the next codec

Each message in the codec call:

Message Header (8) Bytes
    First 2 == Length for the message (starting after this byte, including ending bytes of `00 FF 01`)
    2 == We don't knwo ? (Corresponds to who speaks next, maybe facial animation? Instruction?)
    2 == Face (from face.dat)
    2 == `00 00` // so far consistent
Message (with line breaks as 80 23 80 4E)
(End of message) == 00 FF 01 

----

Conversatio end:
`00 00 FF 04   Message (with line breaks as 80 23 80 4E)
(End of message) == 00 FF 04 FF 00 0D



EX: Introduction (Freq 140.85)

`37 05 4B 00 02 75 00 00 80 03 42 FF`
Freq: `37 05`
`4B 00?

`80 03 42` # Script is 03 42 length

`03 00 08 21 CA 59 F8 00 00 FF`


`03 00 08 65 88 33 20 00 00 FF`


`02 03 1A 00 00 1f 25 80 03 13 FF`
`02` Command 02 ?
`03 1A` MESSAGE LENGTH all the way to `FF 04` 3 bytes from the end of the conversation
`00 00 1f 25` ??? Maybe audio location, `1f 25`
`80` # Script starts:
`03 13` Another length from after the `FF 01` until the end of `04 00 0D` right before the next codec call (`37 05`)

# Dialogue
`01` # Command for Line of dialogue
Template:
`00 17 21 CA 59 F8 00 00`
`00 17` Message is 17 bytes long
`21 CA` == Animation?
`59 F8` == Face 
`00 00` == Intentional spacer?


8 or 9 byte header if including the 01, unless its FF 01 from before ?

`00 17 21 CA 59 F8 00 00`
`00 17` Message is 17 bytes long
`21 CA` == Snake Animation?
`59 F8` == Face (Snake)
`00 00` == NOOP

This is Snake.
`00 FF` # End line

`01 00 22 21 CA 59 F8 00 00 43`

`01` == ??
`00 22` Message is 17 bytes long
`21 CA` == ??? Snake animation?
`59 F8` == Face (Snake)
`00 00` == NOOP
Colonel, can you hear me?
`00 FF 01` # End line

`01 00 18 65 88 33 20 00 00 4C 6F 75 64 20 61 6E 64 20 63 6C 65 61 72 2E 00 FF`

`01` ??
`00 18` 18 bytes
`65 88` 
`33 20` Colonel Face
`00 00`
Loud and clear.
`00 FF 01`  # end line

`00 25 65 88 33 20 00 00` 
65 88 
33 20
`57 68 61 74 27 73 20 74 68 65 20 73 69 74 75 61 74 69 6F 6E 2C 20 53 6E 61 6B 65 3F 00 FF 01`                       
 W  h  a  t  '  s  _  t  h  e     s  i  t  u  a  t  i  o  n  ,  _  S  n  a  k  e  ?  [E O L?]




...

`00 2A 21 CA 59 F8 00 00` 

`47 6F 74 20 69 74 2E 80 23 80 4E 4F 6B 61 79 2E 20 49 27 6D 20 72 65 61 64 79 20 74 6F 20 67 6F 2E 00 00 FF` 
"G  o  t     i  t  .  \r   \n     O  k  a  y  .     I  '  m     r  e  a  d  y     t  o     g  o  .  

`04 00 0D`
`04` command ?
`00 0D` Instruction ?

`04 00 0D 37 05 43 41 4D 50 42 45 4C 4C 00 00`
"add number 140.85 CAMPBELL "

=====


`37 05 4B 00 02 75 00 00 80 03 42 FF 03 00 08 21 CA 59 F8 00 00 FF 03 00 08 65 88 33 20 00 00 FF 02 03 1A 00 00 1F 25 80 03 13 FF 01 00 17 21 CA 59 F8 00 00 54 68 69 73 20 69 73 20 53 6E 61 6B 65 2E 00 FF 01 00 22 21 CA 59 F8 00 00 43 6F 6C 6F 6E 65 6C 2C 20 63 61 6E 20 79 6F 75 20 68 65 61 72 20 6D 65 3F 00 FF 01 00 18 65 88 33 20 00 00 4C 6F 75 64 20 61 6E 64 20 63 6C 65 61 72 2E 00 FF 01 00 25 65 88 33 20 00 00 57 68 61 74 27 73 20 74 68 65 20 73 69 74 75 61 74 69 6F 6E 2C 20 53 6E 61 6B 65 3F 00 FF 01 00 43 21 CA 59 F8 00 00 4C 6F 6F 6B 73 20 6C 69 6B 65 20 74 68 65 20 65 6C 65 76 61 74 6F 72 20 69 6E 20 74 68 65 20 62 61 63 6B 20 69 73 80 23 80 4E 74 68 65 20 6F 6E 6C 79 20 77 61 79 20 75 70 2E 00 FF 01 00 1C 65 88 33 20 00 08 4A 75 73 74 20 61 73 20 49 20 65 78 70 65 63 74 65 64 2E 00 FF 01 00 3C 65 88 33 20 00 00 59 6F 75 27 6C 6C 20 68 61 76 65 20 74 6F 20 74 61 6B 65 20 74 68 65 20 65 6C 65 76 61 74 6F 72 20 74 6F 80 23 80 4E 74 68 65 20 73 75 72 66 61 63 65 2E 00 FF 01 00 27 65 88 33 20 00 04 42 75 74 20 6D 61 6B 65 20 73 75 72 65 20 6E 6F 62 6F 64 79 20 73 65 65 73 20 79 6F 75 2E 00 FF 01 00 2D 65 88 33 20 00 00 49 66 20 79 6F 75 20 6E 65 65 64 20 74 6F 2C 20 63 6F 6E 74 61 63 74 20 6D 65 20 62 79 20 43 6F 64 65 63 2E 00 FF 01 00 21 65 88 33 20 00 00 54 68 65 20 66 72 65 71 75 65 6E 63 79 20 69 73 20 31 34 30 2E 38 35 2E 00 FF 01 00 43 65 88 33 20 00 00 57 68 65 6E 20 79 6F 75 20 77 61 6E 74 20 74 6F 20 75 73 65 20 74 68 65 20 43 6F 64 65 63 2C 80 23 80 4E 70 75 73 68 20 74 68 65 20 53 65 6C 65 63 74 20 42 75 74 74 6F 6E 2E 00 FF 01 00 3D 65 88 33 20 00 00 57 68 65 6E 20 77 65 20 6E 65 65 64 20 74 6F 20 63 6F 6E 74 61 63 74 20 79 6F 75 2C 80 23 80 4E 74 68 65 20 43 6F 64 65 63 20 77 69 6C 6C 20 62 65 65 70 2E 00 FF 01 00 3F 65 88 33 20 00 00 57 68 65 6E 20 79 6F 75 20 68 65 61 72 20 74 68 61 74 20 6E 6F 69 73 65 2C 20 80 23 80 4E 70 72 65 73 73 20 74 68 65 20 53 65 6C 65 63 74 20 42 75 74 74 6F 6E 2E 00 FF 01 00 51 65 88 33 20 00 00 54 68 65 20 43 6F 64 65 63 27 73 20 72 65 63 65 69 76 65 72 20 64 69 72 65 63 74 6C 79 80 23 80 4E 73 74 69 6D 75 6C 61 74 65 73 20 74 68 65 20 73 6D 61 6C 6C 20 62 6F 6E 65 73 20 6F 66 20 79 6F 75 72 20 65 61 72 2E 00 FF 01 00 30 65 88 33 20 00 00 4E 6F 20 6F 6E 65 20 62 75 74 20 79 6F 75 20 77 69 6C 6C 20 62 65 20 61 62 6C 65 20 74 6F 20 68 65 61 72 20 69 74 2E 00 FF 01 00 2A 21 CA 59 F8 00 00 47 6F 74 20 69 74 2E 80 23 80 4E 4F 6B 61 79 2E 20 49 27 6D 20 72 65 61 64 79 20 74 6F 20 67 6F 2E 00 00 FF 04 00 0D 37 05`


## Example 2 In front of disposal Facility

`37 05 43 41 4D 50 42 45 4C 4C 00 00 37 05 5F 00 00 00 00 00 80 05 24 `
`FF 03 00 08 21 CA F7 3B 00 00 `
`FF 03 00 08 65 88 33 20 00 00 `
`FF 02 00 51 00 00 20 22 80 00 4A 

`FF 01 00 14 21 CA F7 3B 00 00` # Snake message header
`49 74 27 73 20 53 6E 61 6B 65 2E 00` # "It's Snake" 

`FF 01 00 2F 21 CA F7 3B 00 00 ` # Header
`49 27 6D 20 69 6E 20 66 72 6F 6E 74 20 6F 66 20 74 68 65 20 64 69 73 70 6F 73 61 6C 20 66 61 63 69 6C 69 74 79 2E` # "I'm in front of the disposal facility."  `00 00`

IF sequence...



`FF 10 01 9A 30 16 11 80 00 B6 02 01 31 0B 11 80 00 B8 01 02 58 31 0B 31 13 31 00 80 00 C5 FF 02 00 54 00 00 20 34 80 00 4D  
`FF 01 00 1A 65 88 33 20 00 00` Campbell header
`45 78 63 65 6C 6C 65 6E 74 2C 20 53 6E 61 6B 65 2E 00` # Excellent Snake

`00 2C 65 88 33 20 00 00` Campbell Header
`41 67 65 20 68 61 73 6E 27 74 20 73 6C 6F 77 65 64 20 79 6F 75 20 64 6F 77 6E 20 6F 6E 65 20 62 69 74 2E 00` # Age hasn't slowed you down one bit."

10 00 6A 30 11 14 01 03 87 11 80 00 00 02 00 31 09 31 13 31 00 80 00 54 FF 02 00 4F 00 00 21 42 80 00 48 FF 01 00 43 21 CA F7 3B 00 00 54 68 61 6E 6B 73 20 74 6F 20 74 68 65 20 56 52 20 74 72 61 69 6E 69 6E 67 20 49 20 64 69 64 20 6F 6E 80 23 80 4E 62 6F 61 72 64 20 74 68 65 20 44 69 73 63 6F 76 65 72 79 2E 00 00 00 00 00 FF 11 80 00 B7 FF 02 00 B2 00 00 20 4D 80 00 AB FF 01 00 1F 65 88 5E 56 00 04 54 68 61 74 20 74 6F 6F 6B 20 61 20 6C 6F 6E 67 20 74 69 6D 65 2E 00 FF 01 00 2F 65 88 5E 56 00 00 49 20 67 75 65 73 73 20 79 6F 75 27 72 65 20 66 65 65 6C 69 6E 67 20 61 20 6C 69 74 74 6C 65 20 72 75 73 74 79 2E 00 FF 01 00 15 21 CA F7 3B 00 00 44 6F 6E 27 74 20 77 6F 72 72 79 2E 00 FF 01 00 3D 21 CA F7 3B 00 00 49 74 27 73 20 62 65 65 6E 20 61 20 77 68 69 6C 65 20 62 75 74 20 69 74 27 73 20 61 6C 6C 20 63 6F 6D 69 6E 67 80 23 80 4E 62 61 63 6B 20 74 6F 20 6D 65 2E 00 00 00 00 FF 02 03 1C 00 00 20 79 80 03 15 FF 06 00 08 00 00 00 00 4A 00 FF 03 00 08 7C 90 00 00 00 00 FF 01 00 2E 94 75 21 F3 00 04 48`