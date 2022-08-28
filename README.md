# YouTube downloader
> Note: this app is only for educational puropse, and I do not respond for any damages, caused by downloading others YouTube content. You use this app at your own risk.

### Prepare (optional):
Best way to make this app working is to add an alias to .bashrc (linux) or any eqivalent.
```shell
alias ytdl="python3 ~/PATH/ytdl.py ~/Downloads"
```
replace PATH with your path to the ytdl.py file, best way is to start from users home directory (~).

### Install Requirements:
If you don't have python installed (Ubuntu based Linux):
```shell
sudo apt install python3
```

After that you want to downoad all requirements:
```shell
pip install -r requirements.txt
```

Done! Now you can enjoy the app.

### Usage:
The app is terminal based so, everything has to be written in commands.
```
ytdl link [OPTIONS]
```

And without the alias:
```
python3 ~/PATH/ytdl.py ~/Downloads link [OPTIONS]
```

There are a few options to choose from:
short | long | description
---|---|---
-h | --help | shows the help table
-P | --playlist | Download the whole playlist (Url must include 'list=')
-l | --low | download lowest resolution
-r resolution | --res resolution | download in given resolution
-a | --audio | download as mp3

As default the resolution is the highest
