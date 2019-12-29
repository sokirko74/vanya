import tkinter as tk
import os
import glob
import time
import statistics
from movements import detect_movements

APPLICATION = None

def current_iso8601():
    """Get current date and time in ISO8601"""
    # https://en.wikipedia.org/wiki/ISO_8601
    # https://xkcd.com/1179/
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

def motion_handler_wrapper(event):
    global APPLICATION
    APPLICATION.motion_handler(event)


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
    def __init__(self, master=None):

        self.Master = master
        master.geometry("900x600")

        self.Instruments = [f for f in glob.glob("/usr/share/zynaddsubfx/banks/Collection/*.xiz")]
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

        tk.Button(master=self, text='Exit', command=self.Master.destroy).pack(side=tk.TOP)

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

    def clear(self):
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

    def try_to_detect_movement(self):
        points = [(x,y) for (_, x, y) in self.Points]
        movements = detect_movements(points)
        if len(movements) == 1:
            movement = list(movements.items())[0][0]
            if movement == "up":
                self.increment_instrument_index(1)
            elif movement == "down":
                self.increment_instrument_index(-1)
            if movement in {"up", "down"}:
                print( '{}: {} \n'.format(str(movements), str(points)))
                self.clear()
                self.run_zynadd()


        self.clear()

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
                self.clear()
                self.bind_moise_move()

        # schedule timer to call myself after 1 second
        self.after(200, self.onUpdate)


    def run_zynadd(self):
        instrument = self.Instruments[self.InstrumentIndex]
        self.print_log(self.InstrumentWidget, "{}".format(instrument))
        self.print_log(self.InstrumentIndexWidget, "{}".format(self.InstrumentIndex))
        os.system ("pkill zynaddsubfx")
        #os.system("zynaddsubfx --no-gui --auto-connect --output jack --load-instrument '{}' &".format(instrument))
        #os.system("zynaddsubfx --no-gui --auto-connect --output alsa --load-instrument '{}' &".format(instrument))
        os.system("zynaddsubfx  --no-gui --auto-connect --output alsa --load-instrument='{}' &".format(instrument))
        time.sleep(0.5)

        os.system("aconnect microKEY-25 ZynAddSubFX")

    def increment_instrument_index(self, delta):
        self.InstrumentIndex += delta
        if self.InstrumentIndex >= len(self.Instruments):
            self.InstrumentIndex = 0
        if self.InstrumentIndex < 0:
            self.InstrumentIndex = len(self.Instruments) - 1

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

if __name__ == '__main__':
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    APPLICATION = Application(master=root)
    root.mainloop()

