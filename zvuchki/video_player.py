from zvuchki.browser_wrapper import TBrowser

import threading
import time



class VideoPlayer (threading.Thread):
    def __init__(self, parent, url, seconds):
        threading.Thread.__init__(self)
        self.parent = parent
        self.browser: TBrowser = parent.browser
        self.url = url
        self.seconds = seconds
        self._interrupted = False

    def stop_playing(self):
        self._interrupted = True
        time.sleep(1)

    def next_track(self):
        self.browser.send_shift_n()

    def prev_track(self):
        self.browser.send_shift_p()

    def run(self):
        for try_index in range(2):
            if not self.parent.is_running or self._interrupted:
                break
            if self.browser.play_youtube(self.url):
                self.parent.set_window_focus()
                print("sleep for  {} seconds (video duration)".format(self.seconds))
                for i in range(self.seconds):
                    if self._interrupted:
                        break
                    time.sleep(1)
                self.browser.close_all_windows()
                self.parent.on_video_finish()
                return
            if self._interrupted:
                return
