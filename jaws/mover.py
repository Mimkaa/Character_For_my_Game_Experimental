import pygame as pg
vec = pg.Vector2
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import math
from settings import *
from functions import *


class Mover:
    def __init__(self, pos, rad, jaw):
        self.vel = vec(0,0)
        self.pos = vec(pos)
        self.moving_pos = vec(pos)
        self.rad = rad
        self.angle_move_left = 5.5
        self.angle_move_right = 4
        self.length = 1


        self.move_back_back = False
        self.back_circles = 0

        self.move_back_forward = True
        self.move_forward_forward = False
        self.forward_circles = 0

        self.finished = True
        self.prev_pos = vec(0,0)
        self.jaw = jaw


    def reset(self, character):
        if self.finished:
            if character.facing_vec == (-1, 0):
                self.reset_left()
            if character.facing_vec == (1, 0):
                self.reset_right()
            if character.facing_vec == (0, 1):
                self.reset_forward()
            if character.facing_vec == (0, -1):
                self.reset_back()

    def reset_left(self):

        self.angle_move_left = 5.5
        self.length = 1
        self.finished = False

    def reset_right(self):

        self.angle_move_right = 4
        self.length = 1
        self.finished = False

    def reset_back(self):

        self.length = 1
        self.move_back_back = False
        self.moving_pos = self.pos + vec(0, -JAW_EXTEND/2)
        self.finished = False
        self.back_circles = 0

    def reset_forward(self):
        self.length = 1
        self.move_back_forward = True
        self.move_forward_forward = False
        self.forward_circles = 0
        self.moving_pos = self.pos - vec(0, JAW_EXTEND/2)
        self.finished = False


    def move(self, pos):
        self.pos = vec(pos)

    def update_left(self, dt):

        if not self.finished:





            if self.angle_move_left  > math.pi*3/4:
                self.angle_move_left = self.angle_move_left  - 7 * dt
                self.length = translate(self.angle_move_left , 5.5, math.pi*3/4, 1, JAW_EXTEND)
                self.moving_pos = self.pos + vec(math.cos(self.angle_move_left),math.sin(self.angle_move_left)) * self.length

            else:
                self.jaw.constraint_right(self.jaw.operant_rect.right -5 )
                self.jaw.constraint(self.jaw.operant_rect.bottom - 5)
                # termination of the action
                check_list_points = [p[0].x * self.jaw.scale > self.jaw.operant_rect.left for p in self.jaw.points]
                check_movement = [math.isclose(p[0].x, p[1].x) and math.isclose(p[0].y, p[1].y) for p in self.jaw.points]
                trues = 0
                for t in check_list_points:
                    if t:
                        trues += 1

                if trues/len(check_list_points) > 0.85 or all(check_movement):
                    self.finished = True

                if trues/len(check_list_points) < 0.95:
                    self.moving_pos += vec(500 * dt, 0)



        else:
            self.moving_pos = self.pos + vec(0, JAW_EXTEND)





    def update_right(self, dt):

        if not self.finished:
            # backup the position
            self.prev_pos = self.moving_pos.copy()



            if self.angle_move_right < 7:
                self.angle_move_right = self.angle_move_right+ 7 * dt
                self.length = translate(self.angle_move_right, 4, 7, 1, JAW_EXTEND)

                self.moving_pos = self.pos + vec(math.cos(self.angle_move_right),math.sin(self.angle_move_right)) * self.length

            else:
                self.jaw.constraint_left(self.jaw.operant_rect.left + 5)
                self.jaw.constraint(self.jaw.operant_rect.bottom - 5)
                # termination of the action
                check_list_points = [p[0].x * self.jaw.scale < self.jaw.operant_rect.right for p in self.jaw.points]
                check_movement = [math.isclose(p[0].x, p[1].x) and math.isclose(p[0].y, p[1].y) for p in self.jaw.points]
                trues = 0
                for t in check_list_points:
                    if t:
                        trues += 1

                if trues/len(check_list_points) > 0.85 or all(check_movement):
                    self.finished = True

                if trues/len(check_list_points) < 0.95:
                    self.moving_pos -= vec(500 * dt, 0)


        else:
            self.moving_pos = self.pos + vec(0, JAW_EXTEND)


    def update_back(self, dt):

        if not self.finished:
            # backup the position
            self.prev_pos = self.moving_pos.copy()



            if dist_vec(self.pos, self.moving_pos) >= JAW_EXTEND :
                self.move_back_back = not self.move_back_back

            if not self.move_back_back:
                self.moving_pos += vec(0, - 500 * dt)
            else:
                self.moving_pos += vec(0, 500 * dt)
                # terminate the action
                check_list_points = [p[0].y * self.jaw.scale > self.jaw.operant_rect.top for p in self.jaw.points]
                trues = 0
                for t in check_list_points:
                    if t:
                        trues += 1

                if trues/len(check_list_points) > 0.95 :
                    self.finished = True

            # if math.isclose(self.prev_pos.x, self.moving_pos.x) and math.isclose(self.prev_pos.y, self.moving_pos.y):
            #     self.finished = True
            # if (self.finish_circle_pos.x - self.jaw.moving_p_center.x)**2 + (self.finish_circle_pos.y - self.jaw.moving_p_center.y)**2 < self.finish_circle_rad ** 2 :
            #     self.finished = True
        else:
            self.moving_pos = self.pos + vec(0, JAW_EXTEND/2)


    def update_forward(self, dt):

        if not self.finished:
            self.prev_pos = self.moving_pos.copy()

            #if self.moving_pos.y <= self.pos.y:
            if self.move_back_forward:
                self.moving_pos += vec(0, - 500 * dt)
                if self.pos.y - self.moving_pos.y > JAW_EXTEND/2 :
                    self.move_back_forward = False
                    self.move_forward_forward = True
                # terminate the action
                if self.forward_circles > 0 :
                    check_list_points = [p[0].y * self.jaw.scale < self.jaw.operant_rect.bottom for p in self.jaw.points]
                    trues = 0
                    for t in check_list_points:
                        if t:
                            trues += 1

                    if trues/len(check_list_points) > 0.95 :
                        self.finished = True

            if self.move_forward_forward:
                self.moving_pos += vec(0, 500 * dt)
                if self.moving_pos.y - self.pos.y > JAW_EXTEND :
                    self.move_back_forward = True
                    self.move_forward_forward = False
                    self.forward_circles += 1

        else:
            self.moving_pos = self.pos - vec(0, JAW_EXTEND/2)

    def pos_moving_pos_dist(self):
        return dist_vec(self.pos, self.moving_pos)


    def draw(self, surf):
        pg.draw.circle(surf, WHITE, self.pos, self.rad)
        pg.draw.line(surf, WHITE, self.pos, self.moving_pos)
        pg.draw.circle(surf, RED, self.moving_pos, self.rad)
        # finish circle
        pg.draw.circle(surf, RED, self.finish_circle_pos, self.finish_circle_rad, 1)