from config import TConfig
import unidecode
import time


class TReqProcessor:
    def __init__(self, logger, config, request, transliterate, duration):
        self.logger = logger
        self.transliterate = transliterate
        self.config: TConfig = config
        self._request = request
        self.query = ""
        self.use_old_urls = False
        self.clip_index = None
        self.add_sec = None
        self.use_yandex_music = False
        self.use_cache = True
        self.request_command = None
        self.channel_id = None
        self.url = None
        self.duration = duration
        self.endtime = None

    def process_req(self):
        words = self._request.strip().split(' ')
        query_words = list()
        self.clip_index = None
        add_to_query = list()
        self.add_sec = 0
        self.use_old_urls = False
        self.use_yandex_music = False
        test_drive = "тест драйв от первого лица"
        test_drive_en  = "test drive"
        self.use_cache = True
        self.request_command = None
        self.channel_id = None

        for token_index, token in enumerate(words):
            if token.isdigit() and self.clip_index is None and int(token) < 200 and token_index > 0:
                self.clip_index = int(token)
                continue
            token = token.upper()
            req_alias = self.config.get_req_alias(token)
            if token == 'Д':
                self.add_sec = 120
            elif token == "ПАМ":
                self.request_command = "ПАМ"
            elif token == "СОКР":
                self.request_command = "СОКР"
            elif token == 'ДД':
                self.add_sec = 240
            elif token == 'Т':
                if self.transliterate:
                    add_to_query.append(test_drive_en)
                else:
                    add_to_query.append(test_drive)
            elif token == 'T':
                self.logger.info('add en test drive')
                add_to_query.append(test_drive_en)
            elif token == 'R':
                add_to_query.append('retro')
            elif token == 'ТД':
                add_to_query.append( test_drive)
                self.add_sec = 120
            elif token == 'ТДД':
                add_to_query.append( test_drive)
                self.add_sec = 240
            elif token == 'К':
                add_to_query.append("в кабине водителя")
            elif token == 'АВТОС':
                query_words.append( "АВТОСИГНАЛИЗАЦИЯ")
            elif token == 'ЗД':
                add_to_query.append( "звук двигателя")
            elif token == 'З':
                add_to_query.append("звук")
            elif token == 'S':
                add_to_query.append("engine start")
            elif req_alias:
                add_to_query.append(req_alias)
            elif token == 'R':
                add_to_query.append("rapper")
            elif token == 'СТ':
                add_to_query.append("СТАРТИНГ")
            elif token == 'М':
                add_to_query.append("МАШИНА")
            elif token == 'Э':
                add_to_query.append( "эксплуатация")
            elif token == 'Р':
                add_to_query.append("реставрация")
            elif token == 'НОВ':
                self.use_cache = False
            elif token == 'П':
                self.use_old_urls = True
            elif token.lower() == 'я':
                self.use_yandex_music = True
            elif token.lower() == 'y':
                self.use_yandex_music = True
            else:
                channel_id =  self.config.translate_alias(token)
                if channel_id  is not None:
                    token = channel_id
                    self.channel_id = channel_id

                if len(token) > 0:
                    query_words.append(token)
        if self.clip_index is None and self.request_command is None:
            self.logger.error("specify video clip index (integer after query)")
            return False

        if len(query_words) == 0 and not add_to_query:
            self.logger.error("no query")
            return False

        self.query = " ".join(query_words)
        if add_to_query:
            self.query += " " + " ".join(add_to_query)

        return True


    def determine_url_and_duration(self, args, browser):
        if self.use_old_urls:
            key = f"{self.query}{self.clip_index}".lower()
            url_data = self.config.saved_urls.get(key)
            if url_data:
                self.url, timeout = url_data
                if args.max_play_seconds < timeout:
                    timeout = args.max_play_seconds
                self.duration = timeout + self.add_sec
            else:
                browser.logger.error("no stored key {}".format(key))
                self.url = "about:blank"
                self.duration = 0
        else:
            # Поиск через Selenium (Google или YouTube)
            query = unidecode.unidecode(self.query) if args.transliterate else self.query
            self.url = browser.get_url_video_from_google_or_cached(
                query,
                self.clip_index,
                self.use_cache,
                self.channel_id is not None
            )
            self.duration = args.max_play_seconds + self.add_sec

    def determine_end_time(self, last_clip_length):
        if last_clip_length:
            real_duration = last_clip_length + self.add_sec
            self.duration = min(self.duration, real_duration)
        self.endtime = time.time() + self.duration

