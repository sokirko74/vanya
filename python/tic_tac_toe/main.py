# importing the required libraries
import pygame as pg
import time
from pygame.locals import *
import numpy
from collections import defaultdict
import argparse

WHITE = (255, 255, 255)
RED = (255, 0, 0)
LINE_COLOR = (0, 0, 0)
CELL_LINE_WIDTH = 2


class TicTacToe:
    unknown_player = 0
    o_player = 1
    x_player = 2
    
    def __init__(self, rows=3, cols=3, win_len=3):
        self.winner = None
        self.window_width = 1000
        self.window_height = 1000
        self.board_rows = rows
        self.board_cols = cols
        self.win_length = win_len
        self.board = None
        self.current_player = None
        self.scores = defaultdict(int)
        self.margin = int(self.cell_width() / 20)
        self.win_id = 0
        self.screen = pg.display.set_mode((self.window_width, self.window_height), 0, 32)
        sign_size =  (self.cell_width()-self.margin * 2, self.cell_height()-self.margin * 2)
        self.x_image = pg.transform.scale(pg.image.load("X_modified.png"), sign_size)
        self.o_image = pg.transform.scale(pg.image.load("o_modified.png"), sign_size)
        self.draw_game_init()

    def cell_width(self):
        return int(self.window_width / self.board_cols)

    def cell_height(self):
        return int(self.window_height / self.board_rows)

    def get_rect(self, row, col):
        return pg.Rect(self.cell_width() * col,
                           self.cell_height() * row,
                           self.cell_width(),
                           self.cell_height())

    def get_center_point(self, row, col):
        return self.get_rect(row, col).center

    def draw_game_init(self):
        self.win_id = 0
        matrix = list()
        for i in range(self.board_rows):
            row = list()
            for k in range(self.board_cols):
                row.append((i, k, self.unknown_player, 0))
            matrix.append(row)

        self.board = numpy.array(matrix, dtype=[('row', 'i8'), ('col', 'i8'), ('player', 'i8'), ('win_id', 'i8')])
        self.scores.clear()
        self.current_player = self.x_player
        self.screen.fill(WHITE)
        for col in range(self.board_cols):
            x = (col + 1) * self.cell_width()
            pg.draw.line(self.screen, LINE_COLOR, (x, 0), (x, self.window_height), CELL_LINE_WIDTH)

        for row in range(self.board_rows):
            y = (row + 1) * self.cell_height()
            pg.draw.line(self.screen, LINE_COLOR, (0, y), (self.window_width, y), CELL_LINE_WIDTH)

    def draw_win_line(self, points):
        x1, y1 = self.get_center_point(points[0]['row'], points[0]['col'])
        x2, y2 = self.get_center_point(points[-1]['row'], points[-1]['col'])
        pg.draw.line(self.screen, RED, (x1, y1), (x2, y2), 10)

        player = self.board[points[0]['row'], points[0]['col']]['player']
        self.scores[player] += 1
        self.win_id += 1
        for p in points:
            self.board[p['row'], p['col']]['player'] = player
            self.board[p['row'], p['col']]['win_id'] = self.win_id

    def find_win_segment(self, board_array, index):
        p = board_array[index]['player']
        start = index
        prev_win_id = None
        while start >= 0:
            if board_array[start]['player'] != p:
                start += 1
                break
            if board_array[start]['win_id'] == prev_win_id and prev_win_id > 0:
                start += 1
                break
            if start == 0:
                break
            prev_win_id = board_array[start]['win_id']
            start -= 1
        end = index
        prev_win_id = None
        while end < len(board_array):
            if board_array[end]['player'] != p:
                break
            if board_array[end]['win_id'] == prev_win_id and prev_win_id > 0:
                break
            prev_win_id = board_array[end]['win_id']
            end += 1
        if end - start >= self.win_length:
            w =  board_array[start:start+self.win_length]
            self.draw_win_line(w)
        else:
            return None

    def transpose(self):
        self.board = numpy.transpose(self.board)

    def diagonal1(self, row, col):
        min_rc = min(row, col)
        x = row - min_rc
        y = col - min_rc
        r = list()
        index = None
        while x < self.board_rows and y < self.board_cols:
            r.append(self.board[x,y])
            if x == row and y == col:
                index = len(r) - 1
            x += 1
            y += 1
        return numpy.array(r), index

    def diagonal2(self, row, col):
        min_rc = min(self.board_rows  - row -1 , col)
        x = row + min_rc
        y = col - min_rc
        r = list()
        index = None
        while x >= 0 and y < self.board_cols:
            r.append(self.board[x,y])
            if x == row and y == col:
                index = len(r) - 1
            x -= 1
            y += 1
        return numpy.array(r), index

    def find_new_win(self, row, col):
        self.find_win_segment(self.board[:,col], row)
        self.find_win_segment(self.board[row,:], col)
        self.find_win_segment(*self.diagonal1(row, col))
        self.find_win_segment(*self.diagonal2(row, col))
        print(self.scores)

    def draw_sign(self, row, col):
        self.board[row][col]['player'] = self.current_player
        x, y = self.get_rect(row, col).topleft
        x += self.margin
        y += self.margin
        img = self.x_image if self.current_player == self.x_player else self.o_image
        self.screen.blit(img, (x, y))
        if self.current_player == self.x_player:
            self.current_player = self.o_player
        else:
            self.current_player = self.x_player

    def user_click(self):
        x, y = pg.mouse.get_pos()
        for col in range(self.board_cols):
            for row in range(self.board_rows):
                if self.get_rect(row, col).collidepoint(x, y):
                    if self.board[row][col]['player'] == self.unknown_player:
                        self.draw_sign(row, col)
                        self.find_new_win(row, col)
                        pg.display.update()
                    break

    def reset_game(self):
        time.sleep(2)
        self.draw_game_init()

    def quit(self):
        pg.quit()
        exit()

    def main(self):
        self.draw_game_init()
        fps = 30
        CLOCK = pg.time.Clock()
        event: pg.Event
        while True:
            for event in pg.event.get():
                if event.type == QUIT:
                    self.quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.quit()
                    elif event.key == pg.K_n:
                        self.draw_game_init()
                elif event.type == pg.MOUSEBUTTONUP:
                    self.user_click()
            pg.display.update()
            CLOCK.tick(fps)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", dest='rows', default=3, type=int)
    parser.add_argument("--cols", dest='cols', default=3, type=int)
    parser.add_argument("--win-len", dest='win_len', default=3, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    TicTacToe(rows=args.rows, cols=args.cols, win_len=args.win_len).main()
