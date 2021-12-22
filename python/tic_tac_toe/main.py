# importing the required libraries
import pygame as pg
import time
from pygame.locals import *
import numpy
from collections import defaultdict

XO = 'x'
WHITE = (255, 255, 255)
RED = (255, 0, 0)
LINE_COLOR = (0, 0, 0)
CELL_LINE_WIDTH = 2


class TicTacToe:
    o_player = 1
    x_player = 2
    
    def __init__(self):
        self.winner = None
        self.window_width = 800
        self.window_height = 800
        self.board_cols = 3
        self.board_rows = 3
        self.win_length = 3
        self.board = None
        self.current_player = None
        self.scores = defaultdict(int)
        self.margin = 20
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
        #self.board = [[None] * self.board_cols] * self.board_rows
        self.board = numpy.zeros((self.board_rows, self.board_cols))
        self.scores.clear()
        self.current_player = self.x_player
        self.screen.fill(WHITE)
        for col in range(self.board_cols):
            x = (col + 1) * self.cell_width()
            pg.draw.line(self.screen, LINE_COLOR, (x, 0), (x, self.window_height), CELL_LINE_WIDTH)

        for row in range(self.board_rows):
            y = (row + 1) * self.cell_height()
            pg.draw.line(self.screen, LINE_COLOR, (0, y), (self.window_width, y), CELL_LINE_WIDTH)


    def draw_win_line(self, row1, col1, row2, col2):
        x1, y1 = self.get_center_point(row1, col1)
        x2, y2 = self.get_center_point(row2, col2)
        pg.draw.line(self.screen, RED, (x1, y1), (x2, y2), 7)

    def search_win_lines(self, board):
        def check_vertic_win(row, col, who):
            section = board[row: row + self.win_length, col]
            return (section == who).sum() == self.win_length

        rows_count, cols_count =  board.shape
        for col in range(cols_count):
            row = 0
            while row < rows_count:
                found = False
                for player in [self.x_player, self.o_player]:
                    if check_vertic_win(row, col, player):
                        yield row, col, player
                        found = True
                if found:
                    row += self.win_length - 1
                else:
                    row += 1

    def calc_scores(self):
        self.scores.clear()
        for row, col, player in self.search_win_lines(self.board):
            self.scores[player] += 1
            self.draw_win_line(row, col, row + self.win_length, col)
        transpose_board = numpy.transpose(self.board)
        for col,row, player in self.search_win_lines(transpose_board):
            self.scores[player] += 1
            self.draw_win_line(row, col, row, col+self.win_length)
        print(self.scores)

    def draw_sign(self, row, col):
        self.board[row][col] = self.current_player
        x,y = self.get_rect(row, col).topleft
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
                    self.draw_sign(row, col)
                    self.calc_scores()
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
                elif event.type == pg.MOUSEBUTTONUP:
                    self.user_click()
            pg.display.update()
            CLOCK.tick(fps)


if __name__ == "__main__":
    TicTacToe().main()
