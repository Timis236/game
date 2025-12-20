import pygame
import math
import random
import sys
import time

# import of keys used in the game
from pygame.locals import (
    K_w,
    K_s,
    K_a,
    K_d,
    K_r,
    K_t,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_SPACE,
    K_LSHIFT,
    K_ESCAPE,
    K_KP0,
    KEYDOWN,
    QUIT,
)

# game modes
DEBUG = 1

# game properties
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
WORLD_LEFT_BOUND = -1000000000
WORLD_RIGHT_BOUND = 1000000000
PLAYER_WIDTH = 36
PLAYER_HEIGHT = 36
BLOCK_WIDTH = 10
BLOCK_HEIGHT = 10
FRAMES_PER_SECOND = 170
GRAVITY = 0.05

# calculated constants
PLAYER_UNIT_WIDTH = PLAYER_WIDTH / BLOCK_WIDTH
PLAYER_UNIT_HEIGHT = PLAYER_HEIGHT / BLOCK_HEIGHT
CHUNK_BLOCK_WIDTH = SCREEN_WIDTH // BLOCK_WIDTH
CHUNK_BLOCK_HEIGHT = SCREEN_HEIGHT // BLOCK_HEIGHT

# color constants
DAY_SKY = (153, 204, 255)
NIGHT_SKY = (0, 0, 51)

# defines the class Player with the parent class Sprite, where Sprite is a base class for any visible game object
class Player(pygame.sprite.Sprite):
    def __init__(self):
        # initialize the sprite when initializing the player
        super(Player, self).__init__()
        # define a Surface object for the player with dimensions 50x50, where a Surface is a base object for representing images
        self.surf = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        # fill the surface
        self.surf.fill((255, 153, 51))
        # defines a rectangle covering the entire defined surface, which is visible in the window and defaults to the position (0,0)
        self.rect = self.surf.get_rect()
        
        # static properties
        self.has_gravity = True
        self.demands_loading = True
        
        # dynamic properties
        self.is_jumping = False
        self.is_hanging = False
        self.attempted_jump = False
        
        self.left_collisions = []
        self.right_collisions = []
        self.top_collisions = []
        self.bottom_collisions = []
        
        # position variables
        self.x = 0
        self.y = 0
        
        self.raw_x = 0
        self.raw_y = 0
        self.dx = 0
        self.dy = 0
        
        self.current_chunk_x = 0
        self.current_chunk_y = 0
        
    # handle the movement of the player relative to their speed and interactions with other objects
    def handle_movement(self, world):
        # handle collision with terrain
        self.left_collisions = []
        self.right_collisions = []
        self.top_collisions = []
        self.bottom_collisions = []
        
        expected_raw_x = self.raw_x + self.dx
        expected_raw_y = self.raw_y + self.dy

        # find the potential collisions
        potential_collisions = []
        
        expected_unit_raw_x = expected_raw_x / BLOCK_WIDTH
        expected_unit_x_left = math.floor(expected_unit_raw_x)
        expected_unit_x_right = expected_unit_x_left + math.ceil(PLAYER_UNIT_WIDTH)
        
        expected_unit_frac_x = expected_unit_raw_x - math.floor(expected_unit_raw_x)
        player_unit_frac_x = PLAYER_UNIT_WIDTH - math.floor(PLAYER_UNIT_WIDTH)
        if expected_unit_frac_x > 1 - player_unit_frac_x:
            expected_unit_x_right += 1
        
        expected_unit_raw_y = expected_raw_y / BLOCK_HEIGHT
        expected_unit_y_top = math.floor(expected_unit_raw_y)
        expected_unit_y_bottom = expected_unit_y_top + math.ceil(PLAYER_UNIT_HEIGHT)
        
        expected_unit_frac_y = expected_unit_raw_y - math.floor(expected_unit_raw_y)
        player_unit_frac_y = PLAYER_UNIT_HEIGHT - math.floor(PLAYER_UNIT_HEIGHT)
        if expected_unit_frac_y > 1 - player_unit_frac_y:
            expected_unit_y_bottom += 1
            
        for i in range(expected_unit_x_left, expected_unit_x_right + 1):
            for j in range(expected_unit_y_top, expected_unit_y_bottom + 1):
                potential_collisions.append((i, j))

        # collision algorithm
        for t in potential_collisions:
            i = t[0] // CHUNK_BLOCK_WIDTH
            j = t[1] // CHUNK_BLOCK_HEIGHT
            k = t[0] % CHUNK_BLOCK_WIDTH
            l = t[1] % CHUNK_BLOCK_HEIGHT
            
            if world[i][j][k][l] != None and world[i][j][k][l].has_collision:
                if (expected_raw_x < world[i][j][k][l].x + BLOCK_WIDTH and expected_raw_x + PLAYER_WIDTH > world[i][j][k][l].x and expected_raw_y < world[i][j][k][l].y + BLOCK_HEIGHT and expected_raw_y + PLAYER_HEIGHT > world[i][j][k][l].y):
                    if (self.rect.top >= world[i][j][k][l].rect.bottom):
                        self.top_collisions.append(t)
                    if (self.rect.bottom <= world[i][j][k][l].rect.top):
                        self.bottom_collisions.append(t)
                    if (self.rect.left >= world[i][j][k][l].rect.right):
                        self.left_collisions.append(t)
                    if (self.rect.right <= world[i][j][k][l].rect.left):
                        self.right_collisions.append(t)
        
        collision_sizes = [len(self.top_collisions), len(self.bottom_collisions), len(self.left_collisions), len(self.right_collisions)]
        dominant_collision = collision_sizes.index(max(collision_sizes))
        if (dominant_collision == 0):   # top
            if len(self.top_collisions) > 0:
                values = []
                for t in self.top_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.bottom)
                self.rect.top = max(values)
                values = []
                for t in self.top_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].y)
                self.raw_y = max(values) + BLOCK_HEIGHT
                self.dy = 0
            
                # if collision is occurring on the same object at a perpendicular direction, ignore it (corner collision)
                for t in self.left_collisions.copy():
                    if t in self.top_collisions:
                        self.left_collisions.remove(t)
                for t in self.right_collisions.copy():
                    if t in self.top_collisions:
                        self.right_collisions.remove(t)
        
        if (dominant_collision == 1):   # bottom
            if len(self.bottom_collisions) > 0:
                values = []
                for t in self.bottom_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.top)
                self.rect.bottom = min(values)
                values = []
                for t in self.bottom_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].y)
                self.raw_y = min(values) - PLAYER_HEIGHT
                self.dy = 0
            
                # if collision is occurring on the same object at a perpendicular direction, ignore it (corner collision)
                for t in self.left_collisions.copy():
                    if t in self.bottom_collisions:
                        self.left_collisions.remove(t)
                for t in self.right_collisions.copy():
                    if t in self.bottom_collisions:
                        self.right_collisions.remove(t)
        
        if (dominant_collision == 2):   # left
            if len(self.left_collisions) > 0:
                values = []
                for t in self.left_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.right)
                self.rect.left = max(values)
                values = []
                for t in self.left_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].x)
                self.raw_x = max(values) + BLOCK_WIDTH
                self.dx = 0
            
                # if collision is occurring on the same object at a perpendicular direction, ignore it (corner collision)
                for t in self.top_collisions.copy():
                    if t in self.left_collisions:
                        self.top_collisions.remove(t)
                for t in self.bottom_collisions.copy():
                    if t in self.left_collisions:
                        self.bottom_collisions.remove(t)
        
        if (dominant_collision == 3):   # right
            if len(self.right_collisions) > 0:
                values = []
                for t in self.right_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.left)
                self.rect.right = min(values)
                values = []
                for t in self.right_collisions:
                    values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].x)
                self.raw_x = min(values) - PLAYER_WIDTH
                self.dx = 0
            
            # if collision is occurring on the same object at a perpendicular direction, ignore it (corner collision)
            for t in self.top_collisions.copy():
                if t in self.right_collisions:
                    self.top_collisions.remove(t)
            for t in self.bottom_collisions.copy():
                if t in self.right_collisions:
                    self.bottom_collisions.remove(t)
                    
        # handle all other collision directions after the dominant collisions have been considered
        if dominant_collision != 0 and len(self.top_collisions) > 0:    # only handle top collision here if it was not dominant
            values = []
            for t in self.top_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.bottom)
            self.rect.top = max(values)
            values = []
            for t in self.top_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].y)
            self.raw_y = max(values) + BLOCK_HEIGHT
            self.dy = 0
        
        if dominant_collision != 1 and len(self.bottom_collisions) > 0: # only handle bottom collision here if it was not dominant
            values = []
            for t in self.bottom_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.top)
            self.rect.bottom = min(values)
            values = []
            for t in self.bottom_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].y)
            self.raw_y = max(values) - PLAYER_HEIGHT
            self.dy = 0
        
        if dominant_collision != 2 and len(self.left_collisions) > 0:   # only handle left collision here if it was not dominant
            values = []
            for t in self.left_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.right)
            self.rect.left = max(values)
            values = []
            for t in self.left_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].x)
            self.raw_x = max(values) + BLOCK_WIDTH
            self.dx = 0
        
        if dominant_collision != 3 and len(self.right_collisions) > 0:  # only handle right collision here if it was not dominant
            values = []
            for t in self.right_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].rect.left)
            self.rect.right = min(values)
            values = []
            for t in self.right_collisions:
                values.append(world[t[0] // CHUNK_BLOCK_WIDTH][t[1] // CHUNK_BLOCK_HEIGHT][t[0] % CHUNK_BLOCK_WIDTH][t[1] % CHUNK_BLOCK_HEIGHT].x)
            self.raw_x = min(values) - PLAYER_WIDTH
            self.dx = 0

        if len(self.left_collisions) == 0 and len(self.right_collisions) == 0:
            self.raw_x += self.dx
        if len(self.top_collisions) == 0 and len(self.bottom_collisions) == 0:
            self.raw_y += self.dy

        # handle collision with world boundaries
        if math.floor(self.raw_x) < WORLD_LEFT_BOUND:
            self.rect.left = WORLD_LEFT_BOUND
            self.raw_x = WORLD_LEFT_BOUND
            self.dx = 0
        if math.ceil(self.raw_x + PLAYER_WIDTH) > WORLD_RIGHT_BOUND:
            self.rect.right = WORLD_RIGHT_BOUND
            self.raw_x = WORLD_RIGHT_BOUND - PLAYER_WIDTH
            self.dx = 0
        
        self.x = round(self.raw_x)
        self.y = round(self.raw_y)
        self.rect.update(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)
        
        self.current_chunk_x = (self.x + math.floor(PLAYER_WIDTH / 2)) // SCREEN_WIDTH
        self.current_chunk_y = (self.y + math.floor(PLAYER_HEIGHT / 2)) // SCREEN_HEIGHT

    # perform actions based on which keys are pressed
    def update_keys(self, pressed_keys):
        # horizontal movement
        if pressed_keys[K_a] and not pressed_keys[K_LSHIFT]:
            self.dx -= 0.05
            if self.dx < -2:
                self.dx = -2
        if pressed_keys[K_d] and not pressed_keys[K_LSHIFT]:
            self.dx += 0.05
            if self.dx > 2:
                self.dx = 2
        if pressed_keys[K_a] and pressed_keys[K_LSHIFT]:
            self.dx -= 0.05
            if self.dx < -1:
                self.dx = -1
        if pressed_keys[K_d] and pressed_keys[K_LSHIFT]:
            self.dx += 0.05
            if self.dx > 1:
                self.dx = 1
        if not pressed_keys[K_a] and not pressed_keys[K_d] or pressed_keys[K_a] and pressed_keys[K_d]:
            if self.dx > 0:
                self.dx -= 0.025
            if self.dx < 0:
                self.dx += 0.025
            if self.dx < 0.025 and self.dx > -0.025:
                self.dx = 0
            
        # vertical movement
        if pressed_keys[K_s]:
            self.dy += 2 * GRAVITY
        if pressed_keys[K_w]:
            if len(self.top_collisions) > 0:
                self.is_hanging = True
                self.is_jumping = False
                self.dy = -1
            else:
                self.is_hanging = False
        else:
            self.is_hanging = False
        if pressed_keys[K_SPACE]:
            if self.can_jump() and not self.is_jumping and not self.attempted_jump:
                self.is_jumping = True
                self.dy = -4
                if len(self.bottom_collisions) == 0:
                    if len(self.left_collisions) > 0 and len(self.right_collisions) == 0:
                        self.dx = 2
                    if len(self.right_collisions) > 0 and len(self.left_collisions) == 0:
                        self.dx = -2
            self.attempted_jump = True
            if self.dy >= 0:
                self.is_jumping = False
        else:
            self.is_jumping = False
            self.attempted_jump = False
            if self.dy < 0 and not self.is_hanging:
                self.dy = 0
    
    def can_jump(self):
        return len(self.bottom_collisions) > 0 or len(self.left_collisions) > 0 or len(self.right_collisions) > 0

# defines the class Terrain with the parent class Sprite, where Sprite is a base class for any visible game object
class Terrain(pygame.sprite.Sprite):
    def __init__(self, x, y, has_collision, rgb):
        # initialize the sprite when initializing the terrain
        super(Terrain, self).__init__()
        # define a Surface object for the terrain with dimensions 10x10, where a Surface is a base object for representing images
        self.surf = pygame.Surface((BLOCK_WIDTH, BLOCK_HEIGHT))
        # fill the surface with white
        self.surf.fill(rgb)
        # defines a rectangle covering the entire defined surface, which is visible in the window and defaults to the position (0,0)
        self.rect = self.surf.get_rect()
        # move the rectangle to the given coordinates in the world
        self.rect = self.rect.move(x, y)
        
        # set terrain properties
        self.x = x
        self.y = y
        self.has_collision = has_collision
        
def generate_chunk(x, y):
    chunk = [[None for i in range(CHUNK_BLOCK_HEIGHT)] for j in range(CHUNK_BLOCK_WIDTH)]
    
    for i in range(CHUNK_BLOCK_WIDTH):
        for j in range(CHUNK_BLOCK_HEIGHT):
            x_pos = i * BLOCK_WIDTH + x * SCREEN_WIDTH
            y_pos = j * BLOCK_HEIGHT + y * SCREEN_HEIGHT
            
            # ground
            if y_pos >= 1000:
                if chunk[i][j] == None:
                    chunk[i][j] = Terrain(x_pos, y_pos, True, (0, 200, 0))
                
            # hills
            if y_pos == 1000 and x_pos + 50 * BLOCK_WIDTH < (x + 1) * SCREEN_WIDTH and random.random() > 0.99:
                for k in range(10):
                    for l in range(k, 50 - k):
                        if chunk[i + l][j - (k + 1)] == None:
                            chunk[i + l][j - (k + 1)] = Terrain(x_pos + l * BLOCK_WIDTH, y_pos - (k + 1) * BLOCK_HEIGHT, True, (0, 200, 0))
                            
            # bridge
            
    
    return chunk
        
pygame.init()
pygame.display.set_caption('Game')
pygame.mouse.set_visible(True)

pygame.font.init()
font = pygame.font.SysFont("OCR-A Extended", 32)

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
clock = pygame.time.Clock()

camera_offset_x = 0
camera_offset_y = 0
camera_focus_x = 0
camera_focus_y = 0
camera_bias_x = 0
camera_bias_y = 0

mouse_x = 0
mouse_y = 0

obj_list = []
player = Player()
obj_list.append(player)

world = {}
chunk_surfaces = {}

# structures
#for i in range(3):
#    for j in range(50):
#        world.append(Terrain(2500 + i * 10, 990 - j * 10, True, True, 150, 75, 0))
#for i in range(3):
#    for j in range(30):
#        world.append(Terrain(4970 + i * 10, 990 - j * 10, False, True, 50, 25, 0))
#for i in range(206):
#    for j in range(3):
#        world.append(Terrain(4970 + i * 10, 690 - j * 10, True, True, 150, 75, 0))
#for i in range(3):
#    for j in range(30):
#        world.append(Terrain(7000 + i * 10, 990 - j * 10, False, True, 50, 25, 0))

# load background
background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
background.fill(DAY_SKY)

# stars   
for i in range(CHUNK_BLOCK_WIDTH):
    for j in range(CHUNK_BLOCK_HEIGHT):
        if (random.random() > 0.997):
            block = Terrain(i * BLOCK_WIDTH, j * BLOCK_HEIGHT, False, (255, 255, 255))
            background.blit(block.surf, block.rect)

# load the world
for obj in obj_list:
    if (obj.demands_loading):
        for i in range(obj.current_chunk_x - 1, obj.current_chunk_x + 2):
            for j in range(obj.current_chunk_y - 1, obj.current_chunk_y + 2):
                # create the chunk if it does not already exist
                if not i in world:
                    world[i] = {}
                    chunk_surfaces[i] = {}
                
                if not j in world[i]:
                    world[i][j] = None
                    chunk_surfaces[i][j] = None
                    
                if world[i][j] == None:
                    world[i][j] = generate_chunk(i, j)
                
                    # draw elements of the chunk onto the chunk surface
                    chunk_surfaces[i][j] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.SRCALPHA,32)
                    chunk_surfaces[i][j].convert_alpha()
                    
                    for k in range(CHUNK_BLOCK_WIDTH):
                        for l in range(CHUNK_BLOCK_HEIGHT):
                            if world[i][j][k][l] != None:
                                chunk_surfaces[i][j].blit(world[i][j][k][l].surf, world[i][j][k][l].rect.move(-i * SCREEN_WIDTH, -j * SCREEN_HEIGHT))

game_timer = 1

running = True
while running:
    # exiting the game with escape or closing the window
    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        elif event.type == QUIT:
            running = False
            
    # get mouse position for fun
    mouse_x = pygame.mouse.get_pos()[0] + camera_offset_x
    mouse_y = pygame.mouse.get_pos()[1] + camera_offset_y         
    
    # handle gravity
    for obj in obj_list:
        if (obj.has_gravity):
            obj.dy += GRAVITY
            if obj.dy > 10:
                obj.dy = 10

    # update player functions
    pressed_keys = pygame.key.get_pressed()
    player.update_keys(pressed_keys)
    player.handle_movement(world)
    
    if pressed_keys[K_r]:
        player.raw_x = 0
        player.raw_y = 0
        player.dx = 0
        player.dy = 0
        camera_offset_x = 0
        camera_offset_y = 0
        camera_focus_x = 0
        camera_focus_y = 0
    
    # handle screen scrolling based on player position
    if pressed_keys[K_a]:
        camera_focus_x += 1
        if not pressed_keys[K_LSHIFT]:
            if camera_focus_x == 101:
                camera_focus_x -= 1
            if camera_focus_x > 101:
                camera_focus_x -= 2
        else:
            if camera_focus_x == 51:
                camera_focus_x -= 1
            if camera_focus_x > 51:
                camera_focus_x -= 2
    if pressed_keys[K_d]:
        camera_focus_x -= 1
        if not pressed_keys[K_LSHIFT]:
            if camera_focus_x == -101:
                camera_focus_x += 1
            if camera_focus_x < -101:
                camera_focus_x += 2
        else:
            if camera_focus_x == -51:
                camera_focus_x += 1
            if camera_focus_x < -51:
                camera_focus_x += 2
    if player.dy < 0:
        camera_focus_y += 1
        if camera_focus_y > 50:
            camera_focus_y = 50
    if player.dy > 0:
        camera_focus_y -= 1
        if camera_focus_y < -50:
            camera_focus_y = -50
    if player.dx == 0 and not pressed_keys[K_a] and not pressed_keys[K_d]:
        if camera_focus_x > 0:
            camera_focus_x -= 2
        if camera_focus_x < 0:
            camera_focus_x += 2
    if (player.dy == 0):
        if camera_focus_y > 0:
            camera_focus_y -= 2
        if camera_focus_y < 0:
            camera_focus_y += 2
            
    # arrow key camera control
    if pressed_keys[K_UP]:
        camera_bias_y -= 3
        if camera_bias_y <= -300:
            camera_bias_y = -300
    if pressed_keys[K_DOWN]:
        camera_bias_y += 3
        if camera_bias_y >= 300:
            camera_bias_y = 300
    if pressed_keys[K_LEFT]:
        camera_bias_x -= 3
        if camera_bias_x <= -300:
            camera_bias_x = -300
    if pressed_keys[K_RIGHT]:
        camera_bias_x += 3
        if camera_bias_x >= 300:
            camera_bias_x = 300
    if pressed_keys[K_KP0]:
        camera_bias_x = 0
        camera_bias_y = 0
        
    # apply camera changes to the main camera offset for proper display
    camera_offset_x = player.x - (SCREEN_WIDTH // 2) + (PLAYER_WIDTH // 2) - camera_focus_x + camera_bias_x
    camera_offset_y = player.y - (SCREEN_HEIGHT // 2) + (PLAYER_HEIGHT // 2) - camera_focus_y + camera_bias_y
    if camera_offset_x < WORLD_LEFT_BOUND:
        camera_offset_x = WORLD_LEFT_BOUND
    if camera_offset_x > WORLD_RIGHT_BOUND - SCREEN_WIDTH:
        camera_offset_x = WORLD_RIGHT_BOUND - SCREEN_WIDTH

    # redraw background screen elements
    screen.blit(background, background.get_rect())
    
    # handle world changes via mouse (mouse1 -> place block, mouse2 -> remove block)
    mouse_pressed = pygame.mouse.get_pressed(num_buttons=3)
    i = mouse_x // SCREEN_WIDTH
    j = mouse_y // SCREEN_HEIGHT
    k = (mouse_x % SCREEN_WIDTH) // BLOCK_WIDTH
    l = (mouse_y % SCREEN_HEIGHT) // BLOCK_HEIGHT
    if mouse_pressed[0] and world[i][j][k][l] == None:
        world[i][j][k][l] = Terrain((mouse_x // BLOCK_WIDTH) * BLOCK_WIDTH, (mouse_y // BLOCK_HEIGHT) * BLOCK_HEIGHT, True, (0, 200, 0))
        
        chunk_surfaces[i][j] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.SRCALPHA,32)
        chunk_surfaces[i][j].convert_alpha()
        for k in range(CHUNK_BLOCK_WIDTH):
            for l in range(CHUNK_BLOCK_HEIGHT):
                if world[i][j][k][l] != None:
                    chunk_surfaces[i][j].blit(world[i][j][k][l].surf, world[i][j][k][l].rect.move(-i * SCREEN_WIDTH, -j * SCREEN_HEIGHT))
    if mouse_pressed[2] and world[i][j][k][l] != None:
        world[i][j][k][l] = None
        
        chunk_surfaces[i][j] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.SRCALPHA,32)
        chunk_surfaces[i][j].convert_alpha()
        for k in range(CHUNK_BLOCK_WIDTH):
            for l in range(CHUNK_BLOCK_HEIGHT):
                if world[i][j][k][l] != None:
                    chunk_surfaces[i][j].blit(world[i][j][k][l].surf, world[i][j][k][l].rect.move(-i * SCREEN_WIDTH, -j * SCREEN_HEIGHT))
    
    # redraw screen elements (world)
    for obj in obj_list:
        if (obj.demands_loading):
            for i in range(obj.current_chunk_x - 1, obj.current_chunk_x + 2):
                for j in range(obj.current_chunk_y - 1, obj.current_chunk_y + 2):
                    # create the chunk if it does not already exist
                    if not i in world:
                        world[i] = {}
                        chunk_surfaces[i] = {}
                    
                    if not j in world[i]:
                        world[i][j] = None
                        chunk_surfaces[i][j] = None
                    
                    if world[i][j] == None:
                        world[i][j] = generate_chunk(i, j)
                    
                        # draw elements of the chunk onto the chunk surface
                        chunk_surfaces[i][j] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.SRCALPHA,32)
                        chunk_surfaces[i][j].convert_alpha()
                        
                        for k in range(CHUNK_BLOCK_WIDTH):
                            for l in range(CHUNK_BLOCK_HEIGHT):
                                if world[i][j][k][l] != None:
                                    chunk_surfaces[i][j].blit(world[i][j][k][l].surf, world[i][j][k][l].rect.move(-i * SCREEN_WIDTH, -j * SCREEN_HEIGHT))
                    
                    # render the chunk surface
                    screen.blit(chunk_surfaces[i][j], (i*SCREEN_WIDTH-camera_offset_x, j*SCREEN_HEIGHT-camera_offset_y))
    
    # redraw objects
    screen.blit(player.surf, player.rect.copy().move(-camera_offset_x, -camera_offset_y))

    # create and draw debug text
    if (DEBUG):
        x_text = font.render("X: " + str(player.raw_x), False, (255, 255, 255))
        y_text = font.render("Y: " + str(player.raw_y), False, (255, 255, 255))
        dx_text = font.render("DX: " + str(player.dx), False, (255, 255, 255))
        dy_text = font.render("DY: " + str(player.dy), False, (255, 255, 255))
        lcol_text = font.render("LEFT COLLISION: " + str(player.left_collisions), False, (255, 255, 255))
        rcol_text = font.render("RIGHT COLLISION: " + str(player.right_collisions), False, (255, 255, 255))
        tcol_text = font.render("TOP COLLISION: " + str(player.top_collisions), False, (255, 255, 255))
        bcol_text = font.render("BOTTOM COLLISION: " + str(player.bottom_collisions), False, (255, 255, 255))
        cox_text = font.render("XCAM OFFSET: " + str(camera_offset_x), False, (255, 255, 255))
        coy_text = font.render("YCAM OFFSET: " + str(camera_offset_y), False, (255, 255, 255))
        cfx_text = font.render("XCAM FOCUS: " + str(camera_focus_x), False, (255, 255, 255))
        cfy_text = font.render("YCAM FOCUS: " + str(camera_focus_y), False, (255, 255, 255))
        mx_text = font.render("MOUSE X: " + str(mouse_x), False, (255, 255, 255))
        my_text = font.render("MOUSE Y: " + str(mouse_y), False, (255, 255, 255))
        gt_text = font.render("GAME TIMER: " + str(game_timer), False, (255, 255, 255))
        cc_text = font.render("CURRENT CHUNK: (" + str(player.current_chunk_x) + ", " + str(player.current_chunk_y) + ")", False, (255, 255, 255))
        
        screen.blit(x_text, (0, 0))
        screen.blit(y_text, (0, 32))
        screen.blit(dx_text, (0, 64))
        screen.blit(dy_text, (0, 96))
        screen.blit(lcol_text, (0, 128))
        screen.blit(rcol_text, (0, 160))
        screen.blit(tcol_text, (0, 192))
        screen.blit(bcol_text, (0, 224))
        screen.blit(cox_text, (0, 256))
        screen.blit(coy_text, (0, 288))
        screen.blit(cfx_text, (0, 320))
        screen.blit(cfy_text, (0, 352))
        screen.blit(mx_text, (0, 384))
        screen.blit(my_text, (0, 416))
        screen.blit(gt_text, (0, 448))
        screen.blit(cc_text, (0, 480))
    
    # update display and maintain max fps
    pygame.display.flip()
    clock.tick(FRAMES_PER_SECOND)
    game_timer += 1

pygame.quit()