import pygame as pg
import json
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from .mover import Mover
from functions import *
from settings import *
vec = pg.Vector2


class Jaw:
    def __init__(self,pos,rag_name, operant):
        with open(f"jaws/{rag_name}", "r") as json_file:
            rag = json.load(json_file)
        self.scale = rag['scale']
        self.pos=vec(pos)/self.scale
        self.origin_points=[vec(p)+self.pos for p in rag['points']]
        self.points=[[vec(p)+self.pos,vec(p)+self.pos] for p in rag['points']]
        self.sticks = []
        for stick in rag['connections']:
            self.add_stick(stick)
        self.grounded = rag['grounded']
        self.for_motion = rag['for_motion']
        self.center_origin=self.get_center(self.origin_points)
        grounded_origin = [self.origin_points[i] for i in self.grounded]
        self.bottom_center_origin = self.get_center(grounded_origin)
        self.create_rect()

        self.operant = operant
        self.operant_rect = operant.body_rect

        self.to_follow = Mover(self.rect.midbottom , 10, self)
        for_motion_p = [self.points[i][0] for i in self.for_motion]
        self.moving_p_center = self.get_center(for_motion_p) * self.scale



    def add_stick(self, points):
        self.sticks.append([points[0], points[1], dist_vec(self.points[points[0]][0], self.points[points[1]][0])])

    def move_grounded_center(self, offset):

        self.pos=vec(offset)/self.scale

        for i, point in enumerate(self.points):
            if i in self.grounded:
                point[0]=self.origin_points[i]+self.pos-self.center_origin
                #point[1]=point[0]

    def move_grounded_bottom(self, offset):
        self.pos=vec(offset)/self.scale

        for i, point in enumerate(self.points):
            if i in self.grounded:
                point[0]=self.origin_points[i]+self.pos-self.bottom_center_origin
                #point[1]=point[0]

    def constraint(self, bottom):
        for p in self.points:
            if p[0].y * self.scale > bottom:
                p[1]=p[0].copy()
                p[0].y = bottom/self.scale

    def constraint_top(self, top):
        for p in self.points:
            if p[0].y * self.scale < top:
                p[0].y = top/self.scale

    def constraint_right(self, right):
        for p in self.points:
            if p[0].x * self.scale > right:
                p[0].x = right/self.scale

    def constraint_left(self, left):
        for p in self.points:
            if p[0].x * self.scale < left:
                p[0].x = left/self.scale

    def put_moving(self, bottom):
        for n,p in enumerate(self.points):
            if n in self.for_motion:
                p[0].y = bottom/self.scale




    def incline_to(self, target, scale):
        dir_vec = target - (vec(self.rect.midbottom) + vec(0, 10))

        for p in self.for_motion:
            self.points[p][1] = self.points[p][0]
            if dir_vec.length() > 0:
                self.points[p][0] += dir_vec.normalize() * scale



    def update_mover(self, dt, character):
        self.operant_rect = self.operant.body_rect

        if character.facing_vec == vec(-1, 0):
            self.move_grounded_bottom(self.operant_rect.center)
            self.to_follow.move(self.operant_rect.midtop)
            if not self.to_follow.finished:
                self.incline_to(self.to_follow.moving_pos, 2)
            else:
                self.constraint_top(self.operant_rect.top + 5)
                self.constraint(self.operant_rect.bottom - 5)
                self.constraint_left(self.operant_rect.left + 5)
                self.constraint_right(self.operant_rect.right - 5)
            #self.constraint(character.rect.bottom - 5)
            self.to_follow.update_left(dt)

        if character.facing_vec == vec(1, 0):
            self.move_grounded_bottom(self.operant_rect.center)
            self.to_follow.move(self.operant_rect.midtop)
            if not self.to_follow.finished:
                self.incline_to(self.to_follow.moving_pos, 2)
            else:
                self.constraint_top(self.operant_rect.top + 5)
                self.constraint(self.operant_rect.bottom - 5)
                self.constraint_left(self.operant_rect.left + 5)
                self.constraint_right(self.operant_rect.right - 5)
            #self.constraint(character.rect.bottom - 5)
            self.to_follow.update_right(dt)

        if character.facing_vec == vec(0, -1):
            self.to_follow.update_back(dt)
            self.move_grounded_bottom(self.operant_rect.center)
            self.to_follow.move(self.operant_rect.midbottom)
            if not self.to_follow.finished:
                self.incline_to(self.to_follow.moving_pos, 2)
            else:
                self.constraint_top(self.operant_rect.top + 5)
                self.constraint(self.operant_rect.bottom - 5)
                self.constraint_left(self.operant_rect.left + 5)
                self.constraint_right(self.operant_rect.right - 5)
            #self.constraint(character.rect.bottom - 5)

        if character.facing_vec == vec(0, 1):
            self.to_follow.update_forward(dt)
            self.move_grounded_bottom(self.operant_rect.center)
            self.to_follow.move(self.operant_rect.midtop)
            if not self.to_follow.finished:
                self.incline_to(self.to_follow.moving_pos, 3)
            else:
                self.constraint_top(self.operant_rect.top + 5)
                self.constraint(self.operant_rect.bottom - 5)
                self.constraint_left(self.operant_rect.left + 5)
                self.constraint_right(self.operant_rect.right - 5)
            #self.constraint_top(character.rect.top)


    def apply_force(self, force):
        for p in self.points:
            p[0] += force

    def update(self):
        self.create_rect()
        for i, point in enumerate(self.points):
            if i not in self.grounded:
                grad=point[0]-point[1]
                point[1]=point[0].copy()
                point[0]+=grad
                point[0].y += 0.01
        for_motion_p = [self.points[i][0] for i in self.for_motion]
        self.moving_p_center = self.get_center(for_motion_p) * self.scale


    def update_sticks(self):
        for stick in self.sticks:
            dis = dist_vec(self.points[stick[0]][0], self.points[stick[1]][0])
            if dis > 0:
                dis_dif = stick[2] - dis
                mv_ratio = dis_dif / dis / 2
                grad=self.points[stick[1]][0]-self.points[stick[0]][0]

                if stick[0] not in self.grounded:
                    self.points[stick[0]][0]-=grad*mv_ratio*0.85

                if stick[1] not in self.grounded:
                    self.points[stick[1]][0]+=grad*mv_ratio*0.85



    def get_center(self, points):

        center=vec(0,0)

        for v in points:
            center+=v.copy()
        center/=len(points)

        return center

    def create_rect(self):
        min_x,max_x,min_y,max_y=self.get_min_max_coords()
        self.rect = pg.Rect(min_x, min_y, *self.get_surf_size())


    def get_min_max_coords(self):
        y_points = [p[0].y * self.scale for p in self.points]
        x_points = [p[0].x * self.scale for p in self.points]
        min_x = min(x_points)
        max_x = max(x_points)
        min_y = min(y_points)
        max_y = max(y_points)
        return min_x,max_x,min_y,max_y

    def get_surf_size(self):
        min_x,max_x,min_y,max_y=self.get_min_max_coords()
        width = int(max_x - min_x + 2)
        height = int(max_y - min_y + 2)
        return width,height



    def render_polygon(self, target_surf, color, offset=(0, 0)):
        min_x,max_x,min_y,max_y=self.get_min_max_coords()
        width,height=self.get_surf_size()
        surf = pg.Surface((width, height))
        self.render_sticks(surf, offset=(int(min_x), int(min_y)))
        surf.set_colorkey((0, 0, 0))
        m = pg.mask.from_surface(surf)
        outline = m.outline() # get outline of mask
        surf.fill((0, 0, 0)) # fill with color that will be colorkey
        surf.set_colorkey((0, 0, 0))
        pg.draw.polygon(surf, color, outline)
        target_surf.blit(surf, (min_x - offset[0], min_y - offset[1]))
        #self.to_follow.draw(target_surf)
        # pg.draw.circle(target_surf,RED,self.moving_p_center,10)
        # for p in self.points:
        #     pg.draw.circle(target_surf,RED,p[0]*self.scale,5)

    def render_sticks(self, surf, offset=(0, 0)):
        render_points = [p[0]*self.scale-vec(offset) for p in self.points]
        for stick in self.sticks:
            pg.draw.line(surf, (255, 255, 255), render_points[stick[0]], render_points[stick[1]], 1)
        pg.draw.rect(surf, RED, self.rect, 1)
        #self.to_follow.draw(surf)