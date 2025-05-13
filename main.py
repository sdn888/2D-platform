import pygame
import sys
import random

# Инициализация
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)

# Физика
gravity = 0.5
jump_power = -10
player_speed = 5

# Параметры прыжка
MAX_JUMP_HEIGHT = 90
MAX_HORIZONTAL_DISTANCE = 200

# Создание экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Платформер: Все монетки доступны!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# Звуки
sound_enabled = False
try:
    pygame.mixer.init()
    jump_sound = pygame.mixer.Sound("sounds/jump.wav")
    coin_sound = pygame.mixer.Sound("sounds/coin.wav")
    hurt_sound = pygame.mixer.Sound("sounds/hurt.wav")
    game_over_sound = pygame.mixer.Sound("sounds/game_over.wav")
    sound_enabled = True
except Exception as e:
    print(f"Звуковые файлы не найдены: {e}. Игра без звука.")

# Изображения
try:
    BACKGROUND_IMG = pygame.transform.scale(
        pygame.image.load("images/background.png").convert(), (WIDTH, HEIGHT)
    )
    PLAYER_NORMAL_IMG = pygame.transform.scale(pygame.image.load("images/cat_basic.png").convert_alpha(), (60, 60))
    PLAYER_BURNED_IMG = pygame.transform.scale(pygame.image.load("images/cat_burned_f3.png").convert_alpha(), (60, 60))
    COIN_IMG = pygame.transform.scale(pygame.image.load("images/coin.png").convert_alpha(), (20, 20))
    FIREBALL_IMG = pygame.transform.scale(pygame.image.load("images/fireball.png").convert_alpha(), (30, 30))
except FileNotFoundError as e:
    print(f"Не хватает изображения: {e}")
    pygame.quit()
    sys.exit()

# Классы
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = PLAYER_NORMAL_IMG
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.on_ground = False
        self.burned = False
        self.burned_time = 0
        self.platform_dx = 0

    def update(self, keys):
        # --- Состояние горения ---
        if self.burned and pygame.time.get_ticks() - self.burned_time >= 2000:
            self.image = PLAYER_NORMAL_IMG
            self.mask = pygame.mask.from_surface(self.image)
            self.burned = False

        # --- Инициализация смещений ---
        dx = 0
        dy = 0

        # --- Горизонтальное движение ---
        if keys[pygame.K_a]:
            dx = -player_speed
        if keys[pygame.K_d]:
            dx = player_speed

        # Применяем горизонтальное смещение
        self.rect.x += dx
        # Проверяем границы экрана по горизонтали
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        # Здесь можно добавить проверку столкновений со стенами, если они есть

        # --- Вертикальное движение ---
        # Сначала предполагаем, что не на земле
        self.on_ground = False

        # Применяем гравитацию
        self.vel_y += gravity
        # Ограничиваем скорость падения (опционально, но полезно)
        if self.vel_y > 15:  # Максимальная скорость падения
            self.vel_y = 15
        dy += self.vel_y  # Добавляем вертикальную скорость к смещению

        # Сохраняем текущую позицию Y перед движением
        previous_y = self.rect.y

        # Предварительно применяем вертикальное смещение
        self.rect.y += dy

        # Проверка столкновений по вертикали
        for p in platform_group:
            # Проверяем, столкнулся ли игрок с платформой
            if p.rect.colliderect(self.rect):
                # Если движемся ВНИЗ (сталкиваемся с верхом платформы)
                if self.vel_y > 0:
                    # Ставим низ игрока ТОЧНО на верх платформы
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0  # Останавливаем вертикальное движение
                    self.on_ground = True  # Теперь точно на земле
                    dy = 0  # Отменяем оставшееся смещение dy в этом кадре
                    break  # Нашли опору, дальше не проверяем

                # Если движемся ВВЕРХ (сталкиваемся с низом платформы)
                elif self.vel_y < 0 and not p.can_pass_through:
                    # Ставим верх игрока ТОЧНО под низ платформы
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0  # Останавливаем вертикальное движение
                    dy = 0  # Отменяем оставшееся смещение dy
                    # self.on_ground не меняем
                    break  # Ударились о потолок

        # Если после проверки столкновений мы все еще "на земле" (не было отрыва),
        # учитываем горизонтальное движение платформы
        if self.on_ground:
            self.rect.x += (p.speed * p.direction if hasattr(p, 'moving') and p.moving and p.rect.colliderect(self.rect) else 0)

        # Проверка нижней границы экрана (если упал ниже платформ)
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel_y = 0
            self.on_ground = True  # Считаем пол уровнем земли

        # Возвращаем Y на предыдущее значение, чтобы проверить, оторвались ли мы от земли
        self.rect.y = previous_y
        # Снова применяем вертикальное смещение
        self.rect.y += self.vel_y

        # После применения вертикального движения окончательно проверяем, на земле ли мы
        self.on_ground = False
        for p in platform_group:
            if p.rect.colliderect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height) and self.vel_y >= 0:
                self.on_ground = True
                self.rect.bottom = p.rect.top
                self.vel_y = 0
                break

        # Применяем остаточное горизонтальное смещение от платформы (если есть и мы на земле)
        self.rect.x += (p.speed * p.direction if self.on_ground and hasattr(p, 'moving') and p.moving and p.rect.colliderect(self.rect) else 0)

        # Финальные проверки границ
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = min(HEIGHT - self.rect.height, self.rect.y)

    def jump(self):
        if self.on_ground:
            self.vel_y = jump_power
            self.on_ground = False # Сразу после прыжка перестаем быть на земле
            if sound_enabled:
                jump_sound.play()

        self.rect.x += dx + (self.platform_dx if self.on_ground else 0)
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y += dy
        self.rect.y = min(HEIGHT - self.rect.height, self.rect.y)

    def jump(self):
        if self.on_ground:
            self.vel_y = jump_power
            if sound_enabled:
                jump_sound.play()

    def take_hit(self):
        if not self.burned:
            self.image = PLAYER_BURNED_IMG
            self.burned = True
            self.burned_time = pygame.time.get_ticks()
            if sound_enabled:
                hurt_sound.play()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, moving=False, speed=0, can_pass_through=False, image_path=None):
        super().__init__()
        if image_path:
            original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (w, h))
        else:
            self.image = pygame.Surface((w, h))
            self.image.fill((100, 100, 100))  # Цвет по умолчанию

        self.rect = self.image.get_rect(topleft=(x, y))
        self.moving = moving
        self.speed = speed
        self.direction = 1
        self.can_pass_through = can_pass_through

    def update(self):
        if self.moving:
            self.rect.x += self.speed * self.direction
            if self.rect.left < 0 or self.rect.right > WIDTH:
                self.direction *= -1


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = COIN_IMG
        self.rect = self.image.get_rect(center=(x, y))


class Fireball(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = FIREBALL_IMG
        self.rect = self.image.get_rect(center=(x, 0))
        self.speed = 5

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


# Логика проверок
def can_reach(prev_platform, new_platform):
    dx = abs(new_platform.rect.centerx - prev_platform.rect.centerx)
    dy = prev_platform.rect.top - new_platform.rect.top  # сравнение по верхним границам
    return dx <= MAX_HORIZONTAL_DISTANCE and 0 <= dy <= MAX_JUMP_HEIGHT


def coin_is_reachable(platform, coin):
    dy = platform.rect.top - coin.rect.centery
    dx = abs(coin.rect.centerx - platform.rect.centerx)

    return 0 <= dy <= MAX_JUMP_HEIGHT and dx <= MAX_HORIZONTAL_DISTANCE


def generate_random_level(level_num):
    platforms = []
    coins = []

    # Начальная платформа (пол)
    start_platform = Platform(0, HEIGHT - 40, WIDTH, 40, "images/ground.png") # Пример пути к изображению земли
    platforms.append(start_platform)

    last_platform = start_platform
    total_platforms = 3 + level_num * 2

    platform_images = ["images/platform1.png", "images/platform2.png"]  # Список возможных изображений платформ

    for _ in range(total_platforms):
        attempts = 0
        while attempts < 10:
            w = random.randint(80, 150)
            h = 20

            # Генерируем только "достижимые" координаты
            min_y = max(60, last_platform.rect.top - MAX_JUMP_HEIGHT - 20)
            max_y = max(80, last_platform.rect.top - 40)
            y = random.randint(min_y, max_y)
            x = random.randint(
                max(0, last_platform.rect.centerx - MAX_HORIZONTAL_DISTANCE),
                min(WIDTH - w, last_platform.rect.centerx + MAX_HORIZONTAL_DISTANCE)
            )

            moving = random.random() < 0.3
            speed = random.randint(1, 3) if moving else 0
            pass_through = random.random() < 0.2
            image_path = random.choice(platform_images)
            candidate = Platform(x, y, w, h, moving, speed, pass_through)

            if can_reach(last_platform, candidate):
                coin_x = x + w // 2
                coin_y = max(30, y - 30)
                coin = Coin(coin_x, coin_y)

                if coin_is_reachable(candidate, coin):
                    platforms.append(candidate)
                    coins.append(coin)
                    last_platform = candidate
                    break
            attempts += 1

    fireball_interval = max(1000, 5000 - level_num * 500)
    return {
        "platforms": platforms,
        "coins": coins,
        "fireball_interval": fireball_interval
    }


# Игровые переменные
NUM_LEVELS = 10
levels = [generate_random_level(i) for i in range(NUM_LEVELS)]

current_level = 0

player = Player(100, 500)
player_group = pygame.sprite.Group(player)
platform_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()

score = 0
lives = 3
paused = False
last_fireball_time = pygame.time.get_ticks()


def load_level(index):
    platform_group.empty()
    coin_group.empty()
    fireball_group.empty()
    for p in levels[index]["platforms"]:
        platform_group.add(p)
    for c in levels[index]["coins"]:
        coin_group.add(c)


def draw_ui():
    screen.blit(font.render(f"Счёт: {score}", True, BLACK), (10, 10))
    screen.blit(font.render(f"Жизни: {lives}", True, BLACK), (10, 40))
    if paused:
        screen.blit(font.render("Пауза", True, BLACK), (WIDTH // 2 - 40, HEIGHT // 2))


def show_game_over():
    if sound_enabled:
        game_over_sound.play()
    screen.fill(BLACK)
    text = font.render("Game Over", True, WHITE)
    screen.blit(text, (WIDTH // 2 - 60, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.delay(2000)


def show_level_transition(level_number):
    screen.fill(SKY_BLUE)
    text = font.render(f"Уровень {level_number + 1}", True, BLACK)
    screen.blit(text, (WIDTH // 2 - 60, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.delay(2000)


def reset_game():
    global current_level, score, lives
    current_level = 0
    score = 0
    lives = 3
    load_level(current_level)
    show_level_transition(current_level)
    player.rect.topleft = (100, 500)
    player.vel_y = 0


load_level(current_level)
show_level_transition(current_level)

# Главный цикл
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()
            if event.key == pygame.K_ESCAPE:
                paused = not paused

    if not paused:
        keys = pygame.key.get_pressed()
        player.update(keys)

        platform_group.update()
        fireball_group.update()

        for coin in pygame.sprite.spritecollide(player, coin_group, True):
            score += 10
            if sound_enabled:
                coin_sound.play()

        current_interval = levels[current_level]["fireball_interval"]
        if pygame.time.get_ticks() - last_fireball_time > current_interval:
            x_pos = random.randint(0, WIDTH - 30)
            fireball_group.add(Fireball(x_pos))
            last_fireball_time = pygame.time.get_ticks()

        if pygame.sprite.spritecollide(player, fireball_group, True):
            if lives > 0:
                lives -= 1
                player.take_hit()
                player.rect.topleft = (100, 500)
            if lives <= 0:
                lives = 0
                show_game_over()
                running = False

        if not coin_group:
            if current_level < len(levels) - 1:
                current_level += 1
                show_level_transition(current_level)
                load_level(current_level)
                player.rect.topleft = (100, 500)
                player.vel_y = 0
                last_fireball_time = pygame.time.get_ticks()
            else:
                screen.fill(SKY_BLUE)
                screen.blit(font.render("🎉 ПОБЕДА! Все уровни пройдены!", True, BLACK),
                            (WIDTH // 2 - 200, HEIGHT // 2))
                pygame.display.flip()
                pygame.time.delay(3000)
                reset_game()

    screen.blit(BACKGROUND_IMG, (0, 0))
    platform_group.draw(screen)
    coin_group.draw(screen)
    fireball_group.draw(screen)
    player_group.draw(screen)
    draw_ui()
    pygame.display.flip()

pygame.quit()
sys.exit()
