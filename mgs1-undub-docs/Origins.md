
When MGS2 was being developed, I remember the trailers I'd see would be completely in Japanese. It had this allure, I guess, and even though by that point I was mostly raised on 90s action movies. I was excited about Metal Gear Solid 2, but I think that curiosity stuck with me about the Japanese version. 

I was excited back when the Legacy collection came out. I had all the games already, but I saw play-asia had the Japanese legacy collection in stock, and given the PS3 was finally a region-free console, I thought I saw it as my chance to finally play the series in Japanese. 

![[legacyCollection.jpg]]

Unfortunately for me, while yes you could play the games in Japanese, it was exclusively Japanese. There were no english subtitles available. It was disappointing, but hey, me being such a nerd about the series I pretty much had the script memorized, I played through it anyway. Still, for some of the later games I had not played through 30 times, I wanted a way to be able to experience the Japanese voice actors performance, but still understand what was happening more than just contextually. 

### Inspiration

I figured maybe one day I'd hack the game apart and inject the subtitles. I figured it couldn't be that hard, but I was definitely far from ready to do something like that. There were a lot of free utilities i'd used to try ripping music. But injecting text was far more difficult for someone who's just got a passing fancy. Plus, back then it's not like I really even knew what a hex editor was. 

But there were some things along the way that inspired me. I was always hugely impressed by the efforts of the team that translated Policenauts into english. Slowbeef actually has a long series of his own blog posts chronicling his own journey injecting english into that game. Its actually a great read, and super entertaining. I'll leave a [link to part 1.](https://lparchive.org/Policenauts/Update%2042/) 

Anyway, Slowbeef admits to being an actual computer programmer. Whereas I majored in music performance. I just have the passing fancy at computers; i took Java in high school, and in my first job I went down such a long linux rabbit hole I'm still looking for the other end. But as I had mentioned my fascination taking things apart and seeing how they worked, I started also falling down the rabbit hole of creators on Youtube who talk about game development, discuss how glitches worked in NES games, people who build their own bread board computers, and such. Between all of these voices, I started to pick up a few things. 

So long story short, I always love watching different hackers taking things out of MGS2. Actually there were a few glitches I found via youtube and rushed back to my console to try. In particular the door glitch in MGS2 where you can do Raiden's punch combo and edge into the loading zone. 

And I'd see a lot of different translation projects get up and off the ground. But the biggest problem, at least in my mind, was that Metal Gear Solid wasn't one of these projects because MGS did get an official translation and release. We weren't going to see hackers waste their time translating a game that's already been translated. 

So i figured I'd just have to do it myself. The more I looked into various tools, the more I saw that there's been a lot of advances, but with several different versions out (and the Master collection just released) there was a wide spread for what tool worked for what. 

I've always known from the get go, my choice is to always work with the original version. So for Metal Gear Solid, Playstation, and 2 and 3 then we're headed for PS2. Why? There's little things about each version that don't translate well to the later releases. For a full list you can look here on the [community bug tracker](https://docs.google.com/spreadsheets/d/1WhQSRpkC_A9wBDV0o-Pohh1dMhL1H6nbVzvdluIVWrw/edit?gid=0#gid=0) to see how many things still have yet to be resolved, even things that persist since the HD collection on PS3. Plus, especially the more I learned about MGS2 and all that it was meant to be a wool-over-your-eyes reveal that Snake was not the main character, I wanted to see what a Japanese person would've experienced on day one. In particular, one key feature is the game selection prompt. We're asked whether we played the previous game, and if not, it completely skips the Tanker chapter. Isn't it worth experiencing those nuances present in the original version?

Anyway. I'm sure that my tools and work will help pave the way for the same things to be done with the HD collections. I just have a focus on the originals first. Besides, master collection actually reuses the original. 

Anyway, in researching tools I stumbled on many things, and many talented people all hacking the same games with the same reference I had for the series. I had a conversation with someone else who was looking into it who said, "Why not just replace the audio in the English version with the sounds from the Japanese?"

Great idea, but it wasn't going to work. I've done it easily with the Demo file extractor. You can inject the japanese audio into the english game. And with no issues. But the issue I did see? The timing was off. I knew that was going to be an issue because the timing isn't the same on Codec dialogue either. In fact the whole codec conversation from localizations will ebb and flow in their own way. 

And if I was going to have to fix the timing, it wasn't worth going only half way. We might as well start with Japanese version, and go for gold translating it. 

So what follows is my own journey into Romhacking. 
### References

Just to name a few of the relevant video creators, I'll throw a bunch of links to their channels below. It's not so much a dedication 

Red Code Interactive
https://www.youtube.com/@RedCodeInteractive

Retro Game Mechanics Explained
https://www.youtube.com/@RGMechEx

Ben Eater
https://www.youtube.com/@BenEater

Modern Vintage Gamer
https://www.youtube.com/@ModernVintageGamer

If you're at all curious about Linux...
https://www.youtube.com/@tutoriaLinux

And I'll name another few that you should probably know already... Slowbeef of course. Son of a Glitch, Boundary Break. Speedrunners, and other game exploiters, and exploit finders. Linus Tech Tips and all the other tech youtubers who like taking things apart. 






