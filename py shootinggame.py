import pygame
import sys
import random
import math

# ==========================================
# 1. 게임 설정 및 초기화 (Constants & Init)
# ==========================================
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRAVITY = 0.8 

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)      
MAGENTA = (255, 0, 255)   
BG_COLOR = (30, 30, 30)   

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Awesome Action Game") # 창 제목 추가
font = pygame.font.SysFont("malgungothic", 20)        
large_font = pygame.font.SysFont("malgungothic", 60) 

# ==========================================
# 2. 베이스 클래스
# ==========================================
class Entity:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.y_vel = 0 

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# ==========================================
# 3. 플레이어 및 투사체 클래스
# ==========================================
class Player(Entity):
    def __init__(self):
        super().__init__(100, SCREEN_HEIGHT - 100, 40, 40, RED)
        self.hp = 100            
        self.max_hp = 100        
        self.score = 0           
        self.direction = 1       
        self.is_jumping = False  
        self.invincible_timer = 0
        
        self.has_double_shot = False 
        self.item_timer = 0          
        self.shield_timer = 0        

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= 5
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            self.rect.x += 5
            self.direction = 1

        # 화면 밖으로 나가지 못하게 방지
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

    def jump(self):
        if not self.is_jumping:
            self.y_vel = -16      
            self.is_jumping = True

    def shoot(self, missile_list):
        offsets = [-10, 10] if self.has_double_shot else [0]
        for off in offsets:
            missile_list.append(Missile(self.rect.centerx, self.rect.centery, self.direction, off))

    def update(self, platforms, dt):
        self.y_vel += GRAVITY
        self.rect.y += self.y_vel
        
        if self.invincible_timer > 0: 
            self.invincible_timer -= dt
            
        if self.has_double_shot:
            self.item_timer -= dt
            if self.item_timer <= 0:
                self.has_double_shot = False 
                self.item_timer = 0
                
        if self.shield_timer > 0:
            self.shield_timer -= dt

        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                if self.rect.bottom <= plat.top + self.y_vel:
                    self.rect.bottom = plat.top 
                    self.y_vel = 0              
                    self.is_jumping = False     

    def draw(self, surface):
        if self.invincible_timer <= 0 or (self.invincible_timer // 100) % 2 == 0:
            super().draw(surface)
            
        if self.shield_timer > 0:
            pygame.draw.rect(surface, CYAN, self.rect.inflate(10, 10), 3)    

class Missile(Entity):
    def __init__(self, x, y, direction, offset_y=0):
        super().__init__(x, y + offset_y, 15, 8, CYAN)
        self.direction = direction
        self.speed = 12

    def update(self):
        self.rect.x += self.speed * self.direction 

class EnemyBullet(Entity):
    def __init__(self, x, y, target_x, target_y):
        super().__init__(x, y, 10, 10, YELLOW)
        angle = math.atan2(target_y - y, target_x - x)
        self.vx = math.cos(angle) * 5 
        self.vy = math.sin(angle) * 5 

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

# ==========================================
# 4. 적 클래스 및 보스 클래스
# ==========================================
class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 35, 35, ORANGE)
        self.hp = 100
        self.max_hp = 100

    def update(self, player_rect, platforms):
        if self.rect.x < player_rect.x: self.rect.x += 2
        else: self.rect.x -= 2
        
        self.y_vel += GRAVITY
        self.rect.y += self.y_vel
        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.y_vel = 0

    def draw(self, surface):
        super().draw(surface)
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 10, self.rect.width, 5))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 10, self.rect.width * (self.hp/self.max_hp), 5))

class RangedEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = GREEN
        self.shoot_delay = 0

    def update(self, player_rect, platforms, enemy_bullets):
        dist = player_rect.x - self.rect.x
        if abs(dist) > 300: self.rect.x += 2 if dist > 0 else -2
        elif abs(dist) < 200: self.rect.x -= 2 if dist > 0 else -2

        self.y_vel += GRAVITY
        self.rect.y += self.y_vel
        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.y_vel = 0

        self.shoot_delay += 1
        if self.shoot_delay > 90:
            enemy_bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, 
                                            player_rect.centerx, player_rect.centery))
            self.shoot_delay = 0

class DashBoss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect.size = (70, 70)
        self.hp = 500
        self.max_hp = 500
        
        self.state = "IDLE" 
        self.timer = 0
        self.dash_dir = 1
        self.on_ground = False 

    def update(self, player_rect, platforms):
        self.timer += 1
        
        if self.state == "IDLE":
            self.color = ORANGE
            if self.timer > 90: 
                self.timer = 0
                if random.random() < 0.6: self.state = "READY"
                else: self.state = "JUMP_READY"
                    
        elif self.state == "READY":
            self.color = WHITE
            if self.timer > 30:
                self.state = "DASH"
                self.dash_dir = 1 if player_rect.x > self.rect.x else -1 
                self.timer = 0
                
        elif self.state == "DASH":
            self.color = RED
            self.rect.x += self.dash_dir * 12
            
            if self.rect.left <= 0:
                self.rect.left = 0
                self.dash_dir = 1  
            elif self.rect.right >= SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                self.dash_dir = -1 

            if self.timer > 50: 
                self.state = "IDLE"
                self.timer = 0

        elif self.state == "JUMP_READY":
            self.color = CYAN
            if self.timer > 30:
                self.state = "JUMP"
                self.y_vel = -22 
                self.dash_dir = 1 if player_rect.x > self.rect.x else -1
                self.timer = 0
                
        elif self.state == "JUMP":
            self.color = MAGENTA
            self.rect.x += self.dash_dir * 7 
            
            if self.rect.left <= 0:
                self.rect.left = 0
                self.dash_dir = 1
            elif self.rect.right >= SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                self.dash_dir = -1
                
            if self.timer > 10 and self.on_ground:
                self.state = "IDLE"
                self.timer = 0

        self.y_vel += GRAVITY
        self.rect.y += self.y_vel
        self.on_ground = False 
        
        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.y_vel = 0
                self.on_ground = True 

class LaserBoss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect.size = (80, 80)
        self.hp = 600
        self.max_hp = 600
        self.color = (100, 0, 100) 
        
        self.state = "MOVE"
        self.timer = 0
        self.laser_rect = pygame.Rect(0, 0, 0, 0)
        self.is_firing = False

    def update(self, player_rect, platforms, dt):
        self.timer += dt
        
        if self.state == "MOVE":
            target_x = player_rect.x
            if self.rect.x < target_x: self.rect.x += 2
            else: self.rect.x -= 2
            
            self.rect.y = 150 
            
            if self.timer > 3000: 
                self.state = "CHARGE"
                self.timer = 0
                
        elif self.state == "CHARGE":
            self.color = (200, 100, 255)
            if self.timer > 1500: 
                self.state = "FIRE"
                self.timer = 0
                self.is_firing = True
                self.laser_rect = pygame.Rect(self.rect.centerx - 40, self.rect.bottom, 80, SCREEN_HEIGHT)

        elif self.state == "FIRE":
            self.color = WHITE 
            if self.timer > 2000: 
                self.state = "MOVE"
                self.timer = 0
                self.is_firing = False

    def draw(self, surface):
        super().draw(surface)
        if self.state == "CHARGE":
            pygame.draw.rect(surface, RED, (self.rect.centerx - 2, self.rect.bottom, 4, SCREEN_HEIGHT), 1)
            
        if self.is_firing:
            pygame.draw.rect(surface, CYAN, self.laser_rect)
            pygame.draw.rect(surface, WHITE, self.laser_rect.inflate(-20, 0)) 

class Item(Entity):
    def __init__(self, x, y, item_type="double_shot"): 
        color_map = {
            "double_shot": MAGENTA,
            "heal": GREEN,
            "shield": CYAN
        }
        super().__init__(x, y, 25, 25, color_map.get(item_type, MAGENTA))
        self.type = item_type

    def draw(self, surface):
        if (pygame.time.get_ticks() // 200) % 2 == 0:
            super().draw(surface)
        else:
            pygame.draw.rect(surface, WHITE, self.rect, 2)

# ==========================================
# 5. 게임 매니저 (충돌, 쉐이크, 화면 그리기)
# ==========================================
class Game:
    def __init__(self):
        self.platforms = [
            pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40), 
            pygame.Rect(200, 450, 200, 20),
            pygame.Rect(450, 300, 200, 20),
            pygame.Rect(150, 180, 200, 20)
        ]
        
        # 스크린 쉐이크용 변수
        self.shake_timer = 0
        self.shake_intensity = 0
        
        self.reset() 

    def trigger_shake(self, duration=200, intensity=5):
        """화면 흔들림을 유발하는 함수"""
        self.shake_timer = duration
        self.shake_intensity = intensity

    def reset(self):
        self.player = Player()
        self.enemies = [Enemy(random.randint(0, 700), 0), RangedEnemy(700, 0)]
        
        # 보스 랜덤 스폰 로직 적용
        if random.random() > 0.5:
            self.boss = DashBoss(600, 400)
        else:
            self.boss = LaserBoss(400, 150)
            
        self.items = [Item(400, 300)]
        self.missiles = []
        self.enemy_bullets = []
        self.game_over = False
        
        self.item_spawn_timer = 0
        self.boss_respawn_timer = 0
        self.ui_message = ""
        self.ui_message_timer = 0
        self.shake_timer = 0 # 초기화 시 흔들림도 멈춤

    def process_collisions(self):
        # 1. 낙사
        if self.player.rect.top > SCREEN_HEIGHT:
            self.player.hp = 0  
            self.ui_message = "낭떠러지로 추락!"
            self.ui_message_timer = 3000

        # 2. 아이템
        for item in self.items[:]:
            if self.player.rect.colliderect(item.rect):
                if item.type == "double_shot": 
                    self.player.has_double_shot = True
                    self.player.item_timer = 8000
                elif item.type == "heal":
                    self.player.hp = min(self.player.max_hp, self.player.hp + 30) 
                elif item.type == "shield":
                    self.player.shield_timer = 5000
                
                self.player.score += 500
                self.items.remove(item)

        # 3. 아군 미사일 충돌
        for m in self.missiles[:]:
            for e in self.enemies[:]:
                if m.rect.colliderect(e.rect):
                    e.hp -= 40
                    if m in self.missiles: self.missiles.remove(m) 
                    
                    if e.hp <= 0: 
                        self.enemies.remove(e)
                        self.player.score += 100
                        new_enemy = RangedEnemy(random.choice([0, 750]), 0) if random.random() > 0.5 else Enemy(random.choice([0, 750]), 0)
                        self.enemies.append(new_enemy)
            
            if self.boss.hp > 0 and m.rect.colliderect(self.boss.rect):
                self.boss.hp -= 20
                if m in self.missiles: self.missiles.remove(m)
                if self.boss.hp <= 0:
                    self.player.score += 2000 
                    self.trigger_shake(500, 10) # 보스 처치 시 큰 진동

        # 4. 적 총알 피격
        for eb in self.enemy_bullets[:]:
            if self.player.rect.colliderect(eb.rect):
                if self.player.shield_timer <= 0: 
                    self.player.hp -= 10
                    self.trigger_shake(100, 3) # 약한 타격 진동
                self.enemy_bullets.remove(eb) 

        # 5. 몸통 박치기 피격
        check_list = self.enemies[:]
        if self.boss.hp > 0:
            check_list.append(self.boss)
            
        for e in check_list:
            if self.player.rect.colliderect(e.rect) and self.player.invincible_timer <= 0:
                if self.player.shield_timer <= 0:
                    self.player.hp -= 20
                    self.trigger_shake(200, 8) # 강한 박치기 진동
                self.player.invincible_timer = 1000 

        # 6. 레이저 보스 광역기 피격
        if hasattr(self.boss, 'is_firing') and self.boss.is_firing:
            if self.player.rect.colliderect(self.boss.laser_rect):
                if self.player.shield_timer <= 0 and self.player.invincible_timer <= 0:
                    self.player.hp -= 2 
                    self.player.invincible_timer = 100
                    self.trigger_shake(150, 5) # 레이저 피격 시 지속 진동

        if self.player.hp <= 0: 
            self.game_over = True

    def update(self, dt):
        if self.game_over: return 
        
        self.player.update(self.platforms, dt)

        # 쉐이크 타이머 감소 로직
        if self.shake_timer > 0:
            self.shake_timer -= dt

        if self.ui_message_timer > 0:
            self.ui_message_timer -= dt

        # 1. 보스 로직 (dt 인자 오류 수정)
        if self.boss.hp > 0:
            if isinstance(self.boss, LaserBoss):
                self.boss.update(self.player.rect, self.platforms, dt)
                # 레이저 발사 중일 때 화면 전체가 덜덜 떨리는 연출
                if self.boss.is_firing:
                    self.trigger_shake(50, 3) 
            else:
                self.boss.update(self.player.rect, self.platforms)
            
            if self.boss.rect.top > SCREEN_HEIGHT:
                self.boss.hp = 0
                self.ui_message = "보스가 낙사했습니다!"
                self.ui_message_timer = 3000
                
        else:
            self.boss_respawn_timer += dt
            if self.boss_respawn_timer >= 15000:  
                if random.random() > 0.5:
                    self.boss = DashBoss(random.randint(100, 700), 100)
                else:
                    self.boss = LaserBoss(random.randint(100, 700), 150)
                self.boss_respawn_timer = 0
                self.ui_message = "보스가 리젠되었습니다!"
                self.ui_message_timer = 3000

        # 2. 아이템 스폰
        self.item_spawn_timer += dt
        if self.item_spawn_timer >= 5000:
            self.item_spawn_timer = 0
            spawn_x = random.randint(50, SCREEN_WIDTH - 50)
            spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
            if len(self.items) < 3:
                random_type = random.choice(["double_shot", "heal", "shield"])
                self.items.append(Item(spawn_x, spawn_y, random_type))

        # 3. 일반 적 업데이트
        for e in self.enemies[:]:
            if isinstance(e, RangedEnemy): 
                e.update(self.player.rect, self.platforms, self.enemy_bullets)
            else: 
                e.update(self.player.rect, self.platforms)
            
            if e.rect.top > SCREEN_HEIGHT:
                self.enemies.remove(e)
                new_enemy = RangedEnemy(random.choice([0, 750]), 0) if random.random() > 0.5 else Enemy(random.choice([0, 750]), 0)
                self.enemies.append(new_enemy)

        # 4. 투사체 업데이트
        for m in self.missiles[:]:
            m.update()
            if not screen.get_rect().colliderect(m.rect): self.missiles.remove(m)

        for eb in self.enemy_bullets[:]:
            eb.update()
            if not screen.get_rect().colliderect(eb.rect): self.enemy_bullets.remove(eb)

        self.process_collisions() 

    def draw(self, screen):
        # 1. 스크린 쉐이크를 위해 '임시 표면(도화지)' 생성
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.fill(BG_COLOR) 
        
        # 2. 모든 객체를 실제 화면(screen)이 아닌 임시 도화지(temp_surface)에 그립니다.
        for plat in self.platforms: pygame.draw.rect(temp_surface, GREEN, plat)
        for i in self.items: i.draw(temp_surface)
        for m in self.missiles: m.draw(temp_surface)
        for eb in self.enemy_bullets: eb.draw(temp_surface)
        for e in self.enemies: e.draw(temp_surface)
        if self.boss.hp > 0: self.boss.draw(temp_surface) 
        self.player.draw(temp_surface)
        
        self.draw_ui(temp_surface) 

        # 3. 흔들림 계산 (offset 지정)
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        # 4. 실제 화면에 임시 도화지를 덮어씌움 (이때 흔들린 좌표만큼 이동시켜서 붙임)
        screen.fill((0, 0, 0)) # 여백을 검은색으로 채움
        screen.blit(temp_surface, (shake_x, shake_y))

    def draw_ui(self, surface):
        pygame.draw.rect(surface, (50, 50, 50), (20, 20, 200, 20)) 
        pygame.draw.rect(surface, RED, (20, 20, max(0, self.player.hp * 2), 20)) 
        
        score_txt = font.render(f"SCORE: {self.player.score}  BOSS HP: {max(0, self.boss.hp)}", True, YELLOW)
        surface.blit(score_txt, (SCREEN_WIDTH - 300, 20))
        
        if self.game_over:
            msg = large_font.render("GAME OVER (R)", True, WHITE)
            surface.blit(msg, (SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-50))

        y_offset = 50
        if self.player.has_double_shot:
            item_txt = font.render(f"DOUBLE SHOT: {max(0, self.player.item_timer // 1000 + 1)}s", True, MAGENTA)
            surface.blit(item_txt, (20, y_offset))
            y_offset += 25
            
        if self.player.shield_timer > 0:
            shield_txt = font.render(f"SHIELD: {max(0, self.player.shield_timer // 1000 + 1)}s", True, CYAN)
            surface.blit(shield_txt, (20, y_offset))

        if self.ui_message_timer > 0:
            msg_txt = font.render(self.ui_message, True, WHITE)
            msg_rect = msg_txt.get_rect(center=(SCREEN_WIDTH // 2, 80)) 
            
            bg_rect = msg_rect.inflate(30, 15) 
            pygame.draw.rect(surface, (0, 0, 0), bg_rect) 
            pygame.draw.rect(surface, WHITE, bg_rect, 2)  
            
            surface.blit(msg_txt, msg_rect)

# ==========================================
# 6. 메인 실행 루프
# ==========================================
game = Game()
clock = pygame.time.Clock() 

while True:
    dt = clock.tick(60) 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if not game.game_over: 
                if event.key == pygame.K_SPACE: game.player.jump()
                if event.key == pygame.K_s: game.player.shoot(game.missiles)
            elif event.key == pygame.K_r: 
                game.reset()

    if not game.game_over: 
        game.player.handle_input(pygame.key.get_pressed())
        
    game.update(dt)
    game.draw(screen)
    
    pygame.display.flip()
