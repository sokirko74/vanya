
import tkinter as tk
import os
from pathlib import Path
import time
import argparse
from pygame import mixer
import logging


ZYNADDSUBFX_BINARY = "zynaddsubfx"


def setup_logging():
    logger = logging.getLogger("piano_logger")
    logger.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler("piano.log",  mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger


def current_iso8601():
    """Get current date and time in ISO8601"""
    # https://en.wikipedia.org/wiki/ISO_8601
    # https://xkcd.com/1179/
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def play_file(filename):
    mixer.init()
    mixer.music.load(filename)
    mixer.music.play()


class TApplication(tk.Frame):
    def load_collection(self):
        collection = self.all_collections[self.collection_id]
        folder = os.path.join(self.args.collection_folder, collection)
        self.Instruments = [f for f in Path(folder).rglob('*.xiz')]
        print("use {} instruments\n".format(len(self.Instruments)))

    def __init__(self, args, logger, master):
        self.args = args
        self.master = master
        self.logger = logger
        self.collection_switcher_thread = None
        self.master.bind('<Shift-n>', self.next_instrument)
        self.master.bind('<Shift-N>', self.next_instrument)
        self.master.bind("<Return>", self.on_enter_key)

        self.master.geometry("900x600")
        self.master.geometry("+400+600")

        self.Instruments = None
        self.all_collections = os.listdir(args.collection_folder)
        self.collection_id = self.all_collections.index(args.collection)
        self.load_collection()

        self.InstrumentIndex = 0
        self.CollectionWidget = None
        self.InstrumentWidget = None
        self.InstrumentIndexWidget = None
        self.Points = list()
        self.create_widgets()
        self.run_zynadd()
        self.bind_moise_move()
        self.master.wm_protocol("WM_DELETE_WINDOW", self.quit)
        #self.init_collection_switcher()

    def init_collection_switcher(self):
        self.collection_switcher_thread = None
        try:
            self.collection_switcher_thread = TBluetoohKolesoThread(self.logger, self.switch_instrument)
            self.collection_switcher_thread.connect_bluetooth()
        except Exception as e:
            self.logger.info(
                "cannot find bluetooth koleso, ignore it: {}, try to run 'sudo /etc/init.d/bluetooth restart' ".format(
                    e))
            del self.collection_switcher_thread
            self.collection_switcher_thread = None

    def start_collection_switcher(self):
        if self.collection_switcher_thread is not None:
            self.logger.info("start bluetooth thread")
            self.collection_switcher_thread.start()

    def stop_collection_switcher(self):
        if self.collection_switcher_thread is not None:
            self.logger.info("stop bluetooth thread")
            self.collection_switcher_thread.stop_thread()
            del self.collection_switcher_thread
            self.collection_switcher_thread = None

    def print_to_widget(self, widget, s):
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, s)

    def create_widgets(self):
        self.now = tk.StringVar()
        tk.Frame.__init__(self, self.master)
        self.pack()
        self.time = tk.Label(self, font=('Helvetica', 24))
        self.time.pack(side="top")
        self.time["textvariable"] = self.now

        tk.Button(master=self, text='Exit', command=self.quit).pack(side=tk.TOP)
        self.CollectionWidget = tk.Text(self, width=80, height=1, font=("Helvetica", 20))
        self.CollectionWidget.pack(side=tk.TOP)
        self.InstrumentWidget = tk.Text(self, width=80, height=1, font=("Helvetica", 20))
        self.InstrumentWidget.pack(side=tk.TOP)

        if self.args.enable_mouse_instrument_switch:
            self.CoordWidget = tk.Text(self, width=900, height=4)
            self.CoordWidget.pack(side=tk.TOP)

        self.InstrumentIndexWidget = tk.Text(self, width=3, height=1, font=("Helvetica", 48))
        self.InstrumentIndexWidget.pack(side=tk.TOP)

        self.CanvasFrame = tk.Frame(self)
        self.CanvasFrame.pack(fill=tk.BOTH, expand=1)
        self.Canvas = tk.Canvas(self.CanvasFrame, bg="blue")
        self.Canvas.pack(fill=tk.BOTH, expand=1)
        tk.Button(master=self, text='Next', font=("Helvetica", 20), bg="green", width=30,
                  command=self.next_instrument).pack(side=tk.LEFT, padx=50)
        tk.Button(master=self, text='Prev', font=("Helvetica", 20), width=30,
                  command=self.prev_instrument, bg="red").pack(side=tk.LEFT, padx=50)

        # initial time display
        self.on_update()

    def clear_canvas(self):
        self.Points = list()
        self.Canvas.delete("all")

    def draw_points (self):
        self.Canvas.delete("all")
        for i in range (1, len(self.Points)):
            self.Canvas.create_line(self.Points[i-1][1], self.Points[i-1][2], self.Points[i][1], self.Points[i][2])

    def bind_moise_move(self):
        if self.args.enable_mouse_instrument_switch:
            self.master.bind('<Motion>', self.motion_handler)

    def unbind_moise_move(self):
        if self.args.enable_mouse_instrument_switch:
            self.master.unbind('<Motion>')

    def on_enter_key(self, event):
        newIndex = int(self.InstrumentIndexWidget.get("1.0", tk.END).strip())
        if newIndex != self.InstrumentIndex:
            self.InstrumentIndex = newIndex
        self.clear_canvas()
        self.run_zynadd()

    def increment_instrument_index(self, delta):
        self.InstrumentIndex += delta
        if self.InstrumentIndex >= len(self.Instruments):
            self.InstrumentIndex = 0
            if self.collection_id + 1 == len(self.all_collections):
                self.collection_id = 0
            else:
                self.collection_id += 1
            self.load_collection()
        if self.InstrumentIndex < 0:
            if self.collection_id  == 0:
                self.collection_id = len(self.all_collections) - 1
            else:
                self.collection_id -= 1
            self.load_collection()
            self.InstrumentIndex = len(self.Instruments) - 1

    def switch_instrument(self, movement):
        step = 0
        if movement == "up":
            step = 1
        elif movement == "down":
            step = -1

        if step != 0:
            logging.debug('movement: {}'.format(movement))
            self.increment_instrument_index(step)
            self.clear_canvas()
            self.run_zynadd()

    def next_instrument(self):
        self.switch_instrument("up")
    def prev_instrument(self):
        self.switch_instrument("down")

    def try_to_detect_movement(self):
        points = [(x,y) for (_, x, y) in self.Points]
        movements = detect_movements(points)
        if len(movements) != 1:
            #logging.debug('ignore multiple movements')
            pass
        else:
            movement = list(movements.items())[0][0]
            self.switch_instrument(movement)
        self.clear_canvas()

    def on_update(self):
        # update displayed time
        self.now.set(current_iso8601())
        curtime = time.time()
        if self.args.enable_mouse_instrument_switch:
            if self.focus_get() != None and len(self.Points) > 0:
                last_move_time = self.Points[-1][0]
                if curtime - last_move_time > 0.5:
                    self.try_to_detect_movement()
                    self.unbind_moise_move()
                    self.event_generate('<Motion>', warp=True, x=400, y=400)
                    self.clear_canvas()
                    self.bind_moise_move()

        # schedule timer to call myself after 1 second
        self.after(200, self.on_update)

    def run_zynadd(self):
        instrument = self.Instruments[self.InstrumentIndex]
        self.print_to_widget(self.CollectionWidget, "{}".format(self.all_collections[self.collection_id]))
        self.print_to_widget(self.InstrumentWidget, "{}".format(os.path.basename(str(instrument))))
        self.print_to_widget(self.InstrumentIndexWidget, "{}".format(self.InstrumentIndex))

        os.system ("nohup pkill {0} >>binary_spawn_log.txt 2>&1 ".format(ZYNADDSUBFX_BINARY))
        slide_switch = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sound", "slide_switch.wav")
        play_file(slide_switch)

        cmd = "{} --auto-connect --output {} --load-instrument='{}' ".format(ZYNADDSUBFX_BINARY, self.args.sound_server, instrument)
        if not self.args.use_gui:
            cmd += " --no-gui "
        cmd += "  >>binary_spawn_log.txt 2>&1 &"
        os.system(cmd)

        #logging.debug('use instrument {}'.format(instrument))

    def motion_handler(self, event):
        cur_x = event.x
        cur_y = event.y
        curtime = time.time()
        point = (curtime, cur_x, cur_y)
        if len(self.Points) > 0 and self.Points[-1] == point:
            return
        self.Points.append(point)
        self.Points = [(t, x, y) for (t, x, y) in self.Points if curtime - t <= 2.0]
        self.draw_points()
        if self.CoordWidget is not None:
            self.print_to_widget(self.CoordWidget, '{}'.format(str([(x, y) for (_, x, y) in self.Points])))

    def quit(self):
        self.stop_collection_switcher()
        os.system("pkill ffplay")
        os.system("pkill {0}".format(ZYNADDSUBFX_BINARY))
        self.logger.info("destroy tk root and exit mainloop")
        self.master.destroy()
        self.master.quit()




def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-gui", dest='use_gui', default=False, action="store_true")
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--sound-server", dest='sound_server', default="jack", help="jack or alsa (default)")
    parser.add_argument("--enable-mouse-instrument-switch", dest='enable_mouse_instrument_switch', default=False, required=False)
    parser.add_argument("--collection-folder", dest='collection_folder',
                        default="/usr/share/zynaddsubfx/banks")
    parser.add_argument("--collection", dest='collection',
                        default="Collection")
    return parser.parse_args()


def main(logger):
    args = parse_args()
    tk_root = tk.Tk()
    if args.fullscreen:
        tk_root.attributes('-fullscreen', True)
    tk_app = TApplication(args, logger, tk_root)

    tk_app.start_collection_switcher()
    play_file("sound/slide_switch.wav")

    try:
        tk_app.mainloop()
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
        tk_app.quit()


if __name__ == '__main__':
    logger = setup_logging()
    main(logger)
    logger.info("exit from main")

