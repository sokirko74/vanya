import os
from yandex_music import Client
import vlc
from subprocess import Popen


class TYandexMusic:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "yandex_music_access_token.txt")) as inp:
            token = inp.read().strip()
        self.client = Client(token)
        self.client.init()
        self.track_folder = os.path.join(os.path.dirname(__file__), "yandex_music_tracks")
        if not os.path.exists(self.track_folder):
            os.mkdir(self.track_folder)
        self.totem_player = None
        #self.totem_player = Popen(['/usr/bin/totem'])  # something long running

    def play_track(self, artist_id:int, track_id: int):
        file_path  =   os.path.join(self.track_folder, "{}_{}.mp3".format(artist_id, track_id))
        if not os.path.exists(file_path):
            try:
                self.client.artists_tracks(artist_id).tracks[track_id - 1].download(file_path)
            except IndexError as exp:
                # track not found
                return None
        if not os.path.exists(file_path):
            return None
        #p = vlc.MediaPlayer("file://{}".format(file_path))
        #p.play()
        #p = Popen(['/usr/bin/totem', file_path])  # something long running
        # ... do other stuff while subprocess is running
        #pid = os.system('/usr/bin/totem {}'.format(file_path))
        if self.totem_player is not None:
            self.stop_player()
        #self.totem_player = Popen(['/usr/bin/totem', '--play', file_path])
        self.totem_player = Popen(['/usr/bin/vlc', '--play-and-exit', file_path])
        return self.totem_player

    def is_playing(self):
        if self.totem_player is None:
            return False
        if self.totem_player.poll() is None:
            return True
        return False

    def stop_player(self):
        #Popen(['/usr/bin/totem', '--quit'])
        if self.is_playing():
            self.totem_player.terminate()
        self.totem_player = None