
Here's a bunch of ideas for how to proceed:

1. Turn existing parser into a file read/export tool
2. Fork that file to make an XML element writer
3. Use the xml element writer to re-compile codec calls into a new radio file


Identifying calls:
1. We could make a hash function that will count the order of functions as a unique structure in the call, and hash them. Theoretically this should match. Ie.

Ex: 140.85
Call: ANIMATE ANIMATE VOX DIALOGUE (16) Add freq END

Codec Call Finder

Set up call types as STRUCTs?
Would this help me?

## 