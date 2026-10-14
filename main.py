import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()

# Setup Screen for Mobile
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w if info.current_w > 0 else 720
SCREEN_HEIGHT = info.current_h if info.current_h > 0 else 1280
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eldritch Countdown Survival")

clock = pygame.time.Clock()
font_small = pygame.font.SysFont("sans-serif", int(SCREEN_HEIGHT * 0.022))
font_large = pygame.font.SysFont("sans-serif", int(SCREEN_HEIGHT * 0.035))

# --- GAME CLASSES ---

class GlitchOrb:
    def __init__(self):
        self.x = random.uniform(SCREEN_WIDTH * 0.1, SCREEN_WIDTH * 0.9)
        self.y = random.uniform(SCREEN_HEIGHT * 0.1, SCREEN_HEIGHT * 0.8)
        self.base_radius = random.uniform(12, 20)
        self.radius = self.base_radius
        self.max_radius = self.base_radius * 1.8
        self.growth_rate = random.uniform(4.0, 8.0)
        self.color = (random.randint(80, 180), random.randint(100, 220), random.randint(130, 240))
        self.sides = random.randint(3, 8)
        self.value = random.randint(5, 15)

    def update(self, dt):
        if self.radius < self.max_radius:
            self.radius += dt * self.growth_rate

    def draw(self, surface, phase_time):
        pts = []
        for s in range(self.sides):
            angle = (s * 2 * math.pi / self.sides) + phase_time * 0.3
            px = self.x + math.cos(angle) * self.radius
            py = self.y + math.sin(angle) * self.radius
            pts.append((px, py))
        if len(pts) > 2:
            pygame.draw.polygon(surface, self.color, pts, 3)

class JudgmentEye:
    def __init__(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'left':
            self.x, self.y = -40, random.uniform(0, SCREEN_HEIGHT)
        elif side == 'right':
            self.x, self.y = SCREEN_WIDTH + 40, random.uniform(0, SCREEN_HEIGHT)
        elif side == 'top':
            self.x, self.y = random.uniform(0, SCREEN_WIDTH), -40
        else:
            self.x, self.y = random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + 40

        self.speed = random.uniform(1.3, 2.6)
        self.size = SCREEN_HEIGHT * 0.065
        self.pupil_offset = [0, 0]

    def update(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed
        self.pupil_offset = [(dx / dist) * (self.size * 0.2), (dy / dist) * (self.size * 0.2)]

    def draw(self, surface):
        rect = pygame.Rect(self.x - self.size/2, self.y - self.size*0.3, self.size, self.size*0.6)
        pygame.draw.ellipse(surface, (230, 230, 240), rect)
        px = self.x + self.pupil_offset[0]
        py = self.y + self.pupil_offset[1]
        pupil_rect = pygame.Rect(px - self.size*0.18, py - self.size*0.18, self.size*0.36, self.size*0.36)
        pygame.draw.ellipse(surface, (200, 30, 30), pupil_rect)
        pygame.draw.rect(surface, (0, 0, 0), (px - 2, py - self.size*0.12, 4, self.size*0.24))

class TentacleShot:
    def __init__(self, start_pos, target_pos, max_reach):
        self.start = list(start_pos)
        self.current_tip = list(start_pos)
        self.max_reach = max_reach
        self.progress = 0.0
        self.speed = 4.0
        self.finished = False

        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        self.dir = [dx / dist, dy / dist]

    def update(self, dt):
        self.progress += dt * self.speed
        if self.progress >= 1.0:
            self.finished = True
            return

        reach_pct = math.sin(self.progress * math.pi)
        reach_dist = self.max_reach * reach_pct
        self.current_tip[0] = self.start[0] + self.dir[0] * reach_dist
        self.current_tip[1] = self.start[1] + self.dir[1] * reach_dist

    def draw(self, surface, phase_time):
        t_points = [self.start]
        segments = 5
        for seg in range(1, segments + 1):
            pct = seg / segments
            sx = self.start[0] + (self.current_tip[0] - self.start[0]) * pct
            sy = self.start[1] + (self.current_tip[1] - self.start[1]) * pct
            wigg = math.sin(phase_time * 5 + seg) * (8 * (1 - pct))
            t_points.append((sx + wigg, sy + wigg))
        if len(t_points) > 1:
            pygame.draw.lines(surface, (50, 230, 130), False, t_points, 5)

class AcidSpitProjectile:
    def __init__(self, start_pos, target_pos):
        self.x, self.y = start_pos[0], start_pos[1]
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        speed = SCREEN_HEIGHT * 0.6
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed
        self.radius = 8
        self.finished = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < -50 or self.x > SCREEN_WIDTH + 50 or self.y < -50 or self.y > SCREEN_HEIGHT + 50:
            self.finished = True

    def draw(self, surface):
        pygame.draw.circle(surface, (80, 240, 50), (int(self.x), int(self.y)), self.radius)

# --- MAIN GAME STATE ---

class Game:
    def __init__(self):
        self.dna_bank = 0
        self.skills = {
            "lash": {"name": "Tentacle Lash", "lvl": 1, "base_cost": 40, "desc": "Shoots fast tentacles"},
            "armor": {"name": "Membrane Armor", "lvl": 1, "base_cost": 30, "desc": "Increases max HP"},
            "acid": {"name": "Acid Spit", "lvl": 0, "base_cost": 60, "desc": "Auto-fires venom at eyes"},
            "magnet": {"name": "DNA Magnet", "lvl": 0, "base_cost": 50, "desc": "Attracts nearby shapes"},
            "reach": {"name": "Strike Reach", "lvl": 1, "base_cost": 35, "desc": "Extends tentacle range"},
            "shatter": {"name": "Shatter Burst", "lvl": 0, "base_cost": 70, "desc": "Bonus DNA on kills"}
        }

        self.in_skill_tree = False
        self.round_won = False
        self.bg_scroll_offset = 0
        self.reset_run()

    def reset_run(self):
        self.player_pos = [SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.5]
        self.target_pos = list(self.player_pos)
        self.blob_radius = SCREEN_HEIGHT * 0.04

        self.max_health = 2 + self.skills["armor"]["lvl"]
        self.health = self.max_health
        self.max_active_tentacles = self.skills["lash"]["lvl"]
        self.tentacle_reach = SCREEN_HEIGHT * (0.16 + self.skills["reach"]["lvl"] * 0.04)
        self.magnet_range = self.skills["magnet"]["lvl"] * (SCREEN_HEIGHT * 0.08)

        self.run_dna_collected = 0
        self.phase_time = 0
        
        # COUNTDOWN TIMER (60 Seconds to Survive)
        self.time_remaining = 60.0
        
        self.tentacle_cooldown = 0
        self.acid_cooldown = 0

        self.orbs = [GlitchOrb() for _ in range(7)]
        self.eyes = []
        self.active_shots = []
        self.active_acid = []
        self.eye_spawn_timer = 0
        self.in_skill_tree = False
        self.round_won = False

    def open_skill_tree(self, victory=False):
        self.in_skill_tree = True
        self.round_won = victory
        if victory:
            self.dna_bank += 150  # Big Victory Bonus DNA
        else:
            time_survived = 60.0 - max(0.0, self.time_remaining)
            self.dna_bank += int(time_survived)  # Partial survival DNA

    def buy_skill(self, key):
        sk = self.skills[key]
        cost = (sk["lvl"] + 1) * sk["base_cost"]
        if self.dna_bank >= cost:
            self.dna_bank -= cost
            sk["lvl"] += 1

    def update(self, dt):
        if self.in_skill_tree:
            return

        # COUNTDOWN TIMER LOGIC
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0.0
            self.open_skill_tree(victory=True)
            return

        self.phase_time += dt * 2.5
        self.bg_scroll_offset = (self.bg_scroll_offset + dt * 25) % 80

        # Player Movement
        dx = self.target_pos[0] - self.player_pos[0]
        dy = self.target_pos[1] - self.player_pos[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 4:
            speed = min(dist * 0.1, SCREEN_HEIGHT * 0.012)
            self.player_pos[0] += (dx / dist) * speed
            self.player_pos[1] += (dy / dist) * speed

        px, py = self.player_pos

        # Orbs logic
        for orb in self.orbs[:]:
            orb.update(dt)
            odx = px - orb.x
            ody = py - orb.y
            odist = math.sqrt(odx * odx + ody * ody)

            if self.magnet_range > 0 and odist < self.blob_radius + self.magnet_range:
                pull_speed = (1.0 - (odist / (self.blob_radius + self.magnet_range))) * 120 * dt
                orb.x += (odx / odist) * pull_speed
                orb.y += (ody / odist) * pull_speed

            if odist < self.blob_radius + orb.radius:
                self.orbs.remove(orb)
                self.dna_bank += orb.value
                self.run_dna_collected += orb.value
                self.blob_radius = min(SCREEN_HEIGHT * 0.08, self.blob_radius + 0.6)
                self.orbs.append(GlitchOrb())

        # Spawn Eyes
        self.eye_spawn_timer += dt
        if self.eye_spawn_timer > max(0.8, 3.0 - (self.run_dna_collected * 0.01)):
            self.eye_spawn_timer = 0
            self.eyes.append(JudgmentEye())

        # Acid Spit Skill
        if self.skills["acid"]["lvl"] > 0:
            self.acid_cooldown += dt
            acid_rate = max(0.5, 2.2 - (self.skills["acid"]["lvl"] * 0.3))
            if self.acid_cooldown >= acid_rate and self.eyes:
                target_eye = random.choice(self.eyes)
                self.active_acid.append(AcidSpitProjectile(self.player_pos, (target_eye.x, target_eye.y)))
                self.acid_cooldown = 0

        for acid in self.active_acid[:]:
            acid.update(dt)
            for eye in self.eyes[:]:
                adx = acid.x - eye.x
                ady = acid.y - eye.y
                if math.sqrt(adx * adx + ady * ady) < eye.size * 0.5:
                    self.eyes.remove(eye)
                    reward = 10 + (self.skills["shatter"]["lvl"] * 5)
                    self.dna_bank += reward
                    self.run_dna_collected += reward
                    acid.finished = True
                    break
            if acid.finished:
                self.active_acid.remove(acid)

        # Tentacle Lash Skill
        if self.skills["lash"]["lvl"] > 0:
            self.tentacle_cooldown += dt
            if self.tentacle_cooldown >= 0.35 and len(self.active_shots) < self.max_active_tentacles:
                closest_eye = None
                min_e_dist = self.tentacle_reach

                for eye in self.eyes:
                    edx = eye.x - px
                    edy = eye.y - py
                    edist = math.sqrt(edx * edx + edy * edy)
                    if edist < min_e_dist:
                        min_e_dist = edist
                        closest_eye = eye

                if closest_eye:
                    self.active_shots.append(TentacleShot(self.player_pos, (closest_eye.x, closest_eye.y), self.tentacle_reach))
                    self.tentacle_cooldown = 0

        for shot in self.active_shots[:]:
            shot.start = list(self.player_pos)
            shot.update(dt)

            for eye in self.eyes[:]:
                tdx = shot.current_tip[0] - eye.x
                tdy = shot.current_tip[1] - eye.y
                if math.sqrt(tdx * tdx + tdy * tdy) < eye.size * 0.6:
                    self.eyes.remove(eye)
                    reward = 10 + (self.skills["shatter"]["lvl"] * 5)
                    self.dna_bank += reward
                    self.run_dna_collected += reward
                    shot.finished = True
                    break

            if shot.finished:
                self.active_shots.remove(shot)

        # Enemies collision & update
        for eye in self.eyes[:]:
            eye.update(px, py)
            edx = px - eye.x
            edy = py - eye.y
            edist = math.sqrt(edx * edx + edy * edy)

            if edist < (self.blob_radius * 0.85 + eye.size * 0.25):
                self.eyes.remove(eye)
                self.health -= 1
                if self.health <= 0:
                    self.open_skill_tree(victory=False)

    def draw(self, surface):
        surface.fill((20, 22, 32))

        if self.in_skill_tree:
            self.draw_skill_tree(surface)
            return

        # Background Grid
        for i in range(-80, int(SCREEN_WIDTH) + 80, 80):
            x_pos = i + self.bg_scroll_offset
            pygame.draw.line(surface, (35, 45, 65), (x_pos, 0), (x_pos, SCREEN_HEIGHT), 1)
        for j in range(-80, int(SCREEN_HEIGHT) + 80, 80):
            y_pos = j + self.bg_scroll_offset
            pygame.draw.line(surface, (35, 45, 65), (0, y_pos), (SCREEN_WIDTH, y_pos), 1)

        # Orbs
        for orb in self.orbs:
            orb.draw(surface, self.phase_time)

        # Acid Shots
        for acid in self.active_acid:
            acid.draw(surface)

        # Tentacles
        for shot in self.active_shots:
            shot.draw(surface, self.phase_time)

        # Main Blob Character
        px, py = self.player_pos
        blob_pts = []
        num_vertices = 18
        for i in range(num_vertices):
            angle = i * (2 * math.pi / num_vertices)
            wobble = math.sin(self.phase_time * 2 + i) * (self.blob_radius * 0.18)
            r = self.blob_radius + wobble
            vx = px + math.cos(angle) * r
            vy = py + math.sin(angle) * r
            blob_pts.append((vx, vy))
        if len(blob_pts) > 2:
            pygame.draw.polygon(surface, (40, 190, 150), blob_pts, 4)

        # Spores inside Blob
        for n in range(min(12 + self.run_dna_collected // 10, 35)):
            n_angle = n * 0.8 + self.phase_time * 0.5
            n_dist = (n * 3) % (self.blob_radius * 0.65)
            nx = px + math.cos(n_angle) * n_dist
            ny = py + math.sin(n_angle) * n_dist
            pygame.draw.circle(surface, (230, 80, 130), (int(nx), int(ny)), 4)

        # Eyes Enemies
        for eye in self.eyes:
            eye.draw(surface)

        # Countdown Timer HUD Top Text
        mins = int(self.time_remaining // 60)
        secs = int(self.time_remaining % 60)
        ms = int((self.time_remaining % 1) * 10)
        hud_txt1 = font_small.render(f"SURVIVE TIME: {mins:02d}:{secs:02d}.{ms}  |  DNA: {self.dna_bank}", True, (240, 240, 100))
        hud_txt2 = font_small.render(f"MEMBRANE HP: {self.health}/{self.max_health}", True, (250, 100, 100))
        surface.blit(hud_txt1, (20, 30))
        surface.blit(hud_txt2, (20, 65))

    def draw_skill_tree(self, surface):
        surface.fill((15, 15, 22))

        header_text = "=== ROUND CLEARED! VICTORY! ===" if self.round_won else "=== MEMBRANE DISSOLVED ==="
        header_color = (100, 240, 150) if self.round_won else (240, 100, 100)

        title = font_large.render(header_text, True, header_color)
        sub = font_small.render(f"TOTAL DNA BANK: {self.dna_bank}", True, (100, 240, 150))
        surface.blit(title, (SCREEN_WIDTH * 0.08, SCREEN_HEIGHT * 0.05))
        surface.blit(sub, (SCREEN_WIDTH * 0.08, SCREEN_HEIGHT * 0.10))

        y_offset = 0.16
        keys = ["lash", "armor", "acid", "magnet", "reach", "shatter"]
        self.btn_rects = {}

        for key in keys:
            sk = self.skills[key]
            cost = (sk["lvl"] + 1) * sk["base_cost"]
            btn_rect = pygame.Rect(SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * y_offset, SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.08)
            self.btn_rects[key] = btn_rect

            color = (50, 80, 120) if self.dna_bank >= cost else (40, 45, 55)
            pygame.draw.rect(surface, color, btn_rect, border_radius=8)
            pygame.draw.rect(surface, (100, 150, 200), btn_rect, width=2, border_radius=8)

            txt1 = font_small.render(f"{sk['name']} (Lvl {sk['lvl']}) - Cost: {cost} DNA", True, (255, 255, 255))
            txt2 = font_small.render(f"[{sk['desc']}]", True, (180, 180, 180))
            surface.blit(txt1, (btn_rect.x + 15, btn_rect.y + 10))
            surface.blit(txt2, (btn_rect.x + 15, btn_rect.y + 35))

            y_offset += 0.10

        start_rect = pygame.Rect(SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.82, SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.09)
        self.btn_rects["start"] = start_rect
        pygame.draw.rect(surface, (40, 180, 90), start_rect, border_radius=10)
        start_txt = font_large.render("START NEXT ROUND", True, (255, 255, 255))
        surface.blit(start_txt, (start_rect.x + (start_rect.width - start_txt.get_width()) // 2, start_rect.y + 20))

    def handle_touch(self, pos):
        if self.in_skill_tree:
            for key, rect in self.btn_rects.items():
                if rect.collidepoint(pos):
                    if key == "start":
                        self.reset_run()
                    else:
                        self.buy_skill(key)
        else:
            self.target_pos = list(pos)

# --- RUN LOOP ---

def main():
    game = Game()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_touch(event.pos)
            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                if not game.in_skill_tree:
                    game.target_pos = list(event.pos)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()