import pygame
import sys
import random
import math

# ==========================================
# 1. 게임 설정 및 상수 정의 (Configuration)
# ==========================================
pygame.init()

# [디스플레이 및 환경]
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TARGET_FPS = 60
GRAVITY = 2400.0
TOLERANCE_Y = 2

# [색상]
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)      
MAGENTA = (255, 0, 255)   
BG_COLOR = (30, 30, 30)   

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Awesome Action Game - Sprite Architecture")

font = pygame.font.SysFont("malgungothic", 20)        
large_font = pygame.font.SysFont("malgungothic", 60) 

# [게임 밸런스 수치]
SCORE_PER_LEVEL = 1000
SCORE_TWO_BOSS_LIMIT = 10000

PLAYER_MAX_HP = 100
PLAYER_SPEED = 300.0
PLAYER_JUMP_FORCE = -900.0
PLAYER_INVINCIBLE_DUR = 1000

MISSILE_SPEED = 800.0
MISSILE_DAMAGE = 40
DOUBLE_SHOT_OFFSET = 10
ENEMY_BULLET_SPEED = 300.0
ENEMY_BULLET_DAMAGE = 10

ITEM_SPAWN_INTERVAL = 5000
ITEM_DOUBLE_SHOT_DUR = 8000
ITEM_SHIELD_DUR = 5000
ITEM_HEAL_AMOUNT = 30
SCORE_ITEM_PICKUP = 500
SCORE_ENEMY_KILL = 100
SCORE_BOSS_KILL = 2000

ENEMY_BASE_HP = 100
ENEMY_HP_SCALE = 20
ENEMY_BASE_SPEED = 120.0
ENEMY_SPEED_SCALE = 24.0
ENEMY_JUMP_FORCE = -900.0
ENEMY_JUMP_CHANCE = 0.05
ENEMY_JUMP_COOLDOWN = 1000
ENEMY_MELEE_DAMAGE = 20
ENEMY_SPAWN_MAX_DELAY = 4000
ENEMY_SPAWN_MIN_DELAY = 800
ENEMY_SPAWN_DECREASE = 400

RANGED_SHOOT_DELAY = 1500
RANGED_APPROACH_DIST = 300
RANGED_FLEE_DIST = 200

DBOSS_MAX_HP = 500
DBOSS_IDLE_TIME = 1500
DBOSS_READY_TIME = 500
DBOSS_DASH_SPEED = 800.0
DBOSS_DASH_TIME = 800
DBOSS_JUMP_FORCE = -1200.0
DBOSS_JUMP_SPEED_X = 450.0

LBOSS_MAX_HP = 600
LBOSS_MOVE_SPEED = 120.0
LBOSS_BASE_Y = 150
LBOSS_SINE_FREQ = 0.006
LBOSS_SINE_AMP = 60
LBOSS_MOVE_TIME = 3000
LBOSS_CHARGE_TIME = 1500
LBOSS_FIRE_TIME = 2000
LBOSS_LASER_DAMAGE = 2
LBOSS_LASER_HIT_INV = 100

BOSS_RESPAWN_INTERVAL = 10000
SHAKE_BOSS_KILL = (500, 10)
SHAKE_PLAYER_HIT_MELEE = (200, 8)
SHAKE_PLAYER_HIT_BULLET = (100, 3)
SHAKE_PLAYER_HIT_LASER = (150, 5)
SHAKE_LASER_FIRING = (50, 3)


# ==========================================
# 2. 베이스 클래스 (Sprite 상속 및 Float 좌표계)
# ==========================================
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.true_x = float(x)
        self.true_y = float(y)
        self.rect = pygame.Rect(int(x), int(y), width, height)
        self.color = color
        self.y_vel = 0.0

    def update_rect(self):
        self.rect.x = int(self.true_x)
        self.rect.y = int(self.true_y)

    def sync_from_rect(self):
        self.true_x = float(self.rect.x)
        self.true_y = float(self.rect.y)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


# ==========================================
# 3. 플레이어 및 투사체 클래스
# ==========================================
class Player(Entity):
    def __init__(self):
        super().__init__(100, SCREEN_HEIGHT - 100, 40, 40, RED)
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.score = 0
        self.direction = 1
        self.is_jumping = False
        self.invincible_timer = 0
        self.speed = PLAYER_SPEED
        self.has_double_shot = False
        self.item_timer = 0
        self.shield_timer = 0

    def handle_input(self, keys, dt_sec):
        if keys[pygame.K_LEFT]:
            self.true_x -= self.speed * dt_sec
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            self.true_x += self.speed * dt_sec
            self.direction = 1

        self.update_rect()

        if self.rect.left < 0:
            self.rect.left = 0
            self.sync_from_rect()
            
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.sync_from_rect()

    def jump(self):
        if not self.is_jumping:
            self.y_vel = PLAYER_JUMP_FORCE
            self.is_jumping = True

    def shoot(self, missile_group):
        if self.has_double_shot:
            offsets = [-DOUBLE_SHOT_OFFSET, DOUBLE_SHOT_OFFSET]
        else:
            offsets = [0]
            
        for off in offsets:
            m = Missile(self.rect.centerx, self.rect.centery, self.direction, off)
            missile_group.add(m)

    def update(self, platforms, dt):
        dt_sec = dt / 1000.0
        self.y_vel += GRAVITY * dt_sec
        self.true_y += self.y_vel * dt_sec
        self.update_rect()
        
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            
        if self.has_double_shot:
            self.item_timer -= dt
            if self.item_timer <= 0:
                self.has_double_shot = False
                
        if self.shield_timer > 0:
            self.shield_timer -= dt

        on_ground = False
        if self.y_vel >= 0:
            temp_rect = self.rect.copy()
            temp_rect.y += TOLERANCE_Y
            for plat in platforms:
                if temp_rect.colliderect(plat):
                    # 이전 프레임 위치를 고려한 정확한 착지 검사
                    if self.rect.bottom - (self.y_vel * dt_sec) <= plat.top + TOLERANCE_Y:
                        self.rect.bottom = plat.top
                        self.sync_from_rect()
                        self.y_vel = 0
                        on_ground = True
                        break
                        
        self.is_jumping = not on_ground

    def draw(self, surface):
        if self.invincible_timer <= 0 or (self.invincible_timer // 100) % 2 == 0:
            super().draw(surface)
        if self.shield_timer > 0:
            pygame.draw.rect(surface, CYAN, self.rect.inflate(10, 10), 3)


class Missile(Entity):
    def __init__(self, x, y, direction, offset_y=0):
        super().__init__(x, y + offset_y, 15, 8, CYAN)
        self.direction = direction
        self.speed = MISSILE_SPEED

    def update(self, dt):
        dt_sec = dt / 1000.0
        self.true_x += self.speed * self.direction * dt_sec
        self.update_rect()
        
        # 화면 밖으로 나가면 즉시 메모리 해제 및 그룹에서 제거
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()


class EnemyBullet(Entity):
    def __init__(self, x, y, target_x, target_y):
        super().__init__(x, y, 10, 10, YELLOW)
        angle = math.atan2(target_y - y, target_x - x)
        self.speed = ENEMY_BULLET_SPEED
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed

    def update(self, dt):
        dt_sec = dt / 1000.0
        self.true_x += self.vx * dt_sec
        self.true_y += self.vy * dt_sec
        self.update_rect()
        
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()


# ==========================================
# 4. 적 및 보스 클래스
# ==========================================
class Enemy(Entity):
    def __init__(self, x, y, level=1):
        super().__init__(x, y, 35, 35, ORANGE)
        self.max_hp = ENEMY_BASE_HP + (level * ENEMY_HP_SCALE)
        self.hp = self.max_hp
        self.speed = ENEMY_BASE_SPEED + (level * ENEMY_SPEED_SCALE)
        self.jump_cooldown = 0

    def update(self, player_rect, platforms, dt, *args):
        dt_sec = dt / 1000.0
        
        if self.rect.x < player_rect.x:
            self.true_x += self.speed * dt_sec
        else:
            self.true_x -= self.speed * dt_sec
        
        self.y_vel += GRAVITY * dt_sec
        self.true_y += self.y_vel * dt_sec
        self.update_rect()

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

        on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.sync_from_rect()
                self.y_vel = 0
                on_ground = True
                
        if self.jump_cooldown > 0:
            self.jump_cooldown -= dt
            
        if on_ground and self.jump_cooldown <= 0:
            if player_rect.bottom < self.rect.top - 20:
                if random.random() < ENEMY_JUMP_CHANCE:
                    self.y_vel = ENEMY_JUMP_FORCE
                    self.jump_cooldown = ENEMY_JUMP_COOLDOWN

    def draw(self, surface):
        super().draw(surface)
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 10, self.rect.width, 5))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 10, self.rect.width * hp_ratio, 5))


class RangedEnemy(Enemy):
    def __init__(self, x, y, level=1):
        super().__init__(x, y, level)
        self.color = GREEN
        self.shoot_delay = 0

    def update(self, player_rect, platforms, dt, enemy_bullets_group=None):
        dt_sec = dt / 1000.0
        dist = player_rect.x - self.rect.x
        
        if abs(dist) > RANGED_APPROACH_DIST:
            self.true_x += self.speed * dt_sec if dist > 0 else -self.speed * dt_sec
        elif abs(dist) < RANGED_FLEE_DIST:
            self.true_x -= self.speed * dt_sec if dist > 0 else -self.speed * dt_sec

        self.y_vel += GRAVITY * dt_sec
        self.true_y += self.y_vel * dt_sec
        self.update_rect()
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.sync_from_rect()
                self.y_vel = 0

        self.shoot_delay += dt
        if self.shoot_delay > RANGED_SHOOT_DELAY and enemy_bullets_group is not None:
            eb = EnemyBullet(self.rect.centerx, self.rect.centery, player_rect.centerx, player_rect.centery)
            enemy_bullets_group.add(eb)
            self.shoot_delay = 0


class DashBoss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect.size = (70, 70)
        self.hp = DBOSS_MAX_HP
        self.max_hp = DBOSS_MAX_HP
        self.state = "IDLE"
        self.timer = 0
        self.dash_dir = 1
        self.on_ground = False

    def update(self, player_rect, platforms, dt, *args):
        dt_sec = dt / 1000.0
        self.timer += dt
        
        if self.state == "IDLE":
            self.color = ORANGE
            if self.timer > DBOSS_IDLE_TIME:
                self.timer = 0
                self.state = "READY" if random.random() < 0.6 else "JUMP_READY"
                
        elif self.state == "READY":
            self.color = WHITE
            if self.timer > DBOSS_READY_TIME:
                self.state = "DASH"
                self.dash_dir = 1 if player_rect.x > self.rect.x else -1
                self.timer = 0
                
        elif self.state == "DASH":
            self.color = RED
            self.true_x += self.dash_dir * DBOSS_DASH_SPEED * dt_sec
            self.update_rect()
            
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.dash_dir *= -1
                
            if self.timer > DBOSS_DASH_TIME:
                self.state = "IDLE"
                self.timer = 0
                
        elif self.state == "JUMP_READY":
            self.color = CYAN
            if self.timer > DBOSS_READY_TIME:
                self.state = "JUMP"
                self.y_vel = DBOSS_JUMP_FORCE
                self.timer = 0
                self.dash_dir = 1 if player_rect.x > self.rect.x else -1
                
        elif self.state == "JUMP":
            self.color = MAGENTA
            self.true_x += self.dash_dir * DBOSS_JUMP_SPEED_X * dt_sec
            self.update_rect()
            
            if self.timer > 160 and self.on_ground:
                self.state = "IDLE"
                self.timer = 0
                
        # 벽 충돌 처리
        if self.state in ["DASH", "JUMP"]:
            if self.rect.left <= 0:
                self.rect.left = 0
                self.sync_from_rect()
                self.dash_dir = 1
            elif self.rect.right >= SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                self.sync_from_rect()
                self.dash_dir = -1

        self.y_vel += GRAVITY * dt_sec
        self.true_y += self.y_vel * dt_sec
        self.update_rect()
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat) and self.y_vel > 0:
                self.rect.bottom = plat.top
                self.sync_from_rect()
                self.y_vel = 0
                self.on_ground = True


class LaserBoss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect.size = (80, 80)
        self.hp = LBOSS_MAX_HP
        self.max_hp = LBOSS_MAX_HP
        self.color = (100, 0, 100)
        self.state = "MOVE"
        self.timer = 0
        self.laser_rect = pygame.Rect(0, 0, 0, 0)
        self.is_firing = False
        self.base_y = LBOSS_BASE_Y

    def update(self, player_rect, platforms, dt, *args):
        dt_sec = dt / 1000.0
        self.timer += dt
        
        if self.state == "MOVE":
            move_speed = LBOSS_MOVE_SPEED * dt_sec
            self.true_x += move_speed if self.rect.x < player_rect.x else -move_speed
            self.true_y = float(self.base_y + math.sin(pygame.time.get_ticks() * LBOSS_SINE_FREQ) * LBOSS_SINE_AMP)
            self.update_rect()
            
            if self.timer > LBOSS_MOVE_TIME:
                self.state = "CHARGE"
                self.timer = 0
                
        elif self.state == "CHARGE":
            self.color = (200, 100, 255)
            if self.timer > LBOSS_CHARGE_TIME:
                self.state = "FIRE"
                self.timer = 0
                self.is_firing = True
                self.laser_rect = pygame.Rect(self.rect.centerx - 40, self.rect.bottom, 80, SCREEN_HEIGHT)
                
        elif self.state == "FIRE":
            self.color = WHITE
            self.laser_rect.top = self.rect.bottom
            if self.timer > LBOSS_FIRE_TIME:
                self.state = "MOVE"
                self.timer = 0
                self.is_firing = False

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self, surface):
        super().draw(surface)
        if self.state == "CHARGE":
            pygame.draw.rect(surface, RED, (self.rect.centerx - 2, self.rect.bottom, 4, SCREEN_HEIGHT), 1)
        if self.is_firing:
            pygame.draw.rect(surface, CYAN, self.laser_rect)
            pygame.draw.rect(surface, WHITE, self.laser_rect.inflate(-20, 0))


# ==========================================
# 5. 아이템 클래스 (다형성 적용)
# ==========================================
class Item(Entity):
    def __init__(self, x, y, color):
        super().__init__(x, y, 25, 25, color)

    def apply_effect(self, player):
        """이 아이템이 플레이어에게 미치는 효과 (자식 클래스에서 덮어써야 함)"""
        pass 

    def draw(self, surface):
        if (pygame.time.get_ticks() // 200) % 2 == 0:
            super().draw(surface)
        else:
            pygame.draw.rect(surface, WHITE, self.rect, 2)


class HealItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, GREEN)
        
    def apply_effect(self, player):
        player.hp = min(player.max_hp, player.hp + ITEM_HEAL_AMOUNT)


class DoubleShotItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, MAGENTA)
        
    def apply_effect(self, player):
        player.has_double_shot = True
        player.item_timer = ITEM_DOUBLE_SHOT_DUR


class ShieldItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, CYAN)
        
    def apply_effect(self, player):
        player.shield_timer = ITEM_SHIELD_DUR


# ==========================================
# 6. 게임 매니저
# ==========================================
class Game:
    def __init__(self):
        self.platforms = [
            pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40),
            pygame.Rect(200, 450, 200, 20),
            pygame.Rect(450, 300, 200, 20),
            pygame.Rect(150, 180, 200, 20)
        ]
        self.shake_timer = 0
        self.shake_intensity = 0
        self.reset()

    def trigger_shake(self, duration=200, intensity=5):
        self.shake_timer = duration
        self.shake_intensity = intensity

    def reset(self):
        self.player = Player()
        self.level = 1
        
        self.enemies = pygame.sprite.Group()
        self.bosses = pygame.sprite.Group()
        self.missiles = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        
        self.enemies.add(Enemy(random.randint(0, 700), 0, self.level))
        self.enemies.add(RangedEnemy(700, 0, self.level))
        
        if random.random() > 0.5:
            self.bosses.add(DashBoss(600, 400))
        else:
            self.bosses.add(LaserBoss(400, 150))
            
        self.items.add(HealItem(400, 300))
        
        self.enemy_spawn_timer = 0
        self.game_over = False
        self.item_spawn_timer = 0
        self.boss_respawn_timer = 0
        self.ui_message = ""
        self.ui_message_timer = 0
        self.shake_timer = 0

    def process_collisions(self):
        if self.player.rect.top > SCREEN_HEIGHT:
            self.player.hp = 0
            self.ui_message = "낭떠러지로 추락!"
            self.ui_message_timer = 3000

        # 아이템 충돌 처리 (다형성)
        hit_items = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in hit_items:
            item.apply_effect(self.player)
            self.player.score += SCORE_ITEM_PICKUP

        # 미사일 vs 적
        enemy_hits = pygame.sprite.groupcollide(self.enemies, self.missiles, False, True)
        for enemy, hit_missiles in enemy_hits.items():
            enemy.hp -= MISSILE_DAMAGE * len(hit_missiles)
            if enemy.hp <= 0:
                enemy.kill() 
                self.player.score += SCORE_ENEMY_KILL

        # 미사일 vs 보스
        boss_hits = pygame.sprite.groupcollide(self.bosses, self.missiles, False, True)
        for boss, hit_missiles in boss_hits.items():
            boss.hp -= MISSILE_DAMAGE * len(hit_missiles)
            if boss.hp <= 0:
                boss.kill()
                self.player.score += SCORE_BOSS_KILL
                self.trigger_shake(*SHAKE_BOSS_KILL)

        # 적 총알 vs 플레이어
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            if self.player.shield_timer <= 0: 
                self.player.hp -= ENEMY_BULLET_DAMAGE
                self.trigger_shake(*SHAKE_PLAYER_HIT_BULLET)

        # 적/보스 몸통 박치기 vs 플레이어
        if self.player.invincible_timer <= 0:
            collide_enemy = pygame.sprite.spritecollideany(self.player, self.enemies)
            collide_boss = pygame.sprite.spritecollideany(self.player, self.bosses)
            
            if collide_enemy or collide_boss:
                if self.player.shield_timer <= 0:
                    self.player.hp -= ENEMY_MELEE_DAMAGE
                    self.trigger_shake(*SHAKE_PLAYER_HIT_MELEE)
                self.player.invincible_timer = PLAYER_INVINCIBLE_DUR

        # 레이저 보스 특수 공격 처리
        for b in self.bosses:
            if isinstance(b, LaserBoss) and b.is_firing:
                if self.player.rect.colliderect(b.laser_rect):
                    if self.player.shield_timer <= 0 and self.player.invincible_timer <= 0:
                        self.player.hp -= LBOSS_LASER_DAMAGE
                        self.player.invincible_timer = LBOSS_LASER_HIT_INV
                        self.trigger_shake(*SHAKE_PLAYER_HIT_LASER)

        if self.player.hp <= 0:
            self.game_over = True

    def update(self, dt):
        if self.game_over:
            return
        
        self.player.update(self.platforms, dt)
        self.level = 1 + (self.player.score // SCORE_PER_LEVEL)
        
        if self.shake_timer > 0:
            self.shake_timer -= dt
            
        if self.ui_message_timer > 0:
            self.ui_message_timer -= dt
            
        for b in self.bosses:
            b.update(self.player.rect, self.platforms, dt)
            if isinstance(b, LaserBoss) and b.is_firing:
                self.trigger_shake(*SHAKE_LASER_FIRING)

        target_boss_count = 2 if self.player.score >= SCORE_TWO_BOSS_LIMIT else 1
        
        if len(self.bosses) < target_boss_count:
            self.boss_respawn_timer += dt
            if self.boss_respawn_timer >= BOSS_RESPAWN_INTERVAL:
                if random.random() > 0.5:
                    new_boss = DashBoss(random.randint(100, 700), 100)
                else:
                    new_boss = LaserBoss(random.randint(100, 700), 150)
                    
                self.bosses.add(new_boss)
                self.boss_respawn_timer = 0
                self.ui_message = "보스가 등장했습니다!"
                self.ui_message_timer = 2000

        self.item_spawn_timer += dt
        if self.item_spawn_timer >= ITEM_SPAWN_INTERVAL:
            self.item_spawn_timer = 0
            if len(self.items) < 3:
                valid_position = False
                while not valid_position:
                    spawn_x = random.randint(50, SCREEN_WIDTH - 50)
                    spawn_y = random.randint(100, SCREEN_HEIGHT - 100)
                    temp_rect = pygame.Rect(spawn_x, spawn_y, 25, 25)
                    
                    collision = any(temp_rect.colliderect(p) for p in self.platforms)
                    if not collision:
                        valid_position = True
                        
                item_classes = [HealItem, DoubleShotItem, ShieldItem]
                random_item_class = random.choice(item_classes)
                self.items.add(random_item_class(spawn_x, spawn_y))

        self.enemy_spawn_timer += dt
        spawn_delay = max(ENEMY_SPAWN_MIN_DELAY, ENEMY_SPAWN_MAX_DELAY - (self.level * ENEMY_SPAWN_DECREASE))
        
        if self.enemy_spawn_timer >= spawn_delay:
            self.enemy_spawn_timer = 0
            if random.random() > 0.5:
                new_enemy = RangedEnemy(random.choice([0, 750]), 0, self.level)
            else:
                new_enemy = Enemy(random.choice([0, 750]), 0, self.level)
            self.enemies.add(new_enemy)

        for e in self.enemies:
            e.update(self.player.rect, self.platforms, dt, self.enemy_bullets)
            
        for m in self.missiles:
            m.update(dt)
            
        for eb in self.enemy_bullets:
            eb.update(dt)

        self.process_collisions()

    def draw(self, screen):
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.fill(BG_COLOR)
        
        for plat in self.platforms:
            pygame.draw.rect(temp_surface, GREEN, plat)
        
        for i in self.items:
            i.draw(temp_surface)
        for m in self.missiles:
            m.draw(temp_surface)
        for eb in self.enemy_bullets:
            eb.draw(temp_surface)
        for e in self.enemies:
            e.draw(temp_surface)
        for b in self.bosses:
            b.draw(temp_surface)
        
        self.player.draw(temp_surface)
        self.draw_ui(temp_surface)
        
        if self.shake_timer > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)
        else:
            shake_x = 0
            shake_y = 0
            
        screen.fill((0, 0, 0))
        screen.blit(temp_surface, (shake_x, shake_y))

    def draw_ui(self, surface):
        pygame.draw.rect(surface, (50, 50, 50), (20, 20, 200, 20))
        pygame.draw.rect(surface, RED, (20, 20, max(0, self.player.hp * 2), 20))
        
        boss_count = len(self.bosses)
        score_txt = font.render(
            f"LV: {self.level} | SCORE: {self.player.score} | BOSSES: {boss_count}",
            True,
            YELLOW
        )
        surface.blit(score_txt, (SCREEN_WIDTH - 380, 20))
        
        if self.game_over:
            msg = large_font.render("GAME OVER (R)", True, WHITE)
            surface.blit(msg, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
            
        if self.ui_message_timer > 0:
            msg_txt = font.render(self.ui_message, True, WHITE)
            msg_rect = msg_txt.get_rect(center=(SCREEN_WIDTH // 2, 80))
            pygame.draw.rect(surface, (0, 0, 0), msg_rect.inflate(30, 15))
            surface.blit(msg_txt, msg_rect)


# ==========================================
# 7. 메인 루프
# ==========================================
if __name__ == "__main__":
    game = Game()
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(TARGET_FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if not game.game_over:
                    if event.key == pygame.K_SPACE:
                        game.player.jump()
                    if event.key == pygame.K_s:
                        game.player.shoot(game.missiles)
                elif event.key == pygame.K_r:
                    game.reset()
                
        if not game.game_over:
            dt_sec = dt / 1000.0
            game.player.handle_input(pygame.key.get_pressed(), dt_sec)
            
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
