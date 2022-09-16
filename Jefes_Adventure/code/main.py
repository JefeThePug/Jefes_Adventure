import pygame as pg
import states as gs
from common import WIDTH, HEIGHT, FPS, SFX
from support import import_folder
from img import GameImages

pg.init()


class Backgrounds:
    """
    Initialize All Background Images
    """

    def __init__(self):
        # get all background images from file

        self.bgs = import_folder("../img/backgrounds", "image")

    def return_bg(self, type):
        """
        returns a single background for either the Title Screen or the Overworld
        """
        index_special = {"title": -1, "overworld": -2, "settings": -1}
        return self.bgs[index_special[type]]

    def return_bgs(self, start, end):
        """
        returns a list of backgrounds for the various levels
        """
        return self.bgs[start : end + 1]


class Music:
    """
    Initialize All Background Music and Sound Effects
    """

    def __init__(self):
        # get all background images from file
        self.music = import_folder("../audio/bgm", "music")

    def return_wav(self, type):
        """
        returns a single background for either the Title Screen or the Overworld
        """
        index_special = {"title": -1, "overworld": -2, "sbettings": -1}
        return self.music[index_special[type]]

    def return_wavs(self, start, end):
        """
        returns a list of backgrounds for the various levels
        """
        return self.music[start : end + 1]


class Game:
    """
    Manage Gamestates and Draw Screen
    """

    SCREEN_SIZE = (WIDTH, HEIGHT)
    CLOCK = pg.time.Clock()

    def __init__(self):
        self.screen = pg.display.set_mode(self.SCREEN_SIZE)
        pg.display.set_caption("Jefe's Adventure")

        # get collection of BG images & sounds
        self.bgs = Backgrounds()
        self.music = Music()
        self.imgs = GameImages("../img")

        # dictionary to assign background images to gamestates
        self.choose_bg = {
            gs.TitleScreen: "title",
            gs.LevelMenu: "overworld",
            gs.MainGame: [0, 1, 2, 3, 4, 5],
        }
        self.choose_wav = {
            gs.TitleScreen: "title",
            gs.LevelMenu: "overworld",
            gs.MainGame: [0, 1, 2, 5, 4, 5],
        }

        # Build first gamestate (the Title Screen)
        self.current_game_state = gs.TitleScreen(
            self.music.return_wav("title"),
            bg = self.bgs.return_bg("title"),
            imgs = self.imgs,
        )

    def get_events(self):
        """
        Returns necessary events for application. Packed in a dictionary.
        """
        events = pg.event.get()
        mouse_press = pg.mouse.get_pressed()
        keys = pg.key.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        raw_dt = self.CLOCK.get_time()
        dt = raw_dt * FPS

        return {
            "events": events,
            "mouse press": mouse_press,
            "keys": keys,
            "mouse pos": mouse_pos,
            "raw dt": raw_dt,
            "dt": dt,
        }

    def run(self):
        while True:
            level_info = None
            event_info = self.get_events()

            for event in event_info["events"]:
                if event.type == pg.QUIT:
                    SFX.close_all()
                    pg.quit()
                    raise SystemExit

            # get events for current gamestate
            self.current_game_state.update(event_info)


            if self.current_game_state.is_over:
                # find gamestate type
                new_state, level_info = self.current_game_state.next_game_state()

                # get gamestate bg image and music
                bg_index = self.choose_bg[new_state]
                if isinstance(bg_index, str):
                    bg = self.bgs.return_bg(bg_index)
                    wav = self.music.return_wav(self.choose_wav[new_state])
                else:
                    bg = self.bgs.return_bgs(0, 5)
                    wav = self.music.return_wavs(0, 5)

                # initialize new gamestate
                if level_info:
                    self.current_game_state = new_state(
                        level_info, wav, bg=bg, imgs=self.imgs
                    )
                else:
                    self.current_game_state = new_state(wav, bg=bg, imgs=self.imgs)

            # draw current gamestate
            self.current_game_state.draw(self.screen)
            self.CLOCK.tick(FPS)
            pg.display.update()


if __name__ == "__main__":
    game = Game()
    game.run()
