#!/usr/bin/python3

import logging
logging.basicConfig(filename='watch_proc.log', encoding='utf-8', level=logging.INFO)
import time
import datetime
import pytz
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
OUTPATH = "/home/michael/shared/out"
PROCPATH = "/home/michael/shared/proc"

def timestamp():
    newstamp = str(datetime.datetime.now(pytz.timezone('America/Chicago'))) + ": "
    return(newstamp)
    
def move(infile,outpath=OUTPATH):
    success = True
    cmdstr = "mv \"" + infile + "\" " + outpath
    try:
        subprocess.check_output(cmdstr, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(timestamp() + e.output); success = False
    return(success)
    
class Watcher:
    DIRECTORY_TO_WATCH = PROCPATH
    def __init__(self):
        self.observer = Observer()
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            logging.info(timestamp()+"Observer Stopped")
        self.observer.join()
        
class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            logging.info("Received \"created\" event - {event.src_path}.")
            if event.src_path.endswith('.m4a'):
                output_folder = OUTPATH
                output_filename = os.path.splitext(os.path.basename(event.src_path))[0] + "-mono.mp3"
                output_file = os.path.join(output_folder, output_filename)
                logging.info(timestamp()+"began processing: "+output_filename)
                subprocess.call([
                    'ffmpeg',  '-nostdin', '-hide_banner', '-i', event.src_path,
                    '-filter_complex',
                    "[0:0]pan=mono|c0=c0[left0]; [0:0]pan=mono|c0=c1[right0]; [0:1]pan=mono|c0=c0[left1]; [0:1]pan=mono|c0=c1[right1]; [0:2]pan=mono|c0=c0[left2]; [0:2]pan=mono|c0=c1[right2]; [0:3]pan=mono|c0=c0[left3]; [0:3]pan=mono|c0=c1[right3]; [left0][right0][left1][right1][left2][right2][left3][right3]amix=inputs=8:duration=longest:normalize=0",
                    '-ac', '1', output_file
                ])
                logging.info(timestamp()+"finished processing: "+output_filename)
                if move(event.src_path) == True:
                    logging.info(timestamp()+event.src_path + " moved to " + OUTPATH)

if __name__ == '__main__':
    w = Watcher()
    w.run()