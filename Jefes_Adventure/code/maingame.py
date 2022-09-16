import pygame as pg
import states as gs
import json
from common import WIDTH, HEIGHT, TILE_SIZE, SFX
from support import import_csv, import_cut_graphic
from ui import SwitchButton, Bar, BoneIndicator, HelpText
from gamestate import GameState
from player import Player
from tiles import *
from enemy import Enemy
from particles import ParticleEffect
from settingsmenu import SettingsMenu

DECOTYPE = {
    0: {"decorations":"bush", "danger":"cactus", "enemies":"alien"}, 
    1: {"decorations":"grass", "danger":"water", "enemies":"bee"}, 
    2: {"decorations":"mushroom", "danger":"spikes", "enemies":"frog"}, 
    3: {"decorations":"leaves", "danger":"", "enemies":"green_blob"}, 
    4: {"decorations":"mushroom", "danger":"", "enemies":"ice_blob"}, 
    5: {"decorations":"palm*", "danger":"", "enemies":"mouse"}, 
    6: {"decorations":"sand_castle", "danger":"", "enemies":"penguin"}, 
    7: {"decorations":"snow_pile", "danger":"", "enemies":"sandworm"}, 
    8: {"decorations":"snowman*", "danger":"", "enemies":"snail"}, 
    9: {"decorations":"tree*", "danger":"", "enemies":"snake"}, 
    10: {"decorations":"", "danger":"", "enemies":"worm"},
}

class MainGame(GameState):
    def __init__(self, level_code, music, **assets):

        # level setup
        super().__init__(music, **assets)
        self.stage, self.level = level_code
        self.stage = max(0, self.stage)
        self.music[self.stage].play(loops=-1)
        self.music[self.stage].set_volume(0.4)
        self.imgs = assets["imgs"]

        # game-over variables
        with open("../assets/save.json", "r") as f:
            save_data = json.load(f)
        max_level = save_data["max_level"] + 1
        if max_level > 8:
            max_level = 1
            max_stage = min(5, save_data["max_stage"] + 1)
        else:
            max_stage = save_data["max_stage"]
        self.opened_level = (max_stage, max_level)

        # movement help
        self.world_shift = 0

        # player initialization
        self.player = pg.sprite.GroupSingle()
        self.goal = pg.sprite.GroupSingle()
        # ※ player and goal are set up in the Gates Setup ※
        self.current_health = 100

        # dust
        self.particle_sprite = pg.sprite.GroupSingle()
        self.player_on_ground = False
        self.player_on_platform = False
        self.enemy_dust = pg.sprite.Group()

        # setup tile sprites
        self.setup_sprites()

        # setup UI indicators
        self.health_bar = Bar((5, 5), self.imgs.ui["bars"]["health"])
        self.bone_bar = BoneIndicator((42, 42), self.imgs.ui["bars"]["bones"])

        # setup buttons
        pause_btn = SwitchButton(
            (WIDTH - 100, 0), self.imgs.ui["buttons"]["pause"], "unlocked"
        )
        self.buttons = {
            "pause": {"state": None, "obj": pause_btn},
        }

        # settings menu sprite
        self.settings = pg.sprite.GroupSingle()
        self.override_state = None

        # setup help text
        if self.stage == 0:
            self.help_text = HelpText(
                (TILE_SIZE, TILE_SIZE * 7),
                self.level,
                TILE_SIZE,
                self.imgs.ui["scroll"],
            )

    def create_tilegroup(self, layout, tile_type):
        sprite_group = pg.sprite.Group()
        for row_index, row in enumerate(layout):
            for col_index, value in enumerate(row):
                if value == -1: continue
                x, y = [(col_index - 4) * TILE_SIZE, row_index * TILE_SIZE]
                if tile_type == "ground":
                    ground_tiles = import_cut_graphic(self.imgs.ground["ground"])
                    tile_surface = ground_tiles[value]
                    if (value % 4) < 2:
                        sprite = FloatingTile((x, y), TILE_SIZE, tile_surface)
                    else:
                        sprite = StaticTile((x, y), TILE_SIZE, tile_surface)
                elif tile_type == "decorations":
                    if value in [5,8,9]: y -= TILE_SIZE
                    sprite = AnimatedTile(
                        (x, y), TILE_SIZE, self.imgs.decorations[DECOTYPE[value][tile_type]]
                    )
                elif tile_type == "danger":
                    sprite = TrapTile(
                        (x, y), TILE_SIZE, self.imgs.dangers[DECOTYPE[value][tile_type]]
                    )
                elif tile_type == "bones":
                    sprite = BoneTile((x, y), TILE_SIZE, self.imgs.food["bones"])
                elif tile_type == "enemies":
                    sprite = Enemy(
                        (x, y), TILE_SIZE, self.imgs.enemies[DECOTYPE[value][tile_type]]
                    )
                elif "barrier" in tile_type:
                    sprite = Tile((x, y), TILE_SIZE)
                elif tile_type == "gates":
                    if value == 1:
                        # Create goal at exit gate
                        sprite = ExitTile(
                            (x, y),
                            TILE_SIZE,
                            self.imgs.gates["exit"],
                            self.player.sprite,
                        )
                        self.goal.add(sprite)
                        continue
                    else:
                        sprite = InvisibleTile(
                            (x, y), TILE_SIZE, self.imgs.gates["start"]
                        )

                        # Create player at start gate
                        player_sprite = Player(
                            (x + TILE_SIZE / 2, y - TILE_SIZE / 2),
                            self.imgs.pug,
                            self.create_action_sprite,
                        )  #                                self.sfx,
                        self.player.add(player_sprite)
                elif tile_type == "treasures":
                    sprite = TreasureTile(
                        (x, y), TILE_SIZE, self.imgs.treasure, self.player.sprite
                    )
                elif "platforms" in tile_type:
                    ground_tiles = import_cut_graphic(self.imgs.ground["ground"])
                    tile_surface = ground_tiles[value]
                    sprite = MovingPlatform(
                        (x, y), TILE_SIZE, tile_surface, "horizontal" in tile_type
                    )
                sprite_group.add(sprite)
        return sprite_group

    def setup_sprites(self):
        with open("../assets/game_levels.json", "r") as f:
            game_levels = json.load(f)
        level_data = game_levels[str(self.stage)][str(self.level)]
        # ground setup
        ground_layout = import_csv(level_data["ground"])
        self.ground_sprites = self.create_tilegroup(ground_layout, "ground")
        # moving platform setup
        moving_plat_layout = import_csv(level_data["horizontal_platforms"])
        self.plat_sprites = self.create_tilegroup(moving_plat_layout, "horizontal_platforms")
        moving_plat_layout = import_csv(level_data["vertical_platforms"])
        vp = self.create_tilegroup(moving_plat_layout, "vertical_platforms")
        self.plat_sprites.add(vp.sprites())
        # decoration setup
        decoration_layout = import_csv(level_data["decorations"])
        self.decoration_sprites = self.create_tilegroup(decoration_layout, "decorations")
        # bones setup
        bones_layout = import_csv(level_data["bones"])
        self.bone_sprites = self.create_tilegroup(bones_layout, "bones")
        # dangers setup
        dangers_layout = import_csv(level_data["danger"])
        self.danger_sprites = self.create_tilegroup(dangers_layout, "danger")
        # gates setup
        gates_layout = import_csv(level_data["gates"])
        self.gate_sprites = self.create_tilegroup(gates_layout, "gates")
        # treasures setup
        treasures_layout = import_csv(level_data["treasures"])
        self.treasure_sprites = self.create_tilegroup(treasures_layout, "treasures")
        # enemies setup
        enemy_layout = import_csv(level_data["enemies"])
        self.enemy_sprites = self.create_tilegroup(enemy_layout, "enemies")
        # enemy barrier setup
        enemy_barrier_layout = import_csv(level_data["enemy_barrier"])
        self.enemy_barrier_sprites = self.create_tilegroup(enemy_barrier_layout, "enemy_barrier")
        # moving platform barrier setup
        plat_barrier_layout = import_csv(level_data["platform_barrier"])
        self.plat_barrier_sprites = self.create_tilegroup(plat_barrier_layout, "platform_barrier")
        # off-stage barrier setup
        player_barrier_layout = import_csv(level_data["player_barrier"])
        self.player_barrier_sprites = self.create_tilegroup(player_barrier_layout, "player_barrier")

    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < WIDTH / 3 and direction_x < 0:  # Left side of the screen
            self.world_shift = 5
            player.speed = 0
        elif player_x > 2 * WIDTH / 3 and direction_x > 0:  # Right side of the screen
            self.world_shift = -5
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 5

    def create_action_sprite(self, pos, type):
        if type == "jump":
            v = pg.math.Vector2(10, 5)
        elif type == "bark":
            v = pg.math.Vector2(-35, 12)
        else:  # type == "dig"
            v = pg.math.Vector2(-20, 5)

        if self.player.sprite.facing_right:
            pos -= v
        else:
            v.y *= -1
            pos += v

        particle_sprite = ParticleEffect(
            pos, self.imgs.pug["dust_particles"][type], self.player.sprite
        )
        self.particle_sprite.add(particle_sprite)

    def get_player_on_ground(self):
        # determine if player is on ground before action
        self.player_on_ground = self.player.sprite.on_ground

    def create_landing_dust(self):
        if self.player_on_platform: return
        if not self.player_on_ground and self.player.sprite.on_ground:
            if self.player.sprite.facing_right:
                offset = pg.math.Vector2(10, 15)
            else:
                offset = pg.math.Vector2(-10, 15)
            fall_dust_particle = ParticleEffect(
                self.player.sprite.rect.midbottom - offset,
                self.imgs.pug["dust_particles"]["land"],
            )
            self.particle_sprite.add(fall_dust_particle)

    def horizontal_movement_collision(self):
        player = self.player.sprite
        player.hit_rect.x += player.direction.x * player.speed

        for sprite in (
            self.ground_sprites.sprites() + self.player_barrier_sprites.sprites() + self.plat_sprites.sprites()
            ):
            if sprite.rect.colliderect(player.hit_rect):
                if player.direction.x < 0:
                    player.hit_rect.left = sprite.rect.right
                elif player.direction.x > 0:
                    player.hit_rect.right = sprite.rect.left

    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()

        for sprite in (
            self.ground_sprites.sprites() + self.treasure_sprites.sprites()
        ):
            if sprite.rect.colliderect(player.hit_rect):
                if player.direction.y > 0:
                    player.hit_rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                    self.player_on_ground = True
                elif player.direction.y < 0:
                    player.hit_rect.top = sprite.rect.bottom
                    player.direction.y = 0

        for sprite in self.plat_sprites.sprites():
            if sprite.rect.colliderect(player.hit_rect):
                if player.direction.y > 0:
                    self.player_on_platform = True
                    player.hit_rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                    if sprite.is_horizontal:

                        player.hit_rect.x += sprite.speed * 0.5 * ((self.world_shift*-1) or player.speed)
                        player.direction.x = sprite.speed
                        #player.hit_rect.x += sprite.speed * player.speed * player.direction.x * self.world_shift
                elif player.direction.y < 0:
                    player.hit_rect.top = sprite.rect.bottom
                    player.direction.y = 0

        if player.on_ground and player.direction.y < 0 or player.direction.y > 1:
            player.on_ground = False
            player.on_platform = False

    def check_bones(self):
        bones_hit = len(
            pg.sprite.spritecollide(self.player.sprite, self.bone_sprites, True)
        )
        if bones_hit:
            SFX.play_sfx("gulp")
            self.player.sprite.bones += bones_hit

    def reverse_enemies(self):
        for enemy in self.enemy_sprites.sprites():
            if pg.sprite.spritecollide(enemy, self.enemy_barrier_sprites, False):
                enemy.reverse()

    def reverse_platforms(self):
        for platform in self.plat_sprites.sprites():
            if pg.sprite.spritecollide(platform, self.plat_barrier_sprites, False):
                platform.reverse()

    def next_game_state(self):
        self.music[self.stage].stop()

        if self.override_state:
            if self.override_state is gs.MainGame:
                return self.override_state, (self.stage, self.level)
            return self.override_state, None

    def check_enemy_death(self):
        for enemy in self.enemy_sprites.sprites():
            if abs(self.player.sprite.rect.centery - enemy.rect.centery) > TILE_SIZE: continue
            bark_range = abs(self.player.sprite.rect.centerx - enemy.rect.centerx)
            if self.player.sprite.barking and bark_range < 100:
                self.enemy_dust.add(
                    ParticleEffect(enemy.rect.center, self.imgs.enemies["explosion"])
                )
                enemy.kill()

    def bad_collision(self):
        damage = self.player.sprite.get_damage()
        if damage:
            self.current_health += damage

    def check_fail(self):
        if pg.sprite.spritecollide(self.player.sprite, self.danger_sprites, False):
            self.bad_collision()
        if pg.sprite.spritecollide(self.player.sprite, self.enemy_sprites, False):
            self.bad_collision()

        if self.player.sprite.rect.top > HEIGHT or self.current_health <= 0:
            self.override_state = gs.LevelMenu
            self.is_over = True

    def check_win(self):
        if self.goal.sprite.is_open:
            if pg.sprite.spritecollide(self.player.sprite, self.goal, False):
                max_stage, max_level = self.opened_level
                with open("../assets/save.json", "r+") as f:
                    save_data = json.load(f)
                    f.seek(0)
                    if (
                        save_data["max_stage"] == self.stage
                        and save_data["max_level"] == self.level
                    ):
                        json.dump({"max_stage": max_stage, "max_level": max_level}, f)
                self.override_state = gs.LevelMenu
                self.is_over = True 

    def update(self, event_info):
        self.scroll_x()

        # tile updates
        self.player_barrier_sprites.update(self.world_shift)
        self.particle_sprite.update(self.world_shift)
        self.ground_sprites.update(self.world_shift)
        self.plat_sprites.update(self.world_shift)
        self.decoration_sprites.update(self.world_shift)
        self.gate_sprites.update(self.world_shift)
        self.bone_sprites.update(self.world_shift)
        self.danger_sprites.update(self.world_shift)
        self.check_enemy_death()
        self.enemy_dust.update(self.world_shift)
        self.enemy_sprites.update(self.world_shift)
        self.plat_barrier_sprites.update(self.world_shift)
        self.enemy_barrier_sprites.update(self.world_shift)
        self.goal.update(self.world_shift)

        self.reverse_enemies()
        self.reverse_platforms()

        self.horizontal_movement_collision()
        self.get_player_on_ground()  # on ground before collision
        self.vertical_movement_collision()
        self.create_landing_dust()  # on ground after collision

        # check game over
        self.check_win()
        self.check_fail()

        # update ui
        self.health_bar.update(event_info, self.current_health)
        self.bone_bar.update(event_info, self.player.sprite.bones)
        if self.stage == 0:
            self.help_text.update(event_info, self.world_shift)

        # settings update

        for _, button in self.buttons.items():
            button["obj"].update(event_info)
            if button["obj"].clicked:
                self.settings.add(SettingsMenu(True, imgs=self.imgs))
                button["obj"].clicked = False

        if self.settings.sprite:
            self.override_state = self.settings.sprite.update(event_info)

        if self.override_state:
            self.is_over = True

    def draw(self, display_screen):
        display_screen.blit(self.bg[self.stage], (0, 0))
        display_screen.blit(self.bg[self.stage], (WIDTH / 2, 0))

        self.treasure_sprites.update(self.world_shift, display_screen)

        # draw tiles behind player
        self.decoration_sprites.draw(display_screen)
        self.gate_sprites.draw(display_screen)
        self.goal.draw(display_screen)
        self.treasure_sprites.draw(display_screen)
        self.bone_sprites.draw(display_screen)
        self.particle_sprite.draw(display_screen)
        self.ground_sprites.draw(display_screen)
        self.plat_sprites.draw(display_screen)
        self.enemy_dust.draw(display_screen)
        

        self.player.update(display_screen)
        self.check_bones()

        # player
        self.player.draw(display_screen)

        # draw tiles in front of player
        self.danger_sprites.draw(display_screen)
        self.enemy_sprites.draw(display_screen)

        # draw buttons
        for _, data in self.buttons.items():
            data["obj"].draw(display_screen)

        # draw UI
        self.health_bar.draw(display_screen)
        self.bone_bar.draw(display_screen)
        if self.stage == 0:
            self.help_text.draw(display_screen)
        if self.settings.sprite:
            self.settings.sprite.draw(display_screen)
        print(self.player_on_ground)
