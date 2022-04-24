from utils.logging_wrapper import setup_logging

import tkinter as tk
import os
from pathlib import Path
import time
import argparse
from pygame import mixer
import re


ZYNADDSUBFX_BINARY = "zynaddsubfx"


def current_iso8601():
    """Get current date and time in ISO8601"""
    # https://en.wikipedia.org/wiki/ISO_8601
    # https://xkcd.com/1179/
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def play_file(filename):
    mixer.init()
    mixer.music.load(filename)
    mixer.music.set_volume(1)
    mixer.music.play()


class TInstrumentBank:
    def  __init__(self, folder):
        self.name = os.path.basename(folder)
        self.instruments = [f for f in Path(folder).rglob('*.xiz')]
        self.instrument_index = 0

    def increment_instrument_index(self, delta):
        self.instrument_index += delta
        if self.instrument_index >= len(self.instruments):
            self.instrument_index = 0
        if self.instrument_index < 0:
            self.instrument_index = len(self.instruments) - 1

    def get_instrument_name(self):
        instrument = self.instruments[self.instrument_index]
        b = os.path.basename(str(instrument))
        if b.endswith(".xiz"):
            b = b[:-4]
        return b

    def get_instrument_path(self):
        instrument = self.instruments[self.instrument_index]
        return str(instrument)


def load_banks(folder):
    instrument_banks = list()
    for x in os.listdir(folder):
        b = TInstrumentBank(os.path.join(folder, x))
        instrument_banks.append(b)
    return instrument_banks


class TApplication(tk.Frame):
    def __init__(self, args, logger, master):
        self.args = args
        self.zynaddsubfx_path = args.zynaddsubfx_path
        self.master = master
        self.logger = logger
        self.master.geometry("900x600")
        self.main_wnd_width = self.master.winfo_screenwidth()
        self.main_wnd_height = self.master.winfo_screenheight()
        self.run_zynaddsubfx()
        self.volume = self.get_volume()
        self.last_change_instrument_time = time.time()

        self.master.bind('<F1>', self.next_instrument)
        self.master.bind('<F12>', self.next_instrument)
        self.master.bind('<F2>', self.prev_instrument)
        self.master.bind('<F4>', self.next_bank)
        self.master.bind('<F5>', self.volume_up)
        self.master.bind('<F6>', self.volume_down)
        self.instrument_banks = load_banks(args.banks_folder)
        self.bank_index = 0
        self.instrument_index = 0
        self.CollectionWidget = None
        self.InstrumentWidget = None
        self.InstrumentIndexWidget = None
        self.VolumeWidget = None
        self.create_widgets()
        self.master.wm_protocol("WM_DELETE_WINDOW", self.quit)
        self.print_to_widget(self.VolumeWidget, self.volume)

    def set_volume(self):
        cmd = "amixer -D pulse sset Master {}%".format(self.volume)
        ret = self.run_cmd(cmd)
        if ret != 0:
            self.logger.error("{} failed".format(cmd))
        self.print_to_widget(self.VolumeWidget, self.volume)

    def get_volume(self):
        tmp_path = "volume.txt"
        cmd = "amixer -D pulse sget Master >{}".format(tmp_path)
        self.run_cmd(cmd)
        with open(tmp_path) as inp:
            for l in inp:
                match = re.search('Front Left: Playback [0-9]+ .([0-9]+)%.', l)
                if match is not None:
                    return int(match.group(1))
        return None

    def volume_up(self, event):
        self.volume +=  10
        if self.volume > 100:
            self.volume = 100
        self.set_volume()

    def volume_down(self, event):
        self.volume -= 10
        if self.volume < 0:
            self.volume = 0
        self.set_volume()

    def print_to_widget(self, widget, s):
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, s)

    def create_widgets(self):
        self.now = tk.StringVar()
        tk.Frame.__init__(self, self.master)
        self.pack()
        text = "F1-next instrument, F2-prev instrument, F4-next bank, F5-volume up, F6-volume down"
        self.time = tk.Label(self, text=text, font=('Helvetica', 12))
        self.time.pack(side=tk.TOP)

        tk.Button(master=self, text='Exit', command=self.quit).pack(side=tk.TOP)
        fontsize = 20
        if self.main_wnd_width > 900:
            fontsize = 60
        self.CollectionWidget = tk.Text(self, width=self.main_wnd_width-10, height=1, font=("Helvetica", fontsize))
        self.CollectionWidget.pack(side=tk.TOP)
        self.InstrumentWidget = tk.Text(self, width=self.main_wnd_width-10, height=1, font=("Helvetica", fontsize))
        self.InstrumentWidget.pack(side=tk.TOP)
        self.InstrumentIndexWidget = tk.Text(self, width=3, height=1, font=("Helvetica", 48))
        self.VolumeWidget = tk.Text(self, width=3, height=1, font=("Helvetica", 48))
        self.VolumeWidget.pack(side=tk.RIGHT)
        self.InstrumentIndexWidget.pack(side=tk.TOP)

        # initial time display
        self.slide_switch = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sound", "slide_switch.wav")
        self.on_change_instrument()

    def run_cmd(self, cmd):
        self.logger.info(cmd)
        os.system(cmd)

    def clear_canvas(self):
        self.Points = list()
        self.Canvas.delete("all")

    def get_bank(self) -> TInstrumentBank :
        return self.instrument_banks[self.bank_index]

    def check_time(self):
        self.logger.info("check time")
        if time.time() - self.last_change_instrument_time < 1:
            self.logger.info("skip change instrument (timeout)")
            return False
        self.last_change_instrument_time = time.time()
        return True

    def next_instrument(self, event):
        if self.check_time():
            self.get_bank().increment_instrument_index(+1)
            self.on_change_instrument()

    def prev_instrument(self, event):
        if self.check_time():
            self.get_bank().increment_instrument_index(-1)
            self.on_change_instrument()

    def next_bank(self, event):
        self.logger.info("next_bank")
        if self.check_time():
            if self.bank_index  + 1 == len(self.instrument_banks):
                self.bank_index = 0
            else:
                self.bank_index  += 1
            self.on_change_instrument()

    def on_update(self):
        self.now.set(current_iso8601())
        curtime = time.time()
        self.after(200, self.on_update)

    def on_change_instrument(self):
        self.print_to_widget(self.CollectionWidget, self.get_bank().name)
        self.print_to_widget(self.InstrumentWidget, self.get_bank().get_instrument_name())
        self.print_to_widget(self.InstrumentIndexWidget, "{}".format(self.get_bank().instrument_index))
        self.send_command_to_zynaddsubfx("load_instrument {}".format(self.get_bank().get_instrument_path()))
        self.on_update()
        time.sleep(1)
        play_file(self.slide_switch)

    def get_command_path(self):
        return "vanya_commands.txt"

    def send_command_to_zynaddsubfx(self, cmd):
        self.logger.info("send_command_to_zynaddsubfx: {}".format(cmd))
        with open(self.get_command_path(), "w") as outp:
            outp.write(cmd)
        time.sleep(1)
        if os.path.exists(self.get_command_path()):
            self.logger.error("zynaddsubfx is down? command {} failed".format(cmd))
            return False
        return True

    def connect_keyboard(self):
        tmp_path = 'alsa_connections.txt'
        self.run_cmd('aconnect -l > {}'.format(tmp_path))
        zyn_id = None
        keyboard_id = None
        keyboard_name = 'microKEY-25'
        with open(tmp_path) as inp:
            for l in  inp:
                match = re.search("client ([0-9]+): '([^']+)'", l)
                if match is not None:
                    port_id = match.group(1)
                    name =  match.group(2)
                    if name.find('ZynAddSubFX') != -1:
                        zyn_id = port_id
                    elif name.find(keyboard_name) != -1:
                        keyboard_id = port_id
        if keyboard_id is None:
            raise Exception("cannot find keyboard {} in alsa connections".format(keyboard_name))
        if zyn_id is None:
            raise Exception("cannot find ZynAddSubFX in alsa connections".format(keyboard_name))
        self.run_cmd('aconnect {} {}'.format(keyboard_id, zyn_id))

    def run_zynaddsubfx(self):
        self.kill_zynaddsubfx()

        binary_path = self.args.zynaddsubfx_path
        if not os.path.exists(binary_path):
            raise Exception("could not find {}".format(binary_path))
        assert binary_path.endswith(ZYNADDSUBFX_BINARY)

        cmd = "{} {} >>binary_spawn_log.txt 2>&1 &".format(binary_path, self.args.zynaddsubfx_args)
        self.run_cmd(cmd)
        self.logger.info("sleep for {} seconds".format(self.args.zynaddsubfx_starting_timeout))
        time.sleep(self.args.zynaddsubfx_starting_timeout)
        assert self.send_command_to_zynaddsubfx("dummy")
        if self.args.connect_keyboard:
            self.connect_keyboard()

    def kill_zynaddsubfx(self):
        self.run_cmd("pkill ffplay")
        self.run_cmd("pkill {0}".format(ZYNADDSUBFX_BINARY))

    def quit(self):
        self.kill_zynaddsubfx()
        self.logger.info("destroy tk root and exit mainloop")
        self.master.destroy()
        self.master.quit()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--bank-folder", dest='banks_folder',
                        default="/usr/share/zynaddsubfx/banks")
    parser.add_argument("--zynaddsubfx-path", dest='zynaddsubfx_path')
    parser.add_argument("--zynaddsubfx-args", dest='zynaddsubfx_args', default="-a -U")
    parser.add_argument("--zynaddsubfx-starting-timeout", dest='zynaddsubfx_starting_timeout', default=2, type=int)
    parser.add_argument("--skip-keyboard-connect", dest='connect_keyboard',  action="store_false", default=True)
    return parser.parse_args()


def main():
    args = parse_args()
    tk_root = tk.Tk()
    if args.fullscreen:
        tk_root.attributes('-fullscreen', True)
    logger = setup_logging("piano2")
    tk_app = TApplication(args, logger, tk_root)

    play_file("sound/slide_switch.wav")

    try:
        tk_app.mainloop()
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
        tk_app.quit()


if __name__ == '__main__':
    main()