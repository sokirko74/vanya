import os
import sys
import logging
import tkinter as tk
from functools import partial
import argparse
import random
import math
from PIL import Image, ImageTk
import time
from pygame import mixer


def myquit(root):
    root.destroy()
    sys.exit(0)


def play_file(filename):
    mixer.init()
    mixer.music.load(os.path.join(os.path.dirname(__file__), "audio", filename))
    mixer.music.play()
    while mixer.get_busy():
        time.sleep(1)



def pentagram_points(center_x, center_y, r):
    return [
        #
        center_x - int(r * math.sin(2 * math.pi / 5)),
        center_y - int(r * math.cos(2 * math.pi / 5)),

        #
        center_x + int(r * math.sin(2 * math.pi / 5)),
        center_y - int(r * math.cos(2 * math.pi / 5)),

        #
        center_x - int(r * math.sin(math.pi / 5)),
        center_y + int(r * math.cos(math.pi / 5)),

        # vertex
        center_x,
        center_y - r,

        #
        center_x + int(r * math.sin(math.pi / 5)),
        center_y + int(r * math.cos(math.pi / 5)),
    ]


class TSpriteForm:
    def __init__(self, form=None, color=None, jpg=None):
        self.form = form
        self.color = color
        self.jpg = jpg
        self.image = None
        if jpg is not None:
            self.image = ImageTk.PhotoImage(Image.open(jpg))

    def is_equal(self, other):
        return other.form == self.form and other.color == self.color and other.jpg == self.jpg

    def __str__(self):
        if self.jpg is not None:
            return "TSpriteForm: jpg={}".format(self.jpg)
        else:
            return "TSpriteForm:{} {}".format(self.color, self.form)


class TPoint:
    def __init__ (self,x, y):
        self.x = x
        self.y = y


class TSprite:
    def __init__(self, frame):
        self.frame = frame
        self.point = None
        self.sprite_form: TSpriteForm = None
        self.id = None

    def draw_sprite(self):
        color = self.sprite_form.color
        self.hide_sprite()

        if self.sprite_form.form == "rectanglbe":
            self.id = self.frame.canvas.create_rectangle(
                self.point.x, self.point.y,
                self.point.x + self.frame.sprite_width, self.point.y + self.frame.sprite_height,
                outline=color, fill=color)
        elif self.sprite_form.form == "triangle":
            self.id = self.frame.canvas.create_polygon(
                self.point.x, self.point.y,
                self.point.x + self.frame.sprite_width,   self.point.y,
                self.point.x + self.frame.sprite_width / 2, self.point.y + self.frame.sprite_height,
                self.point.x, self.point.y,
                outline=color, fill=color)
        elif self.sprite_form.form == "pentagram":
            points = pentagram_points(self.point.x + self.frame.sprite_width/2,
                                      self.point.y + self.frame.sprite_height/2,
                                      self.frame.sprite_width/2)
            self.id = self.frame.canvas.create_polygon(points, outline=color, fill=color)
        elif self.sprite_form.form == "circle":
            self.id = self.frame.canvas.create_oval(
                self.point.x, self.point.y,
                self.point.x + self.frame.sprite_width, self.point.y + self.frame.sprite_height,
                outline=color, fill=color)
        elif self.sprite_form.jpg is not None:
            self.id = self.frame.canvas.create_image(self.point.x + self.frame.sprite_width/2,
                                           self.point.y + self.frame.sprite_height/2,
                                           image=self.sprite_form.image)

    def hide_sprite(self):
        if self.id is not None:
            self.frame.canvas.delete(self.id)

    def matches(self, sprite):
        if abs(self.point.x - sprite.point.x) < 30 and abs(self.point.y - sprite.point.y) < 30:
            return self.sprite_form.is_equal(sprite.sprite_form)
        return None


def read_folder(folder):
    sprites = list()
    for fpath in os.listdir(os.path.join(os.path.dirname(__file__), folder)):
        sprites.append(TSpriteForm(jpg=os.path.join(folder, fpath)) )
    return sprites


class TCollection:
    basic = 1
    vehicle = 2
    geometric = 3
    all = 4


class TApplication(tk.Frame):
    def __init__(self, logger, master, goals_count):
        super().__init__(master)
        self.logger = logger
        self.redrawing = False
        self.master = master
        self.pack(expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(self, bg="white")
        self.goal_up_margin = 10
        self.goal_horizontal_margin = 10
        self.sprite_width = 100
        self.sprite_height = 100
        self.collection_id = tk.IntVar(value=TCollection.basic)
        self.bottom_command_line_height = 20
        self.canvas_height = self.master.winfo_height() - self.bottom_command_line_height
        self.basic_forms = read_folder("basic")
        self.vehicles_forms = read_folder("vehicles")
        self.geometric_forms = [TSpriteForm(form=f, color=c) for c in ["blue", "red", "yellow", "black"] \
                                    for f in ["rectangle", "triangle", "circle", "pentagram"] ]

        self.goals_count = goals_count
        self.goals_count_str = tk.StringVar()
        self.goals_count_str.set(str(self.goals_count))
        self.goals = None
        self.sprite = TSprite(self)
        self.create_widgets()
        master.bind('<Left>', self.left_key)
        master.bind('<Right>', self.right_key)
        master.bind('<Up>', self.up_key)
        master.bind('<Down>', self.down_key)
        master.bind("<Configure>", self.resize)
        self.master.bind('<Control-n>', self.init_new_game)
        self.master.bind('<Control-N>', self.init_new_game)

        self.moving_step = 5

    def resize(self, event):
        if event.widget == self:
            self.canvas_height = event.height - self.bottom_command_line_height
            self.canvas.config(width=event.width, height=self.canvas_height)

    def check_end_of_game(self):
        for g in self.goals:
            m = self.sprite.matches(g)
            if m is not None:
                if m:
                    self.canvas.configure(bg="green")
                    play_file("success.mp3")
                else:
                    self.canvas.configure(bg="red")
                    play_file("fail.mp3")
                self.canvas.update()
                self.unbind_mouse_move()
                time.sleep(2)
                self.init_new_game()
                return

    def redraw_canvas(self, x, y):
        if self.sprite.point is None:
            return
        if x < 0 or y < 0:
            return
        if x > self.canvas.winfo_width() - self.sprite_width:
            return
        if y > self.canvas.winfo_height() - self.sprite_height:
            return
        if self.redrawing:
            return
        self.redrawing = True
        try:
            self.sprite.hide_sprite()
            self.sprite.point.x = x
            self.sprite.point.y = y
            for g in self.goals:
                g.draw_sprite()
            self.sprite.draw_sprite()
            self.check_end_of_game()
        finally:
            self.redrawing = False

    def redraw_canvas_delta(self, delta_x, delta_y):
        if self.sprite.point is None:
            return
        x = self.sprite.point.x + delta_x
        y = self.sprite.point.y + delta_y
        return self.redraw_canvas(x, y)

    def left_key(self, event):
        self.redraw_canvas_delta(-self.moving_step, 0)

    def right_key(self, event):
        self.redraw_canvas_delta(+self.moving_step, 0)

    def up_key(self, event):
        self.redraw_canvas_delta(0, -self.moving_step)

    def down_key(self, event):
        self.redraw_canvas_delta(0, +self.moving_step)

    def motion_handler(self, event):
        self.redraw_canvas(
            event.x - self.sprite_width/2,
            event.y - self.sprite_height/2)

    def bind_mouse_move(self):
        self.master.bind('<Motion>', self.motion_handler)

    def unbind_mouse_move(self):
        self.master.unbind('<Motion>')

    def get_forms(self):
        c_id = self.collection_id.get()
        if c_id == TCollection.basic:
            return self.basic_forms
        elif c_id == TCollection.vehicle:
            return self.vehicles_forms
        elif c_id == TCollection.geometric:
            return self.geometric_forms
        else:
            return self.basic_forms + self.vehicles_forms + self.geometric_forms

    def init_new_game(self,event=None):
        self.canvas.delete("all")
        self.canvas.configure(bg="white")
        self.goals_count = int(self.goals_count_str.get())
        self.goals = [TSprite(self) for i in range(self.goals_count)]

        start_x = (self.canvas.winfo_width() - self.sprite_width) / 2
        start_y = self.canvas.winfo_height() - self.sprite_height - 2
        self.sprite.point = TPoint(start_x, start_y)
        self.event_generate('<Motion>', warp=True, x=start_x+self.sprite_width/2, y=start_y+self.sprite_height/2)
        self.bind_mouse_move()
        all_forms = self.get_forms()
        forms = random.sample(all_forms, self.goals_count)
        for f in forms:
            self.logger.debug(str(f))
        sum_goals_width = self.sprite_width * self.goals_count
        gap_width = (self.canvas.winfo_width() - 2 * self.goal_horizontal_margin - sum_goals_width)/(self.goals_count -1)
        x = self.goal_horizontal_margin
        for f, g in zip(forms, self.goals):
            g.sprite_form = f
            g.point = TPoint(x, self.goal_up_margin)
            x += self.sprite_width + gap_width
            g.draw_sprite()

        self.sprite.sprite_form = random.choice(forms)
        self.sprite.draw_sprite()

    def quit_command(self):
        myquit(self.master)

    def place_control(self, index, widget):
       widget.place(x=10 + index * 80, y=self.canvas_height + 1, width=70, height=self.bottom_command_line_height - 2)

    def create_widgets(self):
        self.canvas.place(x=0, y=0, width=self.master.winfo_width(), height=self.canvas_height)
        self.place_control(0, tk.Button(self, text="Выйти", command=self.quit_command))
        self.place_control(1, tk.Button(self, text="Новая", command=self.init_new_game))
        self.place_control(2, tk.Entry(textvariable=self.goals_count_str))
        self.place_control(3, tk.Radiobutton(text='основ', variable=self.collection_id, value=TCollection.basic))
        self.place_control(4, tk.Radiobutton(text='машины', variable=self.collection_id, value=TCollection.vehicle))
        self.place_control(5, tk.Radiobutton(text='формы', variable=self.collection_id, value=TCollection.geometric))
        self.place_control(6, tk.Radiobutton(text='все', variable=self.collection_id, value=TCollection.all))


def setup_logging(logfilename):
    logger = logging.getLogger("dlrobot_logger")
    logger.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if os.path.exists(logfilename):
        os.remove(logfilename)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(logfilename, encoding="utf8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    return logger


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--not-fullscreen", dest='fullscreen', default=True, action="store_false")
    parser.add_argument("--goals-count", dest='goals_count', default=2, required=False)

    return parser.parse_args()


def main(logger):
    args = parse_args()
    root = tk.Tk()
    root.wm_protocol("WM_DELETE_WINDOW", partial(myquit, root) )
    if args.fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry("600x500+100+100")
    root.update()
    tk_application = TApplication(logger, master=root, goals_count=args.goals_count)

    try:
        tk_application.mainloop()
    except Exception as e:
        logger.error(e)
        myquit()


if __name__ == "__main__":
    logger = setup_logging("sorter.log")
    main(logger)


#1. не работает
#2. добавит картинки: домик, буквы, значки автомобиля, цифры
#3. Добавить звук
#4. Птицы  и их звучание
#5. мышь