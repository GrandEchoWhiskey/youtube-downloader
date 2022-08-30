import pytube
from pytube.cli import on_progress
import sys
import os
import options

options.SHORT_JUST = 15
options.LONG_JUST = 20
options.HELP_NOTE = 'Usage: python3 ytdl.py target link [OPTIONS]'

audio_only = False
playlist = False
res = 'high'
yt_tar = '.'

def set_audio_only():
    """
    HELP: Download only in mp3 format
    """
    global audio_only
    audio_only = True

def set_playlist():
    """
    HELP: Download a whole playlist
    """
    global playlist
    playlist = True

def set_resolution_low():
    """
    HELP: Get lowest video resolution
    """
    global res
    res = "low"

def set_resolution(resolution: 'resolution'):
    """
    HELP: Set own resolution
    """
    global res
    res = resolution

def set_target(tar: 'target'):
    """
    HELP: Set the target
    """
    global yt_tar
    yt_tar = tar.replace('\"', '')

options.add('t', 'target', set_target)
options.add('a', 'audio', set_audio_only)
options.add('P', 'playlist', set_playlist)
options.add('l', 'low', set_resolution_low)
options.add('r', 'res', set_resolution)

def main():

    try:
        options.exec() 
        if len(sys.argv) < 3:
            raise Exception
    except:
        sys.exit('Use: "python3 ytdl.py -h" for help.')

    target: str = sys.argv[1]
    link: str = sys.argv[2].replace("https://", '')
    downloads: list = []

    if playlist:
        try:
            start = link.index('list=')
            endl = start
            while endl < len(link):
                if link[endl] in ['&', '#']:
                    break
                endl += 1
            pllst = link[start:endl]
            link = link[:link.index('?')+1]+pllst
            p = pytube.Playlist(link)
            downloads.extend(list(p.video_urls))
        except Exception as e:
            sys.exit(f"Unable to set playlist: {e}")

    else:
        downloads.append(link)
    
    for i, url in enumerate(downloads):
        try:
            yt = pytube.YouTube(url, on_progress_callback=on_progress)
            ys = yt.streams
        except:
            sys.exit("Unable to set YouTUbe stream")
        
        print(f"{i+1}. {yt.title}".ljust(71, ' '))
        
        if res == 'high':
            stream = ys.get_highest_resolution()
        elif res == 'low':
            stream = ys.get_lowest_resolution()
        else:
            try:
                stream = ys.get_by_resolution(int(res))
            except:
                sys.exit("Resolution: " + res + " does not exist.")            

        if audio_only:
            stream = ys.get_audio_only()

        try:
            outfile = stream.download(target)
            if audio_only:
                base, ext = os.path.splitext(outfile)
                newfile = base + '.mp3'
                os.rename(outfile, newfile)
        except:
            sys.exit("Unable to save the file")

if __name__ == "__main__":
    main()