import sys
import os
import psutil
import signal
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

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
        if x != 'Drums':
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

        self.master.bind('<F10>', self.next_bank)
        self.master.bind('<F8>', self.prev_bank)
        self.master.bind('<F6>', self.next_instrument)
        self.master.bind('<F4>', self.prev_instrument)
        #self.master.bind('<F5>', self.volume_up)
        #self.master.bind('<F6>', self.volume_down)
        self.instrument_banks = load_banks(args.banks_folder)
        self.bank_index = 0
        self.instrument_index = 0
        self.CollectionWidget = None
        self.InstrumentWidget = None
        self.InstrumentIndexWidget = None
        self.BankIndexWidget = None
        self.VolumeWidget = None
        self.create_widgets()
        self.master.wm_protocol("WM_DELETE_WINDOW", self.quit)
        #self.print_to_widget(self.VolumeWidget, self.volume)
        self.processed_command_count = 0
        self.tk = master
        self.on_update()

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

    def on_update(self):
        self.after(200, self.on_update)
        if self.last_start_zynaddsubfx - time.time() > 60*9:
            self.logger.info('restart at schedule')
            self.reset()

    def print_to_widget(self, widget, s):
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, s)

    def create_widgets(self):
        frame1 = tk.Frame(self.master)
        frame1.pack(side=tk.TOP)

        text = "F4-prev instrument, F6-next instrument, F8-prev bank, F10 - next bank"
        self.legend = tk.Label(frame1, text=text, font=('Helvetica', 12))
        self.legend.pack(side=tk.LEFT)
        tk.Button(frame1, text='Exit', command=self.quit).pack(side=tk.LEFT)
        tk.Button(frame1, text='Reset', command=self.reset).pack(side=tk.LEFT)

        frame2 = tk.Frame(self.master)
        frame2.pack(side=tk.TOP)
        fontsize = 20
        if self.main_wnd_width > 900:
            fontsize = 40
        self.CollectionWidget = tk.Text(frame2, width=self.main_wnd_width-10, height=1, font=("Helvetica", fontsize))
        self.CollectionWidget.pack(side=tk.LEFT)

        frame3 = tk.Frame(self.master)
        frame3.pack(side=tk.TOP)
        self.InstrumentWidget = tk.Text(frame3, width=self.main_wnd_width-10, height=1, font=("Helvetica", fontsize))
        self.InstrumentWidget.pack(side=tk.TOP)

        frame4 = tk.Frame(self.master)
        frame4.pack(side=tk.TOP)
        self.BankIndexWidget = tk.Text(frame4, width=3, height=1, font=("Helvetica", 200), bg="red")
        self.BankIndexWidget.bind("<Button-1>", self.next_bank)
        self.BankIndexWidget.bind("<Button-3>", self.prev_bank)
        self.BankIndexWidget.pack(side=tk.LEFT)

        self.InstrumentIndexWidget = tk.Text(frame4, width=3, height=1, font=("Helvetica", 200), bg="green")
        self.InstrumentIndexWidget.bind("<Button-1>", self.next_instrument)
        self.InstrumentIndexWidget.bind("<Button-3>", self.prev_instrument)
        self.InstrumentIndexWidget.pack(side=tk.LEFT)

        #self.VolumeWidget = tk.Text(self, width=3, height=1, font=("Helvetica", 48))
        #self.VolumeWidget.pack(side=tk.RIGHT)


        # initial time display
        self.slide_switch = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sound", "slide_switch.wav")
        self.on_change_instrument()

        frame5 = tk.Frame(self.master)
        frame5.pack(side=tk.TOP)

        btn1 = tk.Button(frame5, text='Bank', font=("Helvetica", 60), width=10,
                  command=self.next_bank, bg="red")
        btn1.bind("<Button-3>", self.prev_bank)
        btn1.pack(side=tk.LEFT, padx=50, pady=50)

        btn2 = tk.Button(frame5, text='Inst', font=("Helvetica", 60), bg="green", width=10,
                  command=self.next_instrument)
        btn2.bind("<Button-3>", self.prev_instrument)
        btn2.pack(side=tk.LEFT, padx=50, pady=50)

    def run_cmd(self, cmd):
        self.logger.info(cmd)
        os.system(cmd)

    def get_bank(self) -> TInstrumentBank :
        return self.instrument_banks[self.bank_index]

    def next_instrument(self, event=None):
        self.get_bank().increment_instrument_index(+1)
        self.on_change_instrument()

    def prev_instrument(self, event=None):
        self.get_bank().increment_instrument_index(-1)
        self.on_change_instrument()

    def next_bank(self, event=None):
        self.logger.info("next_bank")
        if self.bank_index  + 1 == len(self.instrument_banks):
            self.bank_index = 0
        else:
            self.bank_index  += 1
        self.get_bank().instrument_index = 0
        self.on_change_instrument()

    def prev_bank(self, event):
        self.logger.info("prev_bank")
        if self.bank_index > 0:
            self.bank_index -= 1
        else:
            self.bank_index = len(self.instrument_banks) - 1
        self.get_bank().instrument_index = 0
        self.on_change_instrument()

    def set_instrument_in_zynsubfx(self):
        self.send_command_to_zynaddsubfx("load_instrument {}".format(self.get_bank().get_instrument_path()))

    def on_change_instrument(self):
        if self.processed_command_count > 20:
            self.reset()
        self.processed_command_count += 1
        self.print_to_widget(self.CollectionWidget, self.get_bank().name)
        self.print_to_widget(self.InstrumentWidget, self.get_bank().get_instrument_name())
        self.print_to_widget(self.InstrumentIndexWidget, "{}".format(self.get_bank().instrument_index))
        self.print_to_widget(self.BankIndexWidget, "{}".format(self.bank_index))
        self.set_instrument_in_zynsubfx()
        time.sleep(0.2)
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
            self.run_zynaddsubfx()
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
        self.processed_command_count = 0
        self.last_start_zynaddsubfx = time.time()
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
        for proc in psutil.process_iter():
            if proc.pid  == os.getpid():
                continue
            elif proc.name() == ZYNADDSUBFX_BINARY:
                os.kill(proc.pid, signal.SIGKILL)
            elif proc.name() == 'ffplay':
                os.kill(proc.pid, signal.SIGKILL)

    def reset(self):
        self.run_zynaddsubfx()
        self.set_instrument_in_zynsubfx()

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
    parser.add_argument("--zynaddsubfx-path", dest='zynaddsubfx_path', default='/usr/bin/zynaddsubfx')
    parser.add_argument("--zynaddsubfx-args", dest='zynaddsubfx_args', default="-a -U -I alsa -O alsa")
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

    #play_file("sound/slide_switch.wav")

    try:
        tk_app.master.mainloop()
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt")
        tk_app.quit()


if __name__ == '__main__':
    main()