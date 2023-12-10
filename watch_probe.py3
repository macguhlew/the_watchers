#!/usr/bin/python3

import logging
logging.basicConfig(filename='watch_probe.log', encoding='utf-8', level=logging.INFO)
import time
import datetime
import pytz
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
INPATH = "/home/michael/shared/in"
OUTPATH = "/home/michael/shared/out"
PROCPATH = "/home/michael/shared/proc"

def timestamp():
    newstamp = str(datetime.datetime.now(pytz.timezone('America/Chicago'))) + ": "
    return(newstamp)

def ffprobe(infile):
    cmdstr = "ffprobe \"" + infile + "\" 2>&1 | grep -E \"JAVS|Stream\s\#\""
    try:
        output = subprocess.check_output(cmdstr, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(timestamp() + e.output)
    return(output)
    
def move(infile,outpath=OUTPATH):
    success = True
    cmdstr = "mv \"" + infile + "\" " + outpath
    try:
        subprocess.check_output(cmdstr, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(timestamp() + e.output); success = False
    return(success)
    
class Watcher:
    DIRECTORY_TO_WATCH = INPATH
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
            outpath = OUTPATH #default is to move the file to the OUTPATH
            # Take any action here when a file is first created.
            logging.info("Received \"created\" event - {event.src_path}.")
            if event.src_path.endswith('.m4a'):
                fpresults = ffprobe(event.src_path)
                if fpresults.find('JAVS') > -1:
                    info = "stream_info: " #build the stream info line
                    i = fpresults.find('Stream #')
                    while i > -1:
                        info += fpresults[i+8:i+11] + " "
                        i = fpresults.find('Hz, ',i)
                        info += fpresults[i+4:i+8] + "|"
                        i = fpresults.find('Stream #',i)
                    if info.find("0:0 ster|0:1 ster|0:2 ster|0:3 ster") > -1:
                        outpath = PROCPATH #no else needed; default is OUTPATH

            if move(event.src_path,outpath) == True:
                logging.info(timestamp()+event.src_path + " moved to " + outpath)

if __name__ == '__main__':
    w = Watcher()
    w.run()