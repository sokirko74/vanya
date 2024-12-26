
import tkinter as tk
import json
from movements import detect_movements

SampleBase = None

def motion_handler_wrapper(event):
    global SampleBase
    SampleBase.motion_handler(event)

def write_example(sign):
    global SampleBase
    if len(SampleBase.Points) > 0:
        with open("examples.txt", "a", encoding="utf8") as outf:
            res  = {"sign": sign, "points": SampleBase.Points}
            outf.write (json.dumps(res) + "\n")
        SampleBase.clear()

def leftKey(event):
    write_example("left")

def rightKey(event):
    write_example("right")

def upKey(event):
    write_example("up")

def downKey(event):
    write_example("down")

def unknownKey(event):
    write_example("unknown")

def clearKey(event):
    global SampleBase
    SampleBase.clear()

def detectKey(event):
    global SampleBase
    SampleBase.detect_movements()

def startKey(event):
    global SampleBase
    SampleBase.StartDraw = not SampleBase.StartDraw


def showKey(event):
    global SampleBase

    with open("examples.txt", "r", encoding="utf8") as inpf:
        samples = []
        for x in inpf:
            samples.append (json.loads(x))
        if SampleBase.SampleIndex >=  len(samples):
            SampleBase.SampleIndex = 0
        SampleBase.clear()
        SampleBase.Points = samples[SampleBase.SampleIndex]['points']
        SampleBase.draw_points()
        SampleBase.Text.delete('1.0', tk.END)
        SampleBase.Text.insert(tk.END, "{}: {}".format(SampleBase.SampleIndex,
                                                    json.dumps(samples[SampleBase.SampleIndex])))
        SampleBase.SampleIndex +=  1


class TSampleBase(tk.Frame):

    def __init__(self):
        super().__init__()
        self.SampleIndex = 0
        self.initUI()
        self.Points = list()
        self.StartDraw =  False

    def initUI(self):

        self.pack(fill=tk.BOTH, expand=1)

        self.TextFrame = tk.Frame(self)
        self.TextFrame.pack(side=tk.TOP)

        self.Text = tk.Text(self.TextFrame, height=5)
        self.Text.pack(side=tk.LEFT)
        self.Solution = tk.Text(self.TextFrame, height=5)
        self.Solution.pack(side=tk.RIGHT)

        self.CanvasFrame = tk.Frame(self)
        self.CanvasFrame.pack(fill=tk.BOTH, expand=1)
        self.Canvas = tk.Canvas(self.CanvasFrame, bg="blue")
        self.Canvas.pack(fill=tk.BOTH, expand=1)


    def clear(self):
        self.Points = list()
        self.Canvas.delete("all")
        self.Text.delete('1.0', tk.END)
        self.Solution.delete('1.0', tk.END)

    def detect_movements (self):
        self.Solution.delete('1.0', tk.END)
        self.Solution.insert(tk.END, json.dumps(detect_movements(self.Points)))

    def draw_points (self):
        for i in range (1, len(self.Points)):
            self.Canvas.create_line(self.Points[i-1][0], self.Points[i-1][1], self.Points[i][0], self.Points[i][1])
        self.Text.delete('1.0', tk.END)
        self.Text.insert(tk.END, json.dumps(self.Points))

    def motion_handler(self, event):
        cur_x = event.x
        cur_y = event.y
        if self.StartDraw:
            point = (cur_x,  cur_y)
            if len(self.Points) == 0 or self.Points[-1] != point:
                self.Points.append(point)
            self.draw_points()


def main(points=None):

    root = tk.Tk()
    global SampleBase
    SampleBase = TSampleBase()
    root.geometry("900x500")
    if points != None:
        SampleBase.Points = points
        SampleBase.draw_points()

    root.bind('<Motion>', motion_handler_wrapper)
    root.bind('<Shift-Left>', leftKey)
    root.bind('<Shift-Right>', rightKey)
    root.bind('<Shift-Up>', upKey)
    root.bind('<Shift-Down>', downKey)
    root.bind('<Shift-u>', unknownKey)
    root.bind('<Shift-U>', unknownKey)
    root.bind('<Escape>', unknownKey)
    root.bind('<e>', showKey)
    root.bind('<E>', showKey)
    root.bind('<s>', startKey)
    root.bind('<S>', startKey)
    root.bind('<d>', detectKey)
    root.bind('<D>', detectKey)
    root.mainloop()


if __name__ == '__main__':
    with open("examples.txt", "r", encoding="utf8") as inpf:
        samples = []
        for x in inpf:
            sample = json.loads(x)
            movements = detect_movements(sample['points'])
            if len(movements) == 1 and sample['sign'] == 'unknown':
                print ("test failed")
                main(sample['points'])
                exit(1)


    main()