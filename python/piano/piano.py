import tkinter as tk
import os
from pathlib import Path
import time
import argparse
from pygame import mixer
import logging
import sys

sys.path.append('..')
from common.movements import detect_movements
from common.bluetooth_koleso import  TBluetoohKolesoThread

TK_APPLICATION = None
full_path = os.path.realpath(__file__)
FILEPATH, _ = os.path.split(full_path)
SLIDE_SWITCH = os.path.join(FILEPATH, "sound/slide_switch.wav")
BLUETOOTH_KOLESO = None
ZYNADDSUBFX_BINARY = "zynaddsubfx"

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler("piano.log",  mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    root.addHandler(ch)


def current_iso8601():
    """Get current date and time in ISO8601"""
    # https://en.wikipedia.org/wiki/ISO_8601
    # https://xkcd.com/1179/
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

def motion_handler_wrapper(event):
    global TK_APPLICATION
    TK_APPLICATION.motion_handler(event)

def play_file(filename):
    mixer.init()
    mixer.music.load(filename)
    mixer.music.play()

class Text2(tk.Frame):
    def __init__(self, master, width=0, height=0, **kwargs):
        self.width = width
        self.height = height

        tk.Frame.__init__(self, master, width=self.width, height=self.height)
        self.text_widget = tk.Text(self, **kwargs)
        self.text_widget.pack(expand=tk.YES, fill=tk.BOTH)

    def pack(self, *args, **kwargs):
        tk.Frame.pack(self, *args, **kwargs)
        self.pack_propagate(False)

    def grid(self, *args, **kwargs):
        tk.Frame.grid(self, *args, **kwargs)
        self.grid_propagate(False)


class Application(tk.Frame):
    def __init__(self, args, master=None):
        self.args = args
        self.Master = master
        self.Master.bind('<Shift-n>', self.next_instrument)
        self.Master.bind('<Shift-N>', self.next_instrument)
        self.Master.bind("<Return>", self.on_enter_key)

        master.geometry("900x600")
        root.geometry("+400+600")

        self.Instruments = [f for f in Path(args.instruments_folder).rglob('*.xiz')]
        print("use {} instruments\n".format(len(self.Instruments)))
        if len(self.Instruments) == 0:
            print("no instruments found, exit")
            exit(1)

        self.InstrumentIndex = 0
        #self.CoordWidget = None
        self.InstrumentWidget = None
        self.InstrumentIndexWidget = None
        self.Points = list()
        self.createWidgets()
        self.run_zynadd()
        self.bind_moise_move()

    def print_log(self, widget, s):
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, s)

    def createWidgets(self):
        self.now = tk.StringVar()
        tk.Frame.__init__(self, self.Master)
        self.pack()
        self.time = tk.Label(self, font=('Helvetica', 24))
        self.time.pack(side="top")
        self.time["textvariable"] = self.now

        tk.Button(master=self, text='Exit', command=myquit).pack(side=tk.TOP)

        self.InstrumentWidget = tk.Text(self, width=80, height=1, font=("Helvetica", 20))
        self.InstrumentWidget.pack(side=tk.TOP)

        self.CoordWidget = tk.Text(self, width=900, height=4)
        self.CoordWidget.pack(side=tk.TOP)

        self.InstrumentIndexWidget = tk.Text(self, width=3, height=1, font=("Helvetica", 48))
        self.InstrumentIndexWidget.pack(side=tk.TOP)

        self.CanvasFrame = tk.Frame(self)
        self.CanvasFrame.pack(fill=tk.BOTH, expand=1)
        self.Canvas = tk.Canvas(self.CanvasFrame, bg="blue")
        self.Canvas.pack(fill=tk.BOTH, expand=1)

        # initial time display
        self.onUpdate()

    def clear_canvas(self):
        self.Points = list()
        self.Canvas.delete("all")

    def draw_points (self):
        self.Canvas.delete("all")
        for i in range (1, len(self.Points)):
            self.Canvas.create_line(self.Points[i-1][1], self.Points[i-1][2], self.Points[i][1], self.Points[i][2])

    def bind_moise_move(self):
        self.Master.bind('<Motion>', motion_handler_wrapper)

    def unbind_moise_move(self):
        self.Master.unbind('<Motion>')

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
        if self.InstrumentIndex < 0:
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

    def next_instrument(self, event):
        self.switch_instrument("up")

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

    def onUpdate(self):
        # update displayed time
        self.now.set(current_iso8601())
        curtime = time.time()
        if self.focus_get() != None and len(self.Points) > 0:
            last_move_time = self.Points[-1][0]
            if curtime - last_move_time > 0.5:
                self.try_to_detect_movement()
                self.unbind_moise_move()
                self.event_generate('<Motion>', warp=True, x=400, y=400)
                self.clear_canvas()
                self.bind_moise_move()

        # schedule timer to call myself after 1 second
        self.after(200, self.onUpdate)


    def run_zynadd(self):
        instrument = self.Instruments[self.InstrumentIndex]
        self.print_log(self.InstrumentWidget, "{}".format(instrument))
        self.print_log(self.InstrumentIndexWidget, "{}".format(self.InstrumentIndex))

        os.system ("nohup pkill {0} >>binary_spawn_log.txt 2>&1 ".format(ZYNADDSUBFX_BINARY))
        play_file(SLIDE_SWITCH)

        cmd = "{} --auto-connect --output {} --load-instrument='{}' ".format(ZYNADDSUBFX_BINARY, self.args.sound_server, instrument)
        if not self.args.use_gui:
            cmd += " --no-gui "
        cmd += "  >>binary_spawn_log.txt 2>&1 &"
        os.system(cmd)

        logging.debug('use instrument {}'.format(instrument))


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
        self.print_log(self.CoordWidget, '{}'.format(str([(x,y) for (_, x, y) in self.Points])))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-gui", dest='use_gui', default=False, action="store_true")
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--sound-server", dest='sound_server', default="jack", help="jack or alsa (default)")
    parser.add_argument("--instruments", dest='instruments_folder',
                        default="/usr/share/zynaddsubfx/banks/Collection", help="instrument folder")
    return parser.parse_args()

def bluetooth_koleso_action(is_forward):
    global TK_APPLICATION
    TK_APPLICATION.switch_instrument("up" if is_forward else "down")

def myquit():
    global BLUETOOTH_KOLESO
    if BLUETOOTH_KOLESO is not None:
        BLUETOOTH_KOLESO.killed = True
    os.system("pkill ffplay")
    os.system("pkill {0}".format(ZYNADDSUBFX_BINARY))
    tk.Tk().destroy()
    sys.exit(0)

if __name__ == '__main__':
    args = parse_args()
    root = tk.Tk()
    root.wm_protocol("WM_DELETE_WINDOW", myquit)
    setup_logging()
    try:
        BLUETOOTH_KOLESO = TBluetoohKolesoThread(bluetooth_koleso_action)
    except Exception as e:
        logging.info("cannot find bluetooth koleso, ignore it: {}, try to run 'sudo /etc/init.d/bluetooth restart' ".format(e))

    play_file("sound/slide_switch.wav")
    if args.fullscreen:
        root.attributes('-fullscreen', True)
    TK_APPLICATION = Application(args, master=root)
    if BLUETOOTH_KOLESO is not None:
        BLUETOOTH_KOLESO.start()

    root.mainloop()

