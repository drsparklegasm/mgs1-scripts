Tasks:
- [ ] Handle other commands
- [ ] 
- [ ] Ensure offsets are correct
- [ ] Account for `00` being an end of line delination
- [ ] Create re-compiler
- [ ] Find a way to trace offsets
- [ ] Verify where offsets occur in stage.dir



Notes on stage.dir:
- The code for the codec call is `01 XX XX 0A ` followed by the HEX offset of the start of the call, so for example:
- 140.85 conversation is found in Stage.dir at hex `0x744858` and again at `0x7473B5` 

| Frequency | Offset | hex offset | Length |     |
| --------- | ------ | ---------- | ------ | --- |
| Meryl     | 0      | 0x0        |        |     |


###  Learning Example: If statements

`ff10` represents an IF statement, and an easy one to check is the one after the elevator ride when Colonel Campbell either praises or chastizes snake for his speed.

```
Call Header: 140.85, offset = 294379, length = 1316, UNK0 = 5f00, UNK1 = 0000, UNK2 = 0000, Content = 37055f0000000000800524
	ANIMATE -- Offset: 294390, length = 10 FACE = 21ca, ANIM = f73b, FullContent: ff03000821caf73b0000
	ANIMATE -- Offset: 294400, length = 10 FACE = 6588, ANIM = 3320, FullContent: ff030008658833200000 // 20 
	VOX START! -- Offset: 294410, LengthA = 81, LengthB = 74, Content: ff0200510000202280004a // Container: 
		Dialogue -- Offset = 294421, Length = 22, FACE = 21ca, ANIM = f73b, UNK3 = 0000, breaks = False, 	Text: b"It's Snake.\x00" // 22
		Dialogue -- Offset = 294443, Length = 49, FACE = 21ca, ANIM = f73b, UNK3 = 0000, breaks = False, 	Text: b"I'm in front of the disposal facility.\x00" //  71
		NULL (Command! offset = 294491) // 72, this makes ONE null to end VOX
	IF_CHECK -- Offset = 294493, length = 412, Content = ff10019a3016118000b60201310b118000b8010258310b311331008000c5 // first value 410, 2nd length should be 197, 195 following
		VOX START! -- Offset: 294523, LengthA = 84, LengthB = 77, Content: ff0200540000203480004d (86) 11 bytes
			Dialogue -- Offset = 294534, Length = 28, FACE = 6588, ANIM = 3320, UNK3 = 0000, breaks = False, 	Text: b'Excellent, Snake.\x00' + 28 = 39
			Dialogue -- Offset = 294562, Length = 46, FACE = 6588, ANIM = 3320, UNK3 = 0000, breaks = False, 	Text: b"Age hasn't slowed you down one bit.\x00" // 85
			NULL (Command! offset = 294607) makes 86 to end the VOX command, NO NULL BEFORE NEXT IF!
		IF_CHECK -- Offset = 294609, length = 108, Content = ff10 006a 3011 1401 0387 1180 0000 0200 3109 3113 3100 8000 54 /// (25 header) 106 first one, 84 // first if 170, now 195
			VOX START! -- Offset: 294634, LengthA = 79, LengthB = 72, Content: ff02004f00002142800048 + 81
				Dialogue -- Offset = 294645, Length = 69, FACE = 21ca, ANIM = f73b, UNK3 = 0000, breaks = True, 	Text: b'Thanks to the VR training I did on\\r\\nboard the Discovery.\x00' 
				NULL (Command! offset = 294713)
			Null! (Main loop) offset = 294715
		Null! (Main loop) offset = 294716
	Null! (Main loop) offset = 294717
ELSE -- Offset = 294718, length = 5, Content = ff1180 
	VOX START! -- Offset: 294723, LengthA = 178, LengthB = 171, Content: ff0200b20000204d8000ab
		Dialogue -- Offset = 294734, Length = 33, FACE = 6588, ANIM = 5e56, UNK3 = 0004, breaks = False, 	Text: b'That took a long time.\x00'
		Dialogue -- Offset = 294767, Length = 49, FACE = 6588, ANIM = 5e56, UNK3 = 0000, breaks = False, 	Text: b"I guess you're feeling a little rusty.\x00"
		Dialogue -- Offset = 294816, Length = 23, FACE = 21ca, ANIM = f73b, UNK3 = 0000, breaks = False, 	Text: b"Don't worry.\x00"
		Dialogue -- Offset = 294839, Length = 63, FACE = 21ca, ANIM = f73b, UNK3 = 0000, breaks = True, 	Text: b"It's been a while but it's all coming\\r\\nback to me.\x00"
		NULL (Command! offset = 294901) THIS ends the first IF! (?)
	Null! (Main loop) offset = 294903
Null! (Main loop) offset = 294904


VOX START! -- Offset: 294905, LengthA = 796, LengthB = 789, Content: ff02031c00002079800315
MUS_CUES -- Offset = 294916, length = 10, Content = ff060008000000004a00
ANIMATE -- Offset: 294926, length = 10 FACE = 7c90, ANIM = 0000, FullContent: ff0300087c9000000000
Dialogue -- Offset = 294936, Length = 48, FACE = 9475, ANIM = 21f3, UNK3 = 0004, breaks = False, 	Text: b"How's that Sneaking Suit working out?\x00"Dialogue -- Offset = 294936, Length = 48, FACE = 9475, ANIM = 21f3, UNK3 = 0004, breaks = False, 	Text: b"How's that Sneaking Suit working out?\x00"
```

Extract from one of the versions of my script is above. 

IFs are not followed by a null, but can be followed by another IF
The first is the ENTIRE if statement length, which includes sub-if;s? 
It also includes the else statement
Basically the first few bytes of the IF cover the whole switch statement
The last two only cover that first if statement. 
Everything in the middle is the eval ? Haven't decoded that yet.


## Script conventions

Here are some naming conventions I try to keep to in the script, as well as a description of some of the definitions used. 

| term/variable  | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |     |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| offset         | In the global sense "offset" is our pointer for how far along in the file we are. This is passed to functions for decoding individual commands, and we'll try to leave it static.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |     |
| length         | Length in most context is the length of the entire command. In small commands such as ANIMATE or DIALOGUE/SUBTITLE, the length is written in the 3rd and 4th byte of the sequence, but it is two shorter than how I define it. <br>Ex:<br>`ff 01 00 17 21 ca 59 F8 00 00 This is Snake.\x00`<br>ff01 is the COMMAND<br>0017 Is the length for this command, but it only encompasses the 3rd byte through the \x00 terminating the command/string. So, for purposes of my script length will be 2 longer than this value (regardless of where the command length comes from).                                                                                                                                                                             |     |
| length2        | (To be implemented) length2 is going to be a stand in for the container length; In IF commands and VOX commands, we have a length given at the end of the header.<br>Ex:<br>`ff 02 03 1a 00 00 1f 25 80 03 13`<br>Here we have a "length" of 0x031a, and the final bytes of the header are '80 03 13'. This like length is the length of the content, including the length bytes of 2, and for the purposes of my script will be -2 to the written value. This is different from Length as we want to cleanly add "header + length2" for the full command length (rather than hard code an extra +/- later.<br>for more info see HEADER<br>Note that the difference between 0x031a and 0x0313 is 7, which is the 7 bytes difference between both counts. |     |
| header         | "Header" is the length of a command or conditional header, leading up to the contents, which is likely other commands. Ex:<br>`ff 02 03 1a 00 00 1f 25 80 03 13` is a file header for 140.85, so I would count header as 11 bytes. This includes both length values (which will have a difference between bytes 3 and the last two)                                                                                                                                                                                                                                                                                                                                                                                                                      |     |
| layerNum       | (likely legacy) In development, this is used to keep track of the layers deep we are. Some commands (IF, VOX, etc) are header-based, with content. The content can have an additional depth with this. Initially this is used to track layers deep that we are in embedded content.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |     |
| Command Byte   | When gathering a command byte, we assume pointer is at an FF. It makes more sense conventionally that the FF is a command indicator, so we will generally count a command as FF 02 rather that 02. A list of command bytes is in the dict `commandNamesEng`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |     |
| radioFile      | ioBuffer for the radio file being ingested                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |     |
| radioData      | a full read of the radio file (i felt it easier to work with a bytestring than continuous seeking/reading from disk)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |     |
| fileSize       | (int) length (# of bytes) of the radioFile, used for pointer position tracking                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |     |
| filename       | path to radio.dat. If no path, assume its in the local dir.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |     |
| outputFilename | Output filename (text or xml, depending on ending format i use                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |     |
| container      | In this context, most commands contain content of some kind, some of variable length. If i say container, it implies that the command contains other commands inside its content length. If a command is a container, it will generally have a tailing \x00 to define the end.                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |     |
| 140.85         | If i mention this I'm usually referring specifically to the first call in the dock ("This is snake. Colonel can you hear me?") which is an example I've used frequently as its a striaghtforward example and easy to digest when learning the format.<br><br>Unlike command headers, it does not have a \x00 trailing, probably because calls are compiled back to back in radio.dat                                                                                                                                                                                                                                                                                                                                                                     |     |
| freq           | the frequency of the radio/codec call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |     |
| Call Header    | Header for the call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |     |
| "static"       | Static length means length is ALWAYS the same number of bytes (headers, FF 06, etc.)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |     |
| line           | For decompiling a command, line is a bytestring that encompasses the command byte through the trailing \x00                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |     |
### Toggles

| Toggles:     | Description                                                                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| jpn          | Are we reading a japanese file? If so, engage automatic translation of contents.                                                                          |
| indentToggle | Toggles indenting for each container. <br>                                                                                                                |
| debugOutput  | Adds additional terminal logging and Errors. Basically used for me to check if everything was following conventions or if there were things yet to define |
|              |                                                                                                                                                           |

## Header overviews:

Most of these will come from 140.85 or ???. Offsets are from the USA version, D1

| Command  | Name         | is container?* | Static Header? | Static length? | Example                                            | offset (int) |     |
| -------- | ------------ | -------------- | -------------- | -------------- | -------------------------------------------------- | ------------ | --- |
| `FF 01`  | SUBTITLE     | No             | Yes            | No             | `ff 01 00 17 21 ca 59 F8 00 00 This is Snake.\x00` | 293578       |     |
| `FF 02`  | VOX_START    | Yes            | Yes            | No             | `ff 02 03 1a 00 00 1f 25 80 03 13`                 | 293567       |     |
| `FF 03`  | ANIMATE      | No             | Yes            | Yes            | `ff 03 00 08 21 ca 59 f8 00 00`                    | 293547       |     |
| `FF 04`  | ADD FREQ     | No             | Yes            | No             | `ff 04 00 0d 37 05 43 41 4d 50 42 45 4c 4c 00`     | 294363       |     |
| `FF 05`  | ?            |                |                |                |                                                    |              |     |
| `FF 06`  | MUSIC CUE?   |                |                |                |                                                    |              |     |
| `FF 07`  | PROMPT       |                |                |                |                                                    |              |     |
| `FF 08`  | SAVEGAME ?   |                |                |                |                                                    |              |     |
| `FF 10`  | IF statement | Yes            | No             | No             |                                                    |              |     |
| `FF 11`  | ELSE IF      | Yes            | Yes            | No             |                                                    |              |     |
| `FF 12`  | ELSE ...     | Yes            | Yes            | No             |                                                    |              |     |
| `FF 30`  | Case switch  |                |                |                |                                                    |              |     |
| `FF 31`  | Case X       |                |                |                |                                                    |              |     |
| `FF 32`  | ?            |                |                |                |                                                    |              |     |
| `FF 40`  | EVAL ?       |                |                |                |                                                    |              |     |
| `FF 80`? |              |                |                |                |                                                    |              |     |
| `FF FF`? |              |                |                |                |                                                    |              |     |
\* Container implies that it contains other commands. For example `FF 01` is variable and contains a dialogue line, but not other commands, so its a form of container but not defined here as a container. 


## Understanding the Mei Ling clusterf


# Translating the Japanese Hex Code

Freq 140.85 Conversation:
