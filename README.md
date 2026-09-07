# youtube-chat-vm
script to do Chat uses windows!

# can i use this?
yes but please credit me.
you can also just use the chatbox by switching to the chatbox branch. (the chatbox branch doesnt get updated often because i dont update the chatbox often)

if you dont know how to credit me you can use these:
```
script made by jimhasaburger on github (github.com/jimhasaburger/youtube-chat-vm)
```
```
script originally made by jimhasaburger on github (github.com/jimhasaburger/youtube-chat-vm), modified.
```

you absolutely dont need to use these, its enough to give the link or my username.

# can i help?
of course. use pull requests.

# setup
get virtualbox if you dont already.

you will have to go to install directory and go to sdk and the one folder in there.
then run:
```
pip install setuptools
pip install .
```
now you have vboxapi. do this:
```
pip install virtualbox pyvbox pytchat pywin32 flask socketio
```
then edit config.json
and run the script

report any issues with running to the issues tab.

# commands list for your stream:

```
COMMANDS:
(you can chain them)

!help

!key [key_name]

!repeat [key] [times]

!combo [key_names...] (SEPERATE KEYS WITH SPACE!)

!type [text]

!send [text]

!move [x] [y]

!scroll [num]

!click

!rclick

!mclick

!revert

!restart

!start
```

# KNOWN BUGS:

- chatbox randomly scrolls to random places
- sometimes stops receiving messages from specific people
