# main.py
import pygame
import random
import os
import sys

def resource_path(relative_path):
    """PyInstaller exe এর জন্য path ঠিক করা"""
    try:
        # PyInstaller exe এ path
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# ---------- SETTINGS ----------
WIDTH, HEIGHT = 480, 640
FPS = 60

PLAYER_WIDTH, PLAYER_HEIGHT = 60, 90
ENEMY_WIDTH, ENEMY_HEIGHT = 55, 80

PLAYER_SPEED = 5
ENEMY_MIN_SPEED = 3
ENEMY_MAX_SPEED = 6

SPAWN_EVENT = pygame.USEREVENT + 1
SPAWN_INTERVAL_MS = 900  # initial spawn every 900 ms

# ---------- INITIALIZE PYGAME ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TRAF Car Racing")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
large_font = pygame.font.SysFont(None, 64)

# ---------- LOAD ASSETS ----------
def try_load(path, scale=None):
    """Try to load an image, scale if needed. Return None if fails."""
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.smoothscale(img, scale)
        return img
    except Exception:
        return None

player_img = try_load(resource_path("assets/player_car.png"), (PLAYER_WIDTH, PLAYER_HEIGHT))
enemy_img  = try_load(resource_path("assets/enemy_car.png"), (ENEMY_WIDTH, ENEMY_HEIGHT))
bg_img     = try_load(resource_path("assets/background.png"), (WIDTH, HEIGHT))
# Fallback road image
try:
    road_img = pygame.image.load("road.png").convert()
    road_img = pygame.transform.scale(road_img, (WIDTH, HEIGHT))
except Exception:
    road_img = None

# ---------- GAME OBJECTS ----------
class Player:
    def __init__(self):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - self.height - 20
        self.speed = PLAYER_SPEED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, dx):
        self.x += dx * self.speed
        self.x = max(0, min(WIDTH - self.width, self.x))
        self.rect.topleft = (self.x, self.y)

    def draw(self, surf):
        if player_img:
            surf.blit(player_img, (self.x, self.y))
        else:
            pygame.draw.rect(surf, (30, 144, 255), self.rect)  # fallback blue rect

class Enemy:
    def __init__(self, x, speed):
        self.width = ENEMY_WIDTH
        self.height = ENEMY_HEIGHT
        self.x = x
        self.y = -self.height
        self.speed = speed
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt):
        self.y += self.speed * dt
        self.rect.topleft = (self.x, self.y)

    def draw(self, surf):
        if enemy_img:
            surf.blit(enemy_img, (self.x, self.y))
        else:
            pygame.draw.rect(surf, (220, 20, 60), self.rect)  # fallback red rect

# ---------- HELPERS ----------
def draw_text(surf, text, size, x, y, center=False):
    if size == "large":
        text_surf = large_font.render(text, True, (255, 255, 255))
    else:
        text_surf = font.render(text, True, (255, 255, 255))
    rect = text_surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(text_surf, rect)

# ---------- MAIN GAME FUNCTION ----------
def main():
    pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)
    player = Player()
    enemies = []
    running = True
    game_over = False
    score = 0
    difficulty_timer = 0.0
    enemy_speed_boost = 0.1
    spawn_interval = SPAWN_INTERVAL_MS

    # background scrolling variables
    bg_y = 0
    bg_speed = 4  # road scroll speed

    while running:
        dt = clock.tick(FPS) / 16.0  # normalize movement

        # ---------- EVENT LOOP ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == SPAWN_EVENT and not game_over:
                lane_x = random.randint(0, WIDTH - ENEMY_WIDTH)
                speed = random.uniform(ENEMY_MIN_SPEED + enemy_speed_boost, ENEMY_MAX_SPEED + enemy_speed_boost)
                enemies.append(Enemy(lane_x, speed))

            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    return main()  # restart
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ---------- INPUT ----------
        keys = pygame.key.get_pressed()
        if not game_over:
            dx = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            player.move(dx)

        # ---------- UPDATE ENEMIES ----------
        if not game_over:
            for e in enemies:
                e.update(dt)

        # ---------- REMOVE OFF-SCREEN ENEMIES ----------
        remaining = []
        for e in enemies:
            if e.y > HEIGHT:
                score += 10
            else:
                remaining.append(e)
        enemies = remaining

        # ---------- COLLISION DETECTION ----------
        if not game_over:
            for e in enemies:
                if player.rect.colliderect(e.rect):
                    game_over = True
                    try:
                        crash = pygame.mixer.Sound(resource_path("assets/crash.wav"))
                        crash.play()
                    except Exception:
                        pass
                    break

        # ---------- DIFFICULTY RAMP-UP ----------
        if not game_over:
            difficulty_timer += clock.get_time() / 1000.0
            if difficulty_timer > 5.0:
                enemy_speed_boost += 0.6
                difficulty_timer = 0.0
                spawn_interval = max(300, int(spawn_interval * 0.92))
                pygame.time.set_timer(SPAWN_EVENT, spawn_interval)

        # ---------- DRAW ----------
        # background scrolling
        if bg_img:
            bg_y += bg_speed
            if bg_y >= HEIGHT:
                bg_y = 0
            screen.blit(bg_img, (0, bg_y - HEIGHT))
            screen.blit(bg_img, (0, bg_y))
        else:
            screen.fill((34, 139, 34))
            road_rect = pygame.Rect(40, 0, WIDTH - 80, HEIGHT)
            pygame.draw.rect(screen, (50, 50, 50), road_rect)
            # scrolling dashed line
            bg_y += bg_speed
            if bg_y >= 40:
                bg_y = 0
            for y in range(-40, HEIGHT, 40):
                pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - 5, y + bg_y, 10, 20))

        player.draw(screen)
        for e in enemies:
            e.draw(screen)

        # ---------- HUD ----------
        draw_text(screen, f"Score: {score}", "small", 10, 10)
        if game_over:
            draw_text(screen, "GAME OVER", "large", WIDTH // 2, HEIGHT // 2 - 30, center=True)
            draw_text(screen, "Press R to restart or ESC to quit", "small", WIDTH // 2, HEIGHT // 2 + 30, center=True)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# ---------- RUN ----------
if __name__ == "__main__":
    main()
