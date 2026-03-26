import pygame
import sys
import math
import random

# 1. 초기화 및 상수
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CUBE_SIZE = 40
ENEMY_SIZE = 35
ITEM_SIZE = 25 # 아이템 크기
MOVE_SPEED = 5
ENEMY_SPEED = 2
GRAVITY = 0.8
JUMP_FORCE = -16
MISSILE_SPEED = 12

# 색상
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255) # 아이템 색상
BACKGROUND_COLOR = (30, 30, 30)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("더블 샷 파워업 아이템")
font = pygame.font.SysFont("malgungothic", 20)
large_font = pygame.font.SysFont("malgungothic", 60)

# 2. 클래스 정의
class Missile:
    def __init__(self, x, y, direction, offset_y=0):
        # offset_y: 더블 샷일 때 위아래 간격을 주기 위한 변수
        self.rect = pygame.Rect(x, y + offset_y, 15, 8)
        self.direction = direction
        self.speed = MISSILE_SPEED

    def update(self):
        self.rect.x += self.speed * self.direction

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.hp = 100
        self.max_hp = 100
        self.y_vel = 0
        self.is_jumping = False

    def update(self, player_rect, platforms):
        if self.rect.x < player_rect.x: self.rect.x += ENEMY_SPEED
        elif self.rect.x > player_rect.x: self.rect.x -= ENEMY_SPEED
        
        self.y_vel += GRAVITY
        self.rect.y += self.y_vel

        if not self.is_jumping and player_rect.bottom < self.rect.top - 50:
            if random.randint(1, 60) == 1:
                self.y_vel = -14
                self.is_jumping = True

        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                if self.rect.bottom <= plat.top + self.y_vel:
                    self.rect.bottom = plat.top
                    self.y_vel = 0
                    self.is_jumping = False

    def draw(self, screen):
        pygame.draw.rect(screen, ORANGE, self.rect)
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, ENEMY_SIZE, 5))
        pygame.draw.rect(screen, GREEN, (self.rect.x, self.rect.y - 10, ENEMY_SIZE * hp_ratio, 5))

# 아이템 클래스 추가
class Item:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ITEM_SIZE, ITEM_SIZE)
    
    def draw(self, screen):
        # 반짝이는 효과를 위해 타이머 사용
        if (pygame.time.get_ticks() // 200) % 2 == 0:
            pygame.draw.rect(screen, MAGENTA, self.rect)
        else:
            pygame.draw.rect(screen, WHITE, self.rect, 2)

# 3. 초기화 함수
def reset_game():
    global cube_rect, y_vel, is_jumping, hp, score, game_over, enemies, missiles, player_dir, invincible_timer, items, has_double_shot
    cube_rect = pygame.Rect(100, SCREEN_HEIGHT - 100, CUBE_SIZE, CUBE_SIZE)
    y_vel = 0
    is_jumping = False
    hp = 100
    score = 0
    game_over = False
    player_dir = 1
    invincible_timer = 0
    missiles = []
    has_double_shot = False # 더블 샷 획득 여부
    
    enemies = [Enemy(random.randint(0, 700), 0) for _ in range(2)]
    
    # 아이템 스폰 (맵 중앙 즈음)
    items = [Item(400, 300)]

reset_game()

platforms = [
    pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40),
    pygame.Rect(200, 450, 200, 20),
    pygame.Rect(450, 300, 200, 20),
    pygame.Rect(150, 180, 200, 20)
]

# 4. 메인 루프
running = True
clock = pygame.time.Clock()

while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                reset_game()
            elif not game_over:
                if event.key == pygame.K_SPACE and not is_jumping:
                    y_vel = JUMP_FORCE
                    is_jumping = True
                if event.key == pygame.K_s:
                    # 미사일 발사 로직 수정
                    if has_double_shot:
                        # 더블 샷: 위아래로 약간 오프셋을 줘서 두 개 생성
                        missiles.append(Missile(cube_rect.centerx, cube_rect.centery, player_dir, -10))
                        missiles.append(Missile(cube_rect.centerx, cube_rect.centery, player_dir, 10))
                    else:
                        # 기본 샷: 중앙에서 한 개 생성
                        missiles.append(Missile(cube_rect.centerx, cube_rect.centery, player_dir))

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: 
            cube_rect.x -= MOVE_SPEED
            player_dir = -1
        if keys[pygame.K_RIGHT]: 
            cube_rect.x += MOVE_SPEED
            player_dir = 1

        if invincible_timer > 0: invincible_timer -= dt

        y_vel += GRAVITY
        cube_rect.y += y_vel

        # 플레이어 플랫폼 충돌
        for plat in platforms:
            if cube_rect.colliderect(plat) and y_vel > 0:
                if cube_rect.bottom <= plat.top + y_vel:
                    cube_rect.bottom = plat.top
                    y_vel = 0
                    is_jumping = False
        
        # 아이템 획득 체크
        for item in items[:]:
            if cube_rect.colliderect(item.rect):
                has_double_shot = True
                items.remove(item)
                score += 500 # 아이템 보너스 점수
                print("더블 샷 획득!")

        # 미사일 업데이트 및 적 충돌
        for m in missiles[:]:
            m.update()
            if m.rect.x < 0 or m.rect.x > SCREEN_WIDTH:
                missiles.remove(m)
                continue
            
            for enemy in enemies[:]:
                if m.rect.colliderect(enemy.rect):
                    enemy.hp -= 50
                    if m in missiles: missiles.remove(m)
                    if enemy.hp <= 0:
                        enemies.remove(enemy)
                        score += 100
                        enemies.append(Enemy(random.choice([0, SCREEN_WIDTH]), 0))
                    break

        # 적 업데이트 및 플레이어 충돌
        for enemy in enemies:
            enemy.update(cube_rect, platforms)
            if cube_rect.colliderect(enemy.rect) and invincible_timer <= 0:
                hp -= 20
                invincible_timer = 1000

        if hp <= 0: game_over = True

    # 5. 그리기
    screen.fill(BACKGROUND_COLOR)
    
    for plat in platforms: pygame.draw.rect(screen, GREEN, plat)
    for enemy in enemies: enemy.draw(screen)
    for item in items: item.draw(screen) # 아이템 그리기
    for m in missiles: pygame.draw.rect(screen, CYAN, m.rect)
    
    if invincible_timer <= 0 or (invincible_timer // 100) % 2 == 0:
        pygame.draw.rect(screen, RED, cube_rect)
    
    # UI
    pygame.draw.rect(screen, (50, 50, 50), (20, 20, 200, 20))
    pygame.draw.rect(screen, RED, (20, 20, max(0, hp * 2), 20))
    hp_text = font.render(f"HP: {hp}", True, WHITE)
    screen.blit(hp_text, (20, 15))
    
    score_text = font.render(f"SCORE: {score}", True, YELLOW)
    screen.blit(score_text, (SCREEN_WIDTH - 150, 20))

    # 파워업 상태 표시
    if has_double_shot:
        powerup_text = font.render("DOUBLE SHOT ACTIVE", True, MAGENTA)
        screen.blit(powerup_text, (20, 50))

    if game_over:
        msg = large_font.render("GAME OVER", True, WHITE)
        screen.blit(msg, (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 - 50))

    pygame.display.flip()

pygame.quit()
sys.exit()
