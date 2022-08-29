import pygame as pg
from instructions import instructions, instructions_jp


class Button:
    def __init__(self, pos, frames, state = "unlocked"):
        self.pos = pos

        # images
        self.frames = frames
        self.frame_index = 0
        if isinstance(self.frames, list):
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect(topleft=pos)
            self.tint = self.image.copy()
            self.tint.fill((200, 200, 200), None, pg.BLEND_RGB_MAX)

        # conditions
        self.hover = False
        self.state = state
        self.clicked = False

    def update(self, event_info):
        if self.state != "locked":
            self.hover = self.rect.collidepoint(event_info["mouse pos"])
            for event in event_info["events"]:
                if self.hover and event.type == pg.MOUSEBUTTONDOWN:
                    self.clicked = True

    def draw(self, display_screen):
        if self.state == "locked":
            display_screen.blit(self.tint, self.pos)
        else:
            display_screen.blit(self.image, self.pos)


class AnimatedButton(Button):
    def __init__(self, pos, frames, state):
        super().__init__(pos, frames, state)
        self.animation_speed = 0.05
        self.always_on = False

    def update(self, event_info):
        super().update(event_info)
        if self.state == "unlocked" and (self.always_on or self.hover):
            self.animate()
        else:
            self.frame_index = 0
            self.image = self.frames[self.frame_index]

    def animate(self):
        self.frame_index = (self.frame_index + self.animation_speed) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]


class SwitchButton(Button):
    def update(self, event_info):
        super().update(event_info)
        self.frame_index = int(self.hover)
        self.image = self.frames[self.frame_index]

class ToggleButton(Button):
    def __init__(self, pos, frames, toggle_index=0):
        super().__init__(pos, frames["A"], "unlocked")

        # images
        self.frames = {0:frames["A"], 1:frames["B"]}
        self.toggle_index = toggle_index
        self.frame_index = 0
        self.image = self.frames[self.toggle_index][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)

    def switch(self):
        self.toggle_index = abs(self.toggle_index - 1)
        self.image = self.frames[self.toggle_index][self.frame_index]

    def update(self, event_info):
        super().update(event_info)
        self.frame_index = int(self.hover)
        self.image = self.frames[self.toggle_index][self.frame_index]


class AnimatedUI(AnimatedButton):
    def __init__(self, pos, path):
        super().__init__(pos, path, "unlocked")
        self.hover = True


class Indicator:
    def __init__(self, pos, path):
        self.pos = pos
        self.indicator = AnimatedUI(pos, path["indicator"])

    def update(self, event_info):
        self.indicator.update(event_info)

    def draw(self, display_screen):
        self.indicator.draw(display_screen)


class Bar(Indicator):
    def __init__(self, pos, path):
        super().__init__(pos, path)
        self.bar = path["bar"]
        self.gel = path["gel"]
        self.current = 1
        self.indicator.always_on = True

    def update(self, event_info, current):
        super().update(event_info)
        self.current = current / 100

    def draw(self, display_screen):
        bar_position = self.pos + pg.math.Vector2(15, 8)
        gel_fill = min(self.gel.get_width(), int(self.gel.get_width() * self.current))
        display_screen.blit(self.bar, bar_position)
        subsurface = self.gel.subsurface((0, 0, gel_fill, self.gel.get_height()))
        display_screen.blit(subsurface, bar_position)
        self.indicator.draw(display_screen)


class BoneIndicator(Indicator):
    def __init__(self, pos, path):
        super().__init__(pos, path)
        self.num_bones = 0
        self.font = pg.font.Font("../assets/bubblebutt.ttf", 50)

    def update(self, event_info, num):
        super().update(event_info)
        self.num_bones = num
        if self.num_bones >= 10:
            self.indicator.always_on = True

    def draw(self, display_screen):
        super().draw(display_screen)
        if self.num_bones >= 10:
            color = "#11d113"
        else:
            color = "#d68232"
        bone_amount_surface = self.font.render(str(self.num_bones), True, color)
        bone_amount_rect = bone_amount_surface.get_rect(
            topleft=self.indicator.rect.topright
        )
        bone_amount_rect.center += pg.math.Vector2(8, -12)
        display_screen.blit(bone_amount_surface, bone_amount_rect)


class HelpText:
    def __init__(self, pos, level, tile_size, img):
        self.image = img
        self.image_rect = self.image.get_rect(topleft=pos)
        self.image_rect.x -= tile_size
        self.image_rect.y -= tile_size * 0.5

        with open('../assets/settings.json', 'r') as f:
            lang = json.load(f)["language"]

        fonts = [
            {"font": pg.font.Font("../assets/helptext.ttf", 46), "file": instructions},
            {"font": pg.font.Font("../assets/craftmincho.otf", 44), "file": instructions_jp}]

        line_one, line_two = fonts[lang][file][level - 1].split("\n")
        color = (100, 80, 0)
        self.text = fonts[lang]["font"].render(line_one, True, color)
        self.text2 = fonts[lang]["font"].render(line_two, True, color)
        self.rect = self.text.get_rect(topleft=pos)
        self.rect.x += 10
        self.rect.y += tile_size
        self.rect2 = self.text.get_rect(topleft=pos)
        self.rect2.x += 10
        self.rect2.y += tile_size * 2

    def update(self, event_info, x_shift):
        self.image_rect.x += x_shift
        self.rect.x += x_shift
        self.rect2.x += x_shift

    def draw(self, display_screen):
        display_screen.blit(self.image, self.image_rect)
        display_screen.blit(self.text, self.rect)
        display_screen.blit(self.text2, self.rect2)
