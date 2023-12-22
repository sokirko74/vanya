import json
import os
import time

from yandex_music import Client
import vlc
from subprocess import Popen

YANDEX_MUSIC_ARTISTS = {
 "шейквелл": 4331744,
 "шейквел": 4331744,
 "снупдог": 6165,
 "цой": 953565
}


class TYandexMusic:
    def __init__(self, parent, prefer_rap):
        self.parent = parent
        self.logger = parent.logger
        self.prefer_rap = prefer_rap
        with open(os.path.join(os.path.dirname(__file__), "yandex_music_access_token.txt")) as inp:
            token = inp.read().strip()
        self.client = Client(token)
        self.client.init()
        self.track_folder = os.path.join(os.path.dirname(__file__), "yandex_music_tracks")
        if not os.path.exists(self.track_folder):
            os.mkdir(self.track_folder)
        self.totem_player = None
        #self.totem_player = Popen(['/usr/bin/totem'])  # something long running
        self.artist_info_path = os.path.join(os.path.join(os.path.dirname(__file__)), 'yandex_music_artist.json')
        self.artist_info = dict()
        self.read_artist_info()
        self.start_time_stamp = None

    def read_artist_info(self):
        if os.path.exists(self.artist_info_path):
            with open(self.artist_info_path) as inp:
                self.artist_info =  json.load(inp)
    def write_artist_info(self):
        with open(self.artist_info_path, "w") as outp:
            json.dump(self.artist_info, outp)

    def _get_artist_id(self, query):
        saved = self.artist_info.get(query)
        if saved is not None:
            return saved
        search_result = self.client.search(query)
        if search_result.artists:
            for res in search_result.artists.results:
                if not self.prefer_rap or ('rusrap' in res.genres) or ('foreignrap' in res.genres) or ('rap' in res.genres):
                    artist_id = res.id
                    r = {
                        'id': artist_id,
                        'name': res.name,
                    }
                    if res.cover is not None:
                        r['cover_uri'] = res.cover.uri
                    self.artist_info[query] = r
                    self.write_artist_info()
                    self.logger.info('new artist id={} name={}'.format(artist_id, res.name))
                    return r

    def _prepare_play(self, artist_str: str, track_id: int):
        if self.totem_player is not None:
            self.stop_player()

        artist_info = self._get_artist_id(artist_str)
        if artist_info is None:
            return None
        artist_id = artist_info['id']
        self.logger.info('play id={} name={} track_id={}'.format(artist_id,
                                                                 artist_info['name'],
                                                                 track_id))

        file_path = os.path.join(self.track_folder, "{}_{}.mp3".format(artist_id, track_id))
        if not os.path.exists(file_path):
            try:
                self.logger.info('download track ...')
                self.client.artists_tracks(artist_id).tracks[track_id - 1].download(file_path)
                self.logger.info('success')
            except IndexError as exp:
                # track not found
                return None
        if not os.path.exists(file_path):
            return None
        # p = vlc.MediaPlayer("file://{}".format(file_path))
        # p.play()
        # p = Popen(['/usr/bin/totem', file_path])  # something long running
        # ... do other stuff while subprocess is running
        # pid = os.system('/usr/bin/totem {}'.format(file_path))
        # self.totem_player = Popen(['/usr/bin/totem', '--play', file_path])
        time.sleep(2)
        return file_path

    def play_track(self, artist_str: str, track_id: int):
        self.start_time_stamp = None
        file_path = self._prepare_play(artist_str, track_id)
        if file_path is not None:
            self.totem_player = Popen(['/usr/bin/vlc', '--play-and-exit', file_path])
            self.start_time_stamp = time.time()
            time.sleep(0.5)
            #self.parent
            return self.totem_player
        else:
            return None

    def is_playing(self):
        if self.totem_player is None:
            return False
        obligatory_seconds = 5
        if self.start_time_stamp is not None and time.time() < self.start_time_stamp + obligatory_seconds:
            self.logger.info("hear at least {} seconds before stop".format(obligatory_seconds))
            return False
        if self.totem_player.poll() is None:
            return True
        return False

    def stop_player(self):
        #Popen(['/usr/bin/totem', '--quit'])
        if self.is_playing():
            self.totem_player.terminate()
        self.totem_player = None