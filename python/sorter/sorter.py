import os
import sys
import logging
import tkinter as tk
import argparse
import random
import math
from PIL import Image, ImageTk
import time

import vlc



def play_file(filename):
    player = vlc.MediaPlayer(os.path.join(os.path.dirname(__file__), "audio", filename))
    player.play()
    time.sleep(1)
    while player.is_playing():
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


class TCollection:
    basic = 1
    vehicles = 2
    geometric = 3
    russian_abc = 4
    birds = 5
    all = 6

    @staticmethod
    def get_collection_name(id):
        if id == TCollection.basic:
            return "basic"
        elif id == TCollection.vehicles:
            return "vehicles"
        elif id == TCollection.geometric:
            return "geometric"
        elif id == TCollection.russian_abc:
            return "russian_abc"
        elif id == TCollection.birds:
            return "birds"
        elif id == TCollection.all:
            return "all"


class TSpriteForm:
    sprite_width = 200
    sprite_height = 200
    font_size = 90

    def __init__(self, collection_id, form=None, color=None, image_path=None, char=None):
        self.collection_id = collection_id
        self.form = form
        self.color = color
        self.image_path = image_path
        self.char = char
        self.image = None
        if image_path is not None:
            image = Image.open(image_path)
            image = image.resize((TSpriteForm.sprite_width, TSpriteForm.sprite_height), Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(image)

    def is_equal(self, other):
        return other.form == self.form and \
               other.color == self.color and \
               other.image_path == self.image_path and \
               other.char == self.char

    def play_success(self):
        specific_mp3 = os.path.join("audio", str(self)+".mp3")
        if os.path.exists(specific_mp3):
            play_file(os.path.basename(specific_mp3))
        else:
            play_file("success.mp3")

    def __str__(self):
        if self.image_path is not None:
            main_name, _ = os.path.splitext(os.path.basename(self.image_path))
            return "{}.{}".format(TCollection.get_collection_name(self.collection_id), main_name)
        elif self.char is not None:
            return "char.{}".format(self.char)
        else:
            return "geometric.{}.{}".format(self.color, self.form)


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
        self.hide_sprite()

        if self.sprite_form.form == "rectangle":
            self.id = self.frame.canvas.create_rectangle(
                self.point.x, self.point.y,
                self.point.x + TSpriteForm.sprite_width, self.point.y + TSpriteForm.sprite_height,
                outline=self.sprite_form.color, fill=self.sprite_form.color)
        elif self.sprite_form.form == "triangle":
            self.id = self.frame.canvas.create_polygon(
                self.point.x, self.point.y,
                self.point.x + TSpriteForm.sprite_width,   self.point.y,
                self.point.x + TSpriteForm.sprite_width / 2, self.point.y + TSpriteForm.sprite_height,
                self.point.x, self.point.y,
                outline=self.sprite_form.color, fill=self.sprite_form.color)
        elif self.sprite_form.form == "pentagram":
            points = pentagram_points(self.point.x + TSpriteForm.sprite_width/2,
                                      self.point.y + TSpriteForm.sprite_height/2,
                                      TSpriteForm.sprite_width/2)
            self.id = self.frame.canvas.create_polygon(points, outline=self.sprite_form.color, fill=self.sprite_form.color)
        elif self.sprite_form.form == "circle":
            self.id = self.frame.canvas.create_oval(
                self.point.x, self.point.y,
                self.point.x + TSpriteForm.sprite_width, self.point.y + TSpriteForm.sprite_height,
                outline=self.sprite_form.color, fill=self.sprite_form.color)
        elif self.sprite_form.image_path is not None:
            self.id = self.frame.canvas.create_image(self.point.x + TSpriteForm.sprite_width/2,
                                           self.point.y + TSpriteForm.sprite_height/2,
                                           image=self.sprite_form.image)
        elif self.sprite_form.char is not None:
            self.id = self.frame.canvas.create_text(self.point.x + TSpriteForm.sprite_width/2,
                                                    self.point.y + TSpriteForm.sprite_height/2,
                                                    text=self.sprite_form.char,
                                                    justify=tk.CENTER, font="Verdana {}".format(TSpriteForm.font_size))

    def hide_sprite(self):
        if self.id is not None:
            self.frame.canvas.delete(self.id)

    def matches(self, sprite):
        if abs(self.point.x - sprite.point.x) < 50 and abs(self.point.y - sprite.point.y) < 50:
            return self.sprite_form.is_equal(sprite.sprite_form)
        return None


class TSpriteFormCollections:

    @staticmethod
    def _read_folder(collection_id):
        sprites = list()
        folder = TCollection.get_collection_name(collection_id)
        for fpath in os.listdir(os.path.join(os.path.dirname(__file__), folder)):
            sprites.append(TSpriteForm(collection_id, image_path=os.path.join(folder, fpath)))
        return sprites

    def __init__(self):
        self.basic_forms = TSpriteFormCollections._read_folder(TCollection.basic)
        self.vehicles_forms = TSpriteFormCollections._read_folder(TCollection.vehicles)
        self.geometric_forms = [TSpriteForm(TCollection.geometric, form=f, color=c) for c in
                                ["blue", "red", "yellow", "black"] \
                                for f in ["rectangle", "triangle", "circle", "pentagram"]]
        self.russian_abc = [TSpriteForm(TCollection.russian_abc, char=a) for a in
                            "АЕИЯЮЭЁАЕИЯЮЭЁАБВГДЕЁЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"]
        # three times vowels
        self.bird = TSpriteFormCollections._read_folder(TCollection.birds)

    def get_forms(self, c_id):
        if c_id == TCollection.basic:
            return self.basic_forms
        elif c_id == TCollection.vehicles:
            return self.vehicles_forms
        elif c_id == TCollection.geometric:
            return self.geometric_forms
        elif c_id == TCollection.russian_abc:
            return self.russian_abc
        elif c_id == TCollection.birds:
            return self.bird
        else:
            return self.basic_forms + self.vehicles_forms + self.geometric_forms + self.russian_abc + self.bird


class TApplication(tk.Frame):
    def __init__(self, args, logger, master):
        super().__init__(master)
        self.args = args
        self.goals_count = args.goals_count
        self.logger = logger
        self.redrawing = False
        self.master = master
        self.set_main_window_geometry()
        self.pack(expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(self, bg="white")
        self.collection_id = tk.IntVar(value=TCollection.basic)
        self.bottom_command_line_height = 20
        self.canvas_height = self.master.winfo_height() - self.bottom_command_line_height
        self.collections = TSpriteFormCollections()
        self.goals_count_str = tk.StringVar()
        self.goals_count_str.set(str(self.goals_count))
        self.goals = None
        self.sprite = TSprite(self)
        self.create_widgets()
        self.bind_keys()
        self.moving_step = 5
        self.orientation = 'bottom_up'
        master.wm_protocol("WM_DELETE_WINDOW", self.quit_command )
        self.canvas.update()

    def bind_keys(self):
        self.master.bind('<Left>', self.left_key)
        self.master.bind('<Right>', self.right_key)
        self.master.bind('<Up>', self.up_key)
        self.master.bind('<Down>', self.down_key)
        self.master.bind("<Configure>", self.resize)
        self.master.bind('<Control-n>', self.init_new_game)
        self.master.bind('<Control-N>', self.init_new_game)
        self.master.bind("<Button-3>", self.init_new_game)
        self.master.bind('<Control-x>', self.quit_command)
        self.master.bind('<Control-X>', self.quit_command)
        self.master.bind('<Control-c>', self.stop_game)
        self.master.bind('<Control-C>', self.stop_game)
        self.master.bind('<Control-b>', self.bind_mouse)
        self.unbind_mouse_move()

    def set_main_window_geometry(self):
        if self.args.fullscreen:
            self.master.attributes('-fullscreen', True)
            TSpriteForm.sprite_width = 300
            TSpriteForm.sprite_height = 300
            TSpriteForm.font_size = 180
        else:
            TSpriteForm.sprite_width = 100
            TSpriteForm.sprite_height = 100
            TSpriteForm.font_size = 45
            self.master.geometry("600x500+100+100")
        self.master.update()

    def resize(self, event):
        if event.widget == self:
            self.canvas_height = event.height - self.bottom_command_line_height
            self.canvas.config(width=event.width, height=self.canvas_height)

    def check_end_of_game(self):
        for g in self.goals:
            m = self.sprite.matches(g)
            if m is not None:
                self.unbind_mouse_move()
                if m:
                    self.canvas.configure(bg="green")
                    self.canvas.update()
                    self.sprite.sprite_form.play_success()
                else:
                    self.canvas.configure(bg="red")
                    self.canvas.update()
                    play_file("fail.mp3")

    def redraw_canvas(self, sprite_x, sprite_y):
        if self.sprite.point is None:
            return
        if self.redrawing:
            return
        if sprite_x <= 0:
            sprite_x = 1
        if sprite_y <= 0:
            sprite_y = 1
        if sprite_x > self.canvas.winfo_width() - TSpriteForm.sprite_width:
            sprite_x = self.canvas.winfo_width() - TSpriteForm.sprite_width
        if sprite_y > self.canvas.winfo_height() - TSpriteForm.sprite_height:
            sprite_y = self.canvas.winfo_height() - TSpriteForm.sprite_height
        self.redrawing = True
        try:
            self.sprite.hide_sprite()
            self.sprite.point.x = sprite_x
            self.sprite.point.y = sprite_y
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

    def move_mouse(self, x, y):
        sys.stderr.write("move_mouse {},{}\n".format(x, y))
        self.event_generate('<Motion>', warp=True, x=x, y=y, when="now")

    def mouse_motion_handler(self, event):
        if self.args.fullscreen:
            if event.x > self.canvas.winfo_width() - TSpriteForm.sprite_width:
                self.move_mouse(self.canvas.winfo_width() - TSpriteForm.sprite_width, event.y)
                return
            if event.y > self.canvas.winfo_height() - TSpriteForm.sprite_height:
                self.move_mouse(event.x, self.canvas.winfo_height() - TSpriteForm.sprite_height)
                return
        if event.widget == self.canvas:
            sys.stderr.write("{},{}, {}\n".format(event.x, event.y, event))
            self.redraw_canvas(
                    event.x,
                    event.y)

    def bind_mouse(self, event):
        self.master.bind('<Motion>', self.mouse_motion_handler)

    def generate_bind_mouse_event(self):
        self.event_generate('<Control-b>')

    def unbind_mouse_move(self):
        self.master.unbind('<Motion>')

    def get_start_point(self, padding=10):
        vertical_half = (self.canvas.winfo_width() - TSpriteForm.sprite_width) / 2
        horizontal_half = (self.canvas.winfo_height() - TSpriteForm.sprite_height) / 2
        bottom = self.canvas.winfo_height() - TSpriteForm.sprite_height - padding
        up = padding
        left = padding
        right = self.canvas.winfo_width() - TSpriteForm.sprite_width - padding

        if self.orientation == 'bottom_up':
            return TPoint(vertical_half, bottom)
        if self.orientation == 'up_bottom':
            return TPoint(vertical_half, up)
        if self.orientation == 'left_right':
            return TPoint(left, horizontal_half)
        if self.orientation == 'right_left':
            return TPoint(right, horizontal_half)
        assert False

    def draw_goals_horizontal(self, forms, padding, y):
        sum_goals_width = TSpriteForm.sprite_width * self.goals_count
        gap_width = (self.canvas.winfo_width() - 2 * padding - sum_goals_width) / (self.goals_count - 1)
        x = padding

        for f, g in zip(forms, self.goals):
            g.sprite_form = f
            g.point = TPoint(x, y)
            x += TSpriteForm.sprite_width + gap_width
            g.draw_sprite()

    def draw_goals_vertically(self, forms, padding, x):
        sum_goals_height = TSpriteForm.sprite_height * self.goals_count
        gap_height = (self.canvas.winfo_height() - 2 * padding - sum_goals_height) / (self.goals_count - 1)
        y = padding

        for f, g in zip(forms, self.goals):
            g.sprite_form = f
            g.point = TPoint(x, y)
            y += TSpriteForm.sprite_height + gap_height
            g.draw_sprite()

    def init_new_game(self, event=None):
        padding = 10
        self.canvas.delete("all")
        self.canvas.configure(bg="white")
        self.goals_count = int(self.goals_count_str.get())
        self.goals = [TSprite(self) for i in range(self.goals_count)]
        self.orientation = random.choice(['bottom_up', 'up_bottom', 'left_right', 'right_left'])
        #self.orientation = 'right_left'
        start_point = self.get_start_point(padding)
        self.sprite.point = TPoint(start_point.x, start_point.y)

        all_forms = self.collections.get_forms(self.collection_id.get())
        forms = random.sample(all_forms, self.goals_count)
        for f in forms:
            self.logger.debug(str(f))

        if self.orientation == 'bottom_up':
            self.draw_goals_horizontal(forms, padding, padding)
        if self.orientation == 'up_bottom':
            self.draw_goals_horizontal(forms, padding, self.canvas.winfo_height() - TSpriteForm.sprite_height - padding)
        if self.orientation == 'left_right':
            self.draw_goals_vertically(forms, padding, self.canvas.winfo_width() - TSpriteForm.sprite_width - padding)
        if self.orientation == 'right_left':
            self.draw_goals_vertically(forms, padding, padding)

        self.sprite.sprite_form = random.choice(forms)
        self.sprite.draw_sprite()

        self.move_mouse(start_point.x, start_point.y)
        self.generate_bind_mouse_event()

    def stop_game(self, event=None):
        self.canvas.delete("all")
        self.canvas.configure(bg="white")
        self.unbind_mouse_move()

    def quit_command(self, event=None   ):
        self.master.destroy()
        sys.exit(0)

    def place_control(self, index, widget):
       widget.place(x=10 + index * 80, y=self.canvas_height + 1, width=70, height=self.bottom_command_line_height - 2)

    def create_widgets(self):
        self.canvas.place(x=0, y=0, width=self.master.winfo_width(), height=self.canvas_height)
        self.place_control(0, tk.Button(self, text="Выйти", command=self.quit_command))
        self.place_control(1, tk.Button(self, text="Новая", command=self.init_new_game))
        self.place_control(2, tk.Entry(textvariable=self.goals_count_str))
        self.place_control(3, tk.Radiobutton(text='основ', variable=self.collection_id, value=TCollection.basic))
        self.place_control(4, tk.Radiobutton(text='машины', variable=self.collection_id, value=TCollection.vehicles))
        self.place_control(5, tk.Radiobutton(text='формы', variable=self.collection_id, value=TCollection.geometric))
        self.place_control(6, tk.Radiobutton(text='буквы', variable=self.collection_id, value=TCollection.russian_abc))
        self.place_control(7, tk.Radiobutton(text='птицы', variable=self.collection_id, value=TCollection.birds))
        self.place_control(8, tk.Radiobutton(text='все', variable=self.collection_id, value=TCollection.all))


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
    tk_application = TApplication(args, logger, master=root)
    try:
        tk_application.mainloop()
    except Exception as e:
        root.destroy()
        logger.error(e)


if __name__ == "__main__":
    logger = setup_logging("sorter.log")
    main(logger)
