import pytube
from pytube.cli import on_progress
import sys
import os
import options

options.SHORT_JUST = 15
options.LONG_JUST = 20
options.USAGE_NOTE = 'usage: python3 ytdl.py [options]'
options.HELP_NOTE = 'Use: "python3 ytdl.py -h" for help.'

links = []
audio_only = False
vid_resolution = 'high'
vid_target = '.'

def rename_file(name):
    name = name.replace(' ', '-')
    for char in '!@#$%^&*()+=<>,.?/\'\"\\|{}[]~`':
        name = name.replace(char, '')
    return name

@options.option('a', 'audio')
def set_audio():
    """Set audio only mode (.mp3 files)"""
    set_resolution_low()
    global audio_only
    audio_only = True

@options.option('p', 'playlist')
def set_playlist(link):
    """HELP: Download a whole playlist"""
    link = link.replace('\"', '').replace("https://", '')
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
        links.extend(list(p.video_urls))
    except Exception as e:
        sys.exit(f"Unable to set playlist: {e}")
    
@options.option('l', 'low')
def set_resolution_low():
    """HELP: Get lowest video resolution"""
    global resolution
    resolution = 'low'

@options.option('r', 'res')
def set_resolution(resolution):
    """HELP: Set own resolution"""
    global vid_resolution
    vid_resolution = resolution

@options.option('t', 'target')
def set_target(path):
    """HELP: Set the target"""
    global vid_target
    vid_target = path.replace('\"', '')

@options.option('s', 'source')
def set_source(link):
    """HELP: Set the source link"""
    link = link.replace('\"', '').replace("https://", '')
    links.append(link)

@options.option('f', 'file')
def set_fromfile(path):
    """HELP: Set file source for links"""
    with open(path, 'r') as f:
        while l := f.readline():
            links.append(l)

def main():

    for i, url in enumerate(links):
        try:
            yt = pytube.YouTube(url, on_progress_callback=on_progress)
            ys = yt.streams
        except:
            sys.exit("Unable to set YouTUbe stream")
        
        print(f"{i+1}. {yt.title}".ljust(71, ' '))
        
        if vid_resolution == 'high':
            stream = ys.get_highest_resolution()
        elif vid_resolution == 'low':
            stream = ys.get_lowest_resolution()
        else:
            try:
                stream = ys.get_by_resolution(int(vid_resolution))
            except:
                sys.exit("Resolution: " + vid_resolution + " does not exist.")            

        if audio_only:
            stream = ys.get_audio_only()

        try:
            outfile = stream.download(vid_target)
            head, tail = os.path.split(outfile)
            base, ext = os.path.splitext(tail)
            newfile = os.path.join(head, rename_file(base) + ('.mp3' if audio_only else ext))
            os.rename(outfile, newfile)
        except:
            sys.exit("Unable to save the file")

if __name__ == "__main__":
    options.exec()
    main()
