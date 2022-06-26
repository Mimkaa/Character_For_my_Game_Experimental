import pygame as pg
import random
from settings import *

vec = pg.Vector2
import math


def dist_vec(vec1, vec2):
    return math.sqrt((vec1.x - vec2.x) ** 2 + (vec1.y - vec2.y) ** 2)


class Tentacle:
    def __init__(self, pos, seg_length, seg_num):
        self.segments = []
        self.seg_length = seg_length
        self.base = vec(pos)
        current = Segment(self.base, seg_length)
        self.segments.append(current)
        for i in range(1, seg_num):
            coord = self.segments[i - 1].end.copy()
            self.segments.append(Segment(coord, seg_length))

    def update(self, target):

        current = self.segments[-1]
        current.follow(target.pos)

        for i in range(len(self.segments) - 2, -1, -1):
            self.segments[i].follow(self.segments[i + 1].start)

        self.segments[0].set_start(self.base)

        for i in range(1, len(self.segments)):
            self.segments[i].set_start(self.segments[i - 1].end)

    def draw(self, screen):
        for pr in self.segments:
            pr.draw(screen)


class Target:
    def __init__(self, pos, rad):
        self.pos = vec(pos)
        self.rad = rad

    def draw(self, surface):
        pg.draw.circle(surface, GREEN, self.pos, self.rad)


class Hand(Tentacle):
    def __init__(self, pos, seg_length, seg_num):
        super().__init__(pos, seg_length, seg_num)
        self.target = None

    def set_target(self, target):
        self.target = target

    def pull_target(self):
        rope_extend = (len(self.segments)) * self.seg_length
        self.start_end_vec = self.target.pos - self.segments[0].start
        self.start_end_vec.scale_to_length(rope_extend)

        dist_particles = dist_vec(self.segments[0].start, self.target.pos)

        if dist_particles > rope_extend:
            self.target.pos = self.segments[0].start + self.start_end_vec

    def contract(self):
        self.segments = self.segments[:-1]

    def update(self, base):

        self.base = base
        # pull back
        if self.target:
            self.pull_target()

            current = self.segments[-1]
            current.follow(self.target.pos)

            for i in range(len(self.segments) - 2, -1, -1):
                self.segments[i].follow(self.segments[i + 1].start)

            self.segments[0].set_start(self.base)

            for i in range(1, len(self.segments)):
                self.segments[i].set_start(self.segments[i - 1].end)

    def draw(self, screen):
        for pr in self.segments:
            pr.draw(screen)


class Tentacle_Constraint(Tentacle):
    def __init__(self, pos, seg_length, seg_num):
        super().__init__(pos, seg_length, seg_num)

    def update(self, base, second_obj):
        self.base = base

        current = self.segments[-1]
        current.follow(second_obj.pos)

        for i in range(len(self.segments) - 2, -1, -1):
            self.segments[i].follow(self.segments[i + 1].start)

        self.segments[0].set_start(self.base)

        for i in range(1, len(self.segments)):
            self.segments[i].set_start(self.segments[i - 1].end)

        # pull back
        dist_particles = dist_vec(base, second_obj.pos)
        rope_extend = (len(self.segments)) * self.seg_length
        if dist_particles > rope_extend:
            second_obj.pos = self.segments[-1].end.copy()
            second_obj.vel *= 0


class Segment:
    def __init__(self, start, length):
        self.start = vec(start)
        self.length = length
        self.angle = 0
        self.calculate_end()

    def draw(self, surf):
        pg.draw.line(surf, WHITE, self.start, self.end, 1)

    def calculate_end(self):
        self.end = self.start + vec(math.cos(self.angle) * self.length, math.sin(self.angle) * self.length)

    def follow(self, point):
        point_vec = vec(point) - self.start

        angle = math.atan2(point_vec.y, point_vec.x)

        self.angle = angle
        scaled_point_vec = (self.length / point_vec.length()) * point_vec
        self.start = vec(point) - scaled_point_vec
        self.calculate_end()

    def set_start(self, pos):
        self.start = vec(pos)
        self.calculate_end()


class Polygon:
    def __init__(self, pos):
        self.points = []
        self.pos = vec(pos)
        self.angle = 0
        self.originals = []
        self.overlap = False

    def create_rect(self):
        ys = [p.y for p in self.points]
        xs = [p.x for p in self.points]
        min_x = min(xs)
        man_x = max(xs)
        min_y = min(ys)
        man_y = max(ys)
        width = man_x - min_x
        height = man_y - min_y
        self.rect = pg.Rect(min_x, min_y, width, height)

    def rotate(self, angle):
        self.angle += angle

    def move(self, dir):
        vel = vec(math.cos(self.angle), math.sin(self.angle)).normalize()
        vel.scale_to_length(dir)
        self.pos += vel

    def update(self):
        for n, point in enumerate(self.points):
            self.points[n].x = (self.originals[n].x * math.cos(self.angle) - self.originals[n].y * math.sin(
                self.angle)) + self.pos.x
            self.points[n].y = (self.originals[n].x * math.sin(self.angle) + self.originals[n].y * math.cos(
                self.angle)) + self.pos.y

    def draw(self, surf):
        for n in range(len(self.points)):
            pg.draw.line(surf, RED, self.points[n], self.points[(n + 1) % len(self.points)])
        # pg.draw.rect(surf,WHITE,self.rect,1)


class Particle:
    def __init__(self, pos, radius):
        self.vel = vec(0, 0)
        self.pos = vec(pos)
        self.acc = vec(0, 0)
        self.radius = radius
        self.mass = 1
        self.locked = False
        self.bound_rad = self.radius * 2
        self.bound_circle_pos_vec = vec(0, 0)
        self.bound_circle_pos = vec(0, 0)
        self.bound_rope = Tentacle_Constraint(self.bound_circle_pos, self.bound_rad / 10, 10)
        self.partner = None

    def update_bound_circles_pos(self, grounded):
        if not self.locked:
            self.bound_circle_pos = grounded.pos + self.bound_circle_pos_vec
            self.bound_rope.update(self.bound_circle_pos, self)

    def update(self, dt):
        if not self.locked:
            # self.vel *= 0.99
            self.vel += self.acc * dt * 50
        self.pos += self.vel * dt * 50
        self.acc *= 0

    def poly_collision(self, poly):
        if poly.rect.collidepoint(self.pos):
            dist_lines = {}
            for n, p in enumerate(poly.points):
                start = poly.points[n]
                end = poly.points[(n + 1) % len(poly.points)]
                center = start + (end - start) / 2
                dist_lines[(tuple(start), tuple(end))] = dist_vec(self.pos, center)
            min_dist = min(dist_lines.values())
            closest_line = list({k: v for k, v in dist_lines.items() if math.isclose(v, min_dist)}.keys())[0]
            closest_line_vectorized = [vec(i) for i in closest_line]

            # finding the closest point on the line to our point
            closest_line_start_end_vec = closest_line_vectorized[1] - closest_line_vectorized[0]
            closest_line_start_point_vec = (self.pos - closest_line_vectorized[0])
            length_proj = closest_line_start_point_vec.dot(closest_line_start_end_vec.normalize())
            proj_point = closest_line_start_end_vec.copy()
            proj_point.scale_to_length(length_proj)
            # self.line_point = closest_line_vectorized[0] + proj_point
            line_point = closest_line_vectorized[0] + proj_point

            # now raycasting
            self.intersections = []
            for n, p in enumerate(poly.points):
                start = poly.points[n]
                end = poly.points[(n + 1) % len(poly.points)]
                x1 = start.x
                y1 = start.y
                x2 = end.x
                y2 = end.y

                x3 = self.pos.x
                y3 = self.pos.y
                x4 = line_point.x
                y4 = line_point.y
                denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

                if denom != 0:
                    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
                    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

                    if t > 0 and t < 1 and u > 0:
                        pt = vec(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
                        self.intersections.append(pt)
            # print("inside" if len(self.intersections) % 2 != 0 else "outside")
            if len(self.intersections) % 2 != 0:
                self.pos = line_point
                # prev_vel_mag = self.point.vel.length()
                self.vel = vec(-closest_line_start_end_vec.y, closest_line_start_end_vec.x).normalize() * -1

    def apply_force(self, force):
        f = force.copy() / self.mass
        self.acc += f

    def draw(self, surface):
        pg.draw.circle(surface, WHITE, self.pos, self.radius)
        if not self.locked:
            pg.draw.circle(surface, RED, self.bound_circle_pos, self.bound_rad, 1)
        self.bound_rope.draw(surface)

    def dump(self, percent):
        self.vel *= percent



    def collide_own_kind(self, particles):
        for p in particles:
            if p != self:
                if (p.pos.x - self.pos.x) ** 2 + (p.pos.y - self.pos.y) ** 2 < (self.radius * 2) ** 2:
                    dir_vec = self.pos - p.pos
                    prev_vel = self.vel.copy()
                    if dir_vec.length() > 0 and not self.locked:
                        dir_vec.scale_to_length(self.radius * 2)
                        self.pos = p.pos + dir_vec
                        self.vel = dir_vec.normalize() * prev_vel.length()
                        # self.vel = -self.vel



class Spring:
    def __init__(self, start, end, k, rest_length):
        self.start = start
        self.end = end
        self.k = k
        self.rest_length = rest_length
        self.repel_r = self.end.radius
        self.start.partner = self.end
        self.end.partner = self.start

    def update(self):
        # dir_vec = self.end.pos - self.start.pos
        # dir_vec = dir_vec.normalize()
        #
        # vel_dif = self.end.vel - self.start.vel
        #
        # damp_force = dir_vec.dot(vel_dif)


        force = self.k * (dist_vec(self.start.pos, self.end.pos) - self.rest_length)
        force_total = force

        dir_vec_es = self.end.pos - self.start.pos
        dir_vec_es = dir_vec_es.normalize()

        dir_vec_se = self.start.pos - self.end.pos
        dir_vec_se = dir_vec_se.normalize()

        self.start.apply_force(force_total * dir_vec_es)
        self.end.apply_force(force_total * dir_vec_se)
        self.start.dump(0.99)
        self.end.dump(0.99)
        # force = dir_vec*(-1 * self.k * (dist_vec(self.start.pos,self.end.pos)-self.rest_length))

        # self.end.apply_force(force)
        # force *= -1
        # self.start.apply_force(force)
        # self.end.dump(0.99)
        # self.start.dump(0.99)

    def draw(self, surf):
        pg.draw.line(surf, WHITE, self.start.pos, self.end.pos)


class Counter:
    def __init__(self):
        self.current_time = 0
        self.current_time_set = False

    def count_time(self, milliseconds):
        now = pg.time.get_ticks()
        if not self.current_time_set:
            self.current_time = now
            self.current_time_set = True
        if now - self.current_time > milliseconds:
            self.current_time_set = False
            return True
        return False


class Timer:
    def __init__(self):
        self.count_down = Counter()
        self.count_reset = Counter()
        self.count_down_running = True
        self.count_reset_running = False
        self.random_countdown = 0
        self.random_reset = 0
        self.random_ranges_set = False

    def wait(self, milliseconds, reset_time=0):
        if self.count_down_running:
            if self.count_down.count_time(milliseconds):
                self.count_down_running = False
                self.count_reset_running = True
            return False

        if self.count_reset_running:
            if self.count_reset.count_time(reset_time):
                self.count_reset_running = False
            return True

        if not self.count_reset_running and not self.count_down_running:
            self.count_down_running = True
            self.count_reset_running = False
            return False

    def wait_randomize(self, count_down_range, reset_time_range=(0, 0)):
        if not self.random_ranges_set:
            self.random_countdown = random.randint(count_down_range[0], count_down_range[1])
            self.random_reset = random.randint(reset_time_range[0], reset_time_range[1])
            self.random_ranges_set = True

        if self.count_down_running:
            if self.count_down.count_time(self.random_countdown):
                self.count_down_running = False
                self.count_reset_running = True
            return False

        if self.count_reset_running:
            if self.count_reset.count_time(self.random_reset):
                self.count_reset_running = False
            return True

        if not self.count_reset_running and not self.count_down_running:
            self.count_down_running = True
            self.count_reset_running = False
            self.random_ranges_set = False
            return False

class Stripe:
    def __init__(self, colours, size_stripe, size_main, pos):
        self.image = pg.Surface(size_stripe, pg.SRCALPHA)
        self.size_stripe = size_stripe
        self.size_main = size_main
        self.colours = colours
        self.rect = self.image.get_rect()
        for i in range(len(self.colours)):
            pg.draw.polygon(self.image, self.colours[i],
                            ((self.rect.left + i * ((self.rect.width) / len(self.colours)), self.rect.top),
                             (self.rect.left + i * (self.rect.width) / len(self.colours) + (self.rect.width) / len(
                                 self.colours), self.rect.top),
                             (self.rect.left + i * (self.rect.width) / len(self.colours) + (self.rect.width) / len(
                                 self.colours), self.rect.bottom),
                             (self.rect.left + i * ((self.rect.width) / len(self.colours)), self.rect.bottom)
                             ))
        self.image_copy = self.image.copy()
        self.pos = vec(pos)
        self.action_surf = pg.Surface(size_main, pg.SRCALPHA)
        self.action_surf_copy = self.action_surf.copy()
        self.action_surf_rect = self.action_surf.get_rect()
        self.action_surf_rect.topleft = self.pos
        self.image_pos = (0, 0)

    def update(self, dt, pos, new_action_surf_size):
        self.pos = vec(pos)
        self.action_surf = pg.transform.scale(self.action_surf_copy, new_action_surf_size)
        self.action_surf_rect = self.action_surf.get_rect()
        self.action_surf_rect.topleft = self.pos

        self.image_pos += vec(100 * dt, 0)
        self.image = pg.transform.scale(self.image_copy,
                                        (self.action_surf.get_width() // 2, self.action_surf.get_height()))
        self.rect = self.image.get_rect()

        self.rect.topleft = self.image_pos
        if self.rect.left > self.action_surf_rect.width:
            self.image_pos = vec(-self.rect.width, 0)

    def draw(self, surf):
        self.action_surf.blit(self.image, self.image_pos)
        # pg.draw.rect(self.action_surf, RED, self.rect,1)
        self.action_surf.set_colorkey(BGCOLOR)
        surf.blit(self.action_surf, self.action_surf_rect, None, pg.BLEND_RGBA_MULT)
        #pg.draw.rect(surf, RED, self.action_surf_rect, 1)
