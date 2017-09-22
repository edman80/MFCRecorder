import threading
import datetime
import os

class RecordingThread(threading.Thread):
    URL_TEMPLATE = "hlsvariant://http://video{srv}.myfreecams.com:1935/NxServer/ngrp:mfc_{id}.f4v_mobile/playlist.m3u8"
    READING_BLOCK_SIZE = 1024
    currently_recording_models = {}
    total_data = 0
    file_count = 0
    _lock = threading.Lock()

    def __init__(self, session, settings):
        super().__init__()
        self.file_size = 0
        self.session = session
        self.settings = settings
    
    def run(self):
        #TODO: not sure where we will check if the model is already being recorded
        stream = self.stream
        if not stream: return
        
        start_time = datetime.datetime.now()
        file_path = self.create_path(self.settings.directory_structure, start_time)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with self._lock:
            self.file_count += 1
        
        with stream.open() as source, open(file_path, 'wb') as target:
            while True: #TODO: add recording conditions
                try:
                    target.write(source.read(self.READING_BLOCK_SIZE))
                except:
                    break
                with self._lock:
                    self.total_data += self.READING_BLOCK_SIZE
                self.file_size += self.READING_BLOCK_SIZE
        
        if self.file_size == 0:
            with self._lock:
                self.file_count -= 1
            os.remove(file_path)
            return
        
        #TODO: postprocessing...
        
        if self.settings.completed_directory:
            dir = self.create_path(self.settings.completed_directory, start_time)
            os.makedirs(dir, exist_ok=True)
            os.rename(file_path, os.path.join(dir, os.path.basename(file_path)))
        
        self.currently_recording_models.pop(self.session['uid'], None)
        print(Fore.RED + "{}'s session has ended".format(self.session['nm']) + Fore.RESET)
    
    @property
    def stream(self):
        streams = {} #not sure this is needed for the finally to work
        try:
            streams = Livestreamer().streams(self.URL_TEMPLATE.format(id=int(self.session['uid']) + 100_000_000, srv=int(self.session['camserv']) - 500))
        finally:
            return streams.get('best')
    
    def create_path(self, template, time):
        return template.format(
            path=self.settings.save_directory, model=self.session['nm'], uid=self.session['uid'],
            seconds=now.strftime("%S"), day=now.strftime("%d"),
            minutes=now.strftime("%M"), hour=now.strftime("%H"),
            month=now.strftime("%m"), year=now.strftime("%Y"), auto=self.session['condition'])
