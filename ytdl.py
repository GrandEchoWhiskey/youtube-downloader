import pytube
from pytube.cli import on_progress
import sys
import os
import options

options.SHORT_JUST = 15
options.LONG_JUST = 20
options.HELP_NOTE = 'Usage: python3 ytdl.py [OPTIONS]'

yt_options = {
    'audio_only': False,
    'resolution': 'high',
    'target': '.',
    'playlist': False,
    'source': ''
}

links = []

def set_audio_only():
    """
    HELP: Download only in mp3 format
    """
    yt_options['audio_only'] = True

def set_playlist(link: 'link'):
    """
    HELP: Download a whole playlist
    """
    yt_options['playlist'] = True
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
    

def set_resolution_low():
    """
    HELP: Get lowest video resolution
    """
    yt_options['resolution'] = 'low'

def set_resolution(resolution: 'resolution'):
    """
    HELP: Set own resolution
    """
    yt_options['resolution'] = resolution

def set_target(tar: 'target'):
    """
    HELP: Set the target
    """
    yt_options['target'] = tar.replace('\"', '')

def set_source(src: 'link'):
    """
    HELP: Set the source link
    """
    src = src.replace('\"', '').replace("https://", '')
    yt_options['source'] = src
    links.append(src)

options.add('t', 'target', set_target)
options.add('s', 'source', set_source)
options.add('a', 'audio', set_audio_only)
options.add('p', 'playlist', set_playlist)
options.add('l', 'low', set_resolution_low)
options.add('r', 'res', set_resolution)

def main():

    try:
        options.exec() 
        if len(sys.argv) < 3:
            raise Exception
    except:
        sys.exit('Use: "python3 ytdl.py -h" for help.')

    for i, url in enumerate(links):
        try:
            yt = pytube.YouTube(url, on_progress_callback=on_progress)
            ys = yt.streams
        except:
            sys.exit("Unable to set YouTUbe stream")
        
        print(f"{i+1}. {yt.title}".ljust(71, ' '))
        
        if yt_options['resolution'] == 'high':
            stream = ys.get_highest_resolution()
        elif yt_options['resolution'] == 'low':
            stream = ys.get_lowest_resolution()
        else:
            try:
                stream = ys.get_by_resolution(int(yt_options['resolution']))
            except:
                sys.exit("Resolution: " + yt_options['resolution'] + " does not exist.")            

        if yt_options['audio_only']:
            stream = ys.get_audio_only()

        try:
            outfile = stream.download(yt_options['target'])
            if yt_options['audio_only']:
                base, ext = os.path.splitext(outfile)
                newfile = base + '.mp3'
                os.rename(outfile, newfile)
        except:
            sys.exit("Unable to save the file")

if __name__ == "__main__":
    main()