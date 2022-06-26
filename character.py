from objects import *
from functions import *
from jaws.jaw import Jaw

import json

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
            #self.target.vel *= 0

    def contract(self):
        self.segments = self.segments[:-1]

    def approximate_dir(self):
        dirs = [vec(1, 0), vec(-1, 0), vec(0, -1), vec(0, 1)]
        curr_dir = (self.target.pos - self.base).normalize()
        dot_prods = [(dirs[i], dirs[i].dot(curr_dir)) for i in range(len(dirs))]
        dot_prods_sorted = sorted(dot_prods,key = lambda x: x[1])
        return dot_prods_sorted[-1][0]

    def length(self):
        return self.seg_length * len(self.segments)

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
        # pg.draw.line(screen, RED, self.segments[0].start, self.segments[0].start + self.start_end_vec)
        # pg.draw.circle(screen, RED, self.segments[0].start, 3)



class Click_Once:
    def __init__(self):
        self.all_clicked = {}

    def update(self):
        keys = pg.key.get_pressed()
        all_pressed_copy = self.all_clicked.copy()
        for (n, value) in all_pressed_copy.items():
            if not keys[value]:
                self.all_clicked.pop(n)

    def clicked(self, key):
        keys = pg.key.get_pressed()
        if keys[pg.key.key_code(key)] and key not in self.all_clicked.keys():
            self.all_clicked[key] = pg.key.key_code(key)
            return True
        return False



class Character:
    def __init__(self, body_name, pos, scale = 0.6):

        self.pos = vec(pos)

        with open(f"bodies/{body_name}", "r") as json_file:
            my_dict = json.load(json_file)

        self.particles = []
        self.springs = []
        self.grounded = []
        self.outline = []
        particles_tep = [vec(p)*my_dict['scale'] * scale for p in my_dict["points"]]
        for n, p in enumerate(my_dict["points"]):
            particle = Particle(vec(p)*my_dict['scale'] * scale + self.pos - self.get_particles_center(particles_tep) ,PARTICLE_RADIUS * scale)
            if n in my_dict["grounded"]:
                particle.locked = True
                self.grounded.append(particle)
            self.particles.append(particle)

        # create positions for boundaries
        for p in self.particles:
            if p not in self.grounded:
                p.bound_circle_pos_vec = p.pos - self.grounded[0].pos
                p.bound_circle_pos = self.grounded[0].pos + p.bound_circle_pos_vec

        for con in my_dict["connections"]:
            self.springs.append(Spring(self.particles[con[0]],self.particles[con[1]], 0.1, REST_LENGTH * scale))

        for con in my_dict["outline"]:
            self.outline.append([self.particles[con[0]], self.particles[con[1]]])


        self.create_body_rect()

        self.facing_vec = (0, 1)
        self.blinking_timer = Timer()
        self.stripe = Stripe((PURPULISH1, PURPULISH2, PURPULISH3), (50, 100), (100, 100), (WIDTH // 2, HEIGHT // 2))

        self.drawing_mode = 0
        self.click_once = Click_Once()

        # hand
        self.hand_pos = self.pos.copy()
        self.hand = None
        self.hand_seg_num = 10
        self.contract_hand = False

        # jaw
        self.jaw = Jaw(self.body_rect.midtop, "jaw1.txt", self)
        self.use_jaw = False
        # ratio_scale = self.body_rect.width / self.jaw.rect.width
        # print(ratio_scale)
        # self.jaw.scale = self.jaw.scale + self.jaw.scale * ratio_scale/4
        self.jaw.move_grounded_bottom(self.body_rect.midtop)

        # FOV
        self.fov = math.radians(50)
        self.fov_rad = 300
        self.current_dir_angle = 0


    def get_particles_center(self, particle_set):
        center = vec(0,0)
        for p in particle_set:
            center += p.copy()
        center/=len(particle_set)
        return center

    def create_body_rect(self):
        outline_1d = [i for j in self.outline for i in j]
        ys = [p.pos.y for p in outline_1d]
        xs = [p.pos.x for p in outline_1d]
        min_x = min(xs)
        man_x = max(xs)
        min_y = min(ys)
        man_y = max(ys)
        width = man_x - min_x
        height = man_y - min_y
        self.body_rect = pg.Rect(min_x, min_y, width, height)

    def get_keys(self, dt):
        if self.jaw.to_follow.finished:
            keys = pg.key.get_pressed()
            for n, p in enumerate(self.grounded):
                p.vel = vec(0, 0)
                if keys[pg.K_LEFT] or keys[pg.K_a]:
                    p.vel.x = -150 * dt * 2
                    self.facing_vec = (-1, 0)
                    self.current_dir_angle = math.atan2(p.vel.y, p.vel.x)
                if keys[pg.K_RIGHT] or keys[pg.K_d]:
                    p.vel.x = 150 * dt * 2
                    self.facing_vec = (1, 0)
                    self.current_dir_angle = math.atan2(p.vel.y, p.vel.x)
                if keys[pg.K_UP] or keys[pg.K_w]:
                    p.vel.y = -150 * dt * 2
                    self.facing_vec = (0, -1)
                    self.current_dir_angle = math.atan2(p.vel.y, p.vel.x)
                if keys[pg.K_DOWN] or keys[pg.K_s]:
                    p.vel.y = 150 * dt * 2
                    self.facing_vec = (0, 1)
                    self.current_dir_angle = math.atan2(p.vel.y, p.vel.x)

    def get_keys_one_click(self):
        if self.click_once.clicked("m"):
            self.drawing_mode = (self.drawing_mode + 1) % 2


    def hand_actions(self,targets):
        if self.click_once.clicked("e"):
            # find targets in the field of view
            new_targets_in_fov = []
            for target in targets:
                # checking the distance
                if dist_vec(self.pos, target.pos) < self.fov_rad:
                    # checking if it is in FOV
                    target_vec = (target.pos - self.pos).normalize()
                    direction = vec(math.cos(self.current_dir_angle), math.sin(self.current_dir_angle)).normalize()
                    dot_prod = direction.dot(target_vec)
                    angle = math.acos(dot_prod)
                    if angle < self.fov :
                        new_targets_in_fov.append(target)

            if not self.hand and new_targets_in_fov:
                target = find_the_closest_object(self.pos, new_targets_in_fov)

                dist_to_target = dist_vec(target.pos, self.pos)
                self.hand = Hand(self.hand_pos, dist_to_target / self.hand_seg_num, self.hand_seg_num)
                self.hand.set_target(target)
                self.hand.update(self.hand_pos)
            else:
                self.hand = None

        if self.click_once.clicked("space"):
            self.contract_hand = True
            if self.hand:
                    self.facing_vec = self.hand.approximate_dir()

    def update_hand(self):
        if self.hand:
            self.hand.update(self.hand_pos)
        if self.contract_hand and self.hand:
            if len(self.hand.segments) > 1:
                self.hand.contract()
                # trigger the jaw
                if  self.hand.length() < self.body_rect.width * 3 :
                    self.jaw.to_follow.reset(self)
            else:
                self.hand = None
                self.contract_hand = False



    def update(self, dt):
        # update portion of the game loop
        self.get_keys(dt)
        self.click_once.update()
        self.get_keys_one_click()

        # hand update
        self.hand_pos = self.pos.copy()
        self.update_hand()

        for p in self.particles:
            #p.apply_force(vec(0,0.01))
            p.update(dt)
            #p.collide_own_kind(self.particles)
            p.update_bound_circles_pos(self.grounded[0])

        for s in self.springs:
            s.update()

        self.create_body_rect()
        self.stripe.update(dt, (0, 0), (self.body_rect.width, self.body_rect.height))
        outline_1d_pos = [i.pos.copy() for j in self.outline for i in j]
        self.pos = self.get_particles_center(outline_1d_pos)

        # handle the jaw

        self.jaw.update()
        self.jaw.update_sticks()
        self.jaw.update_mover(dt, self)

    def draw_face(self, surf):
        # open eye
        left_eye_pos = vec(self.body_rect.topleft) + vec(self.body_rect.width//6, self.body_rect.height//6)
        left_eye = pg.Rect(left_eye_pos.x, left_eye_pos.y, self.body_rect.width//4 , self.body_rect.height//2)
        right_eye_pos = vec(self.body_rect.topright) + vec(-self.body_rect.width//6 - self.body_rect.width//4, self.body_rect.height//6)
        right_eye = pg.Rect(right_eye_pos.x, right_eye_pos.y, self.body_rect.width//4 , self.body_rect.height//2)

        # blinking eye
        left_eye_blink_pos = vec(self.body_rect.topleft) + vec(self.body_rect.width//6, self.body_rect.height//6 + self.body_rect.height//2 - 16)
        left_eye_blink = pg.Rect(left_eye_blink_pos.x, left_eye_blink_pos.y, self.body_rect.width//4 , left_eye.width//5)
        right_eye_blink_pos = vec(self.body_rect.topright) + vec(-self.body_rect.width//6 - self.body_rect.width//4, self.body_rect.height//6 + self.body_rect.height//2 - 16)
        right_eye_blink = pg.Rect(right_eye_blink_pos.x, right_eye_blink_pos.y, self.body_rect.width//4 , right_eye.width//5)

        if not self.blinking_timer.wait_randomize((1500, 5500), reset_time_range=(150, 300)):
            if self.facing_vec == vec(0, 1):
                pg.draw.rect(surf, WHITE, left_eye)
                pg.draw.rect(surf, BLACK, left_eye, left_eye.width//10)
                pg.draw.rect(surf, WHITE, right_eye)
                pg.draw.rect(surf, BLACK, right_eye, right_eye.width//10)
            elif self.facing_vec == vec(1, 0):
                pg.draw.rect(surf, WHITE, right_eye)
                pg.draw.rect(surf, BLACK, right_eye, right_eye.width//10)
            elif self.facing_vec == vec(-1, 0):
                pg.draw.rect(surf, WHITE, left_eye)
                pg.draw.rect(surf, BLACK, left_eye, left_eye.width//10)
        else:

            if self.facing_vec == vec(0, 1):
                pg.draw.rect(surf, BLACK, left_eye_blink)
                pg.draw.rect(surf, BLACK, right_eye_blink)
            elif self.facing_vec == vec(1, 0):
                pg.draw.rect(surf, BLACK, right_eye_blink)
            elif self.facing_vec == vec(-1, 0):
                pg.draw.rect(surf, BLACK, left_eye_blink)

    def draw_stripes(self, surf):
        sub_surf_rect = self.body_rect.copy()
        if sub_surf_rect.bottom > HEIGHT:
            sub_surf_rect.bottom = min(HEIGHT, self.body_rect.bottom)
        if sub_surf_rect.right > WIDTH:
            sub_surf_rect.right = min(WIDTH, self.body_rect.right)
        if sub_surf_rect.left < 0 :
            sub_surf_rect.left = max(0, self.body_rect.left)
        if sub_surf_rect.top < 0 :
            sub_surf_rect.top = max(0, self.body_rect.top)
        sub_surf = surf.subsurface(sub_surf_rect)
        sub_surf = sub_surf.copy()
        sub_surf.set_colorkey(BGCOLOR)


        # extraction of the shape
        m = pg.mask.from_surface(sub_surf)
        outline = m.outline() # get outline of mask
        if len(outline) > 1:
            sub_surf.fill((0, 0, 0)) # fill with color that will be colorkey
            sub_surf.set_colorkey((0, 0, 0))
            pg.draw.polygon(sub_surf, WHITE, outline)
            self.stripe.draw(sub_surf)
            surf.blit(sub_surf, sub_surf_rect.topleft)

    def draw_stripes_better(self, surf):
        # a better one
        sub_surf = pg.Surface((self.body_rect.width, self.body_rect.height))
        outline_1d = [i for j in self.outline for i in j]
        body_points = [p.pos - vec(self.body_rect.topleft) for p in outline_1d]
        pg.draw.polygon(sub_surf, WHITE, body_points)
        self.stripe.draw(sub_surf)
        sub_surf.set_colorkey(BLACK)
        surf.blit(sub_surf, self.body_rect.topleft)

    def draw(self, surf):
        # hand drawing
        if self.hand:
            self.hand.draw(surf)

        if self.drawing_mode == 0:
            outline_1d = [i for j in self.outline for i in j]
            body_points = [p.pos for p in outline_1d]

            # drawing orders
            facing_right_left_back = [(self.jaw.render_polygon, (surf, PURPULISH_BODY2)),(pg.draw.polygon,(surf, PURPULISH_BODY2, body_points)),
                            (self.draw_stripes_better, [surf]),(self.draw_face, [surf])]

            facing_forward = [(pg.draw.polygon,(surf, PURPULISH_BODY2, body_points)),
                            (self.draw_stripes_better, [surf]),(self.draw_face, [surf]),(self.jaw.render_polygon, (surf, PURPULISH_BODY2))]

            if self.facing_vec == (0, 1):
                conditions = [True, True, self.jaw.to_follow.finished, not self.jaw.to_follow.finished]
                facing_forward = [item for item, condition in zip(facing_forward, conditions) if condition]
                for func in facing_forward:
                    func[0](*func[1])
            else:
                conditions = [not self.jaw.to_follow.finished, True, True, True]
                facing_right_left_back = [item for item, condition in zip(facing_right_left_back, conditions) if condition]
                for func in facing_right_left_back:
                    func[0](*func[1])
            # draw jaw
            # if not self.jaw.to_follow.finished:
            #     self.jaw.render_polygon(surf, PURPULISH_BODY2)
            # pg.draw.polygon(surf, PURPULISH_BODY2, body_points)
            # self.draw_stripes_better(surf)
            # self.draw_face(surf)

        elif self.drawing_mode == 1:
            for p in self.particles:
                p.draw(surf)

            for s in self.springs:
                s.draw(surf)

            for p_set in self.outline:
                pg.draw.line(surf, YELLOW, p_set[0].pos, p_set[1].pos)


