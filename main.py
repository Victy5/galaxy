import random
from kivy.config import Config

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')

from kivy import platform
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import *
from kivy.properties import Clock
from kivy.graphics.context_instructions import *
from kivy.graphics.vertex_instructions import *
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.core.audio import SoundLoader

Builder.load_file("menu.kv")

class MainWidget(RelativeLayout):
    from transforms import transform, transform_2D, transform_perspective
    from user_control import keyboard_closed, on_keyboard_up, on_keyboard_down, on_touch_up, on_touch_down

    count_display = ObjectProperty()

    menu_widget = ObjectProperty()
    perspective_point_x = NumericProperty(0)  # for it to only accept numbers
    perspective_point_y = NumericProperty(0)

    V_NB_LINES = 8
    V_LINES_SPACING = .4  # percentage in screen width
    vertical_lines = []

    H_NB_LINES = 15
    H_LINES_SPACING = .2  # percentage in screen width
    horizontal_lines = []

    spd_val = .8  # smaller than the SPEED_X value
    SPEED = spd_val  # smaller than the SPEED_X value
    current_offset_y = 0
    current_y_loop = 0

    spd_x = 1.8
    SPEED_X = spd_x
    current_speed_x = 0
    current_offset_x = 0

    NB_TILES = 16
    tiles = []
    tiles_coordinates = []

    SHIP_WIDTH = .1
    SHIP_HEIGHT = .035
    SHIP_BASE_Y = .04
    ship = None
    ship_coordinates = [(0, 0), (0, 0), (0, 0)]

    state_game_over = False
    state_game_has_started = False
    paused = False

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_btn_title = StringProperty("START")
    score_txt = StringProperty()
    high_score_val = NumericProperty()
    high_score = StringProperty()

    sound_begin = None
    sound_galaxy = None
    sound_music1 = None
    sound_gameover_voice = None
    sound_restart = None
    sound_gameover_impact = None

    event = None
    difficult = None


    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        # print("INIT W:" + str(self.width)+" H:"+str(self.height))
        self.init_audio()
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.sound_galaxy.play()
        self.high_score_output()
        self.reset_game()

        # Keyboard
        if self.desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

        self.start_game()
        self.sound_galaxy.play()

    def start_game(self):
        self.event = Clock.schedule_interval(self.update, 1 / 60)
        self.difficult = Clock.schedule_interval(self.increase_difficulty, 60 / 2)

    def init_audio(self):
        self.sound_begin = SoundLoader.load("audio/begin.wav")
        self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
        self.sound_music1 = SoundLoader.load("audio/music1.wav")
        self.sound_gameover_voice = SoundLoader.load("audio/gameover_voice.wav")
        self.sound_restart = SoundLoader.load("audio/restart.wav")
        self.sound_gameover_impact = SoundLoader.load("audio/gameover_impact.wav")

        self.sound_begin.volume = 1
        self.sound_galaxy.volume = .25
        self.sound_music1.volume = .25
        self.sound_gameover_voice.volume = .25
        self.sound_restart.volume = .25
        self.sound_gameover_impact.volume = .6

    def reset_game(self):
        self.SPEED = self.spd_val
        self.SPEED_X = self.spd_x
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.current_offset_x = 0

        self.tiles_coordinates = []
        self.score_txt = "SCORE: " + str(self.current_y_loop)
        self.pre_fill_tiles_coordinate()
        self.generate_tiles_coordinates()
        self.state_game_over = False

    def desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def init_ship(self):
        with self.canvas:
            Color(1, 0, 0)
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width / 2
        base_y = self.SHIP_BASE_Y * self.height
        ship_half_width = self.SHIP_WIDTH * self.width / 2
        ship_height = self.SHIP_HEIGHT * self.height
        #   2
        # 1   3
        # self.transform

        self.ship_coordinates[0] = (center_x - ship_half_width, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)
        for i in range(0, 3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(0, 0, 1, .7)
            for i in range(0, self.NB_TILES):
                self.tiles.append(Quad())

    def pre_fill_tiles_coordinate(self):
        # 10 tiles in a straight line
        for i in range(0, 10):
            self.tiles_coordinates.append((0, i))

    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        # clean the coordinate that are out of the screen
        # ti_y  < self.current_y_loop
        for i in range(len(self.tiles_coordinates) - 1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1

        for i in range(len(self.tiles_coordinates), self.NB_TILES):
            r = random.randint(0, 2)
            # 0 -> straight
            # 1 -> right
            # 2 -> left
            start_index = -int(self.V_NB_LINES / 2) + 1
            end_index = start_index + self.V_NB_LINES - 1

            if last_x <= start_index:
                r = 1
            if last_x >= end_index:
                r = 2

            self.tiles_coordinates.append((last_x, last_y))
            if r == 1:  # right
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:  # left
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))

            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100])
            for i in range(0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        offset = index - 0.5
        line_x = central_line_x + offset * spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = self.H_LINES_SPACING * self.height
        line_y = index * spacing_y - self.current_offset_y
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):
        for i in range(0, self.NB_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0] + 1, tile_coordinates[1] + 1)

            # 2     3
            #
            # 1     4
            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_vertical_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1

        for i in range(start_index, start_index + self.V_NB_LINES):
            line_x = self.get_line_x_from_index(i)

            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[i].points = [x1, y1, x2, y2]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)
        for i in range(0, self.H_NB_LINES):
            line_y = self.get_line_y_from_index(i)
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]

    def pause_game(self):
        print("Paused")
        self.sound_music1.stop()
        self.menu_title = "P    A   U   S   E   D"
        self.menu_btn_title = "RESUME"
        if self.event:
            self.event.cancel()
            self.difficult.cancel()
            self.paused = True


        self.menu_widget.opacity = 1

    def resume_game(self):
        print("resumed")
        if self.paused:
            self.paused = False
            self.menu_widget.opacity = 0
            self.start_countdown()

    def start_countdown(self):
        overlay = CountDownDisplay()

        self.add_widget(overlay)
        overlay.start_countdown()
        Clock.schedule_once(self.after_cdwn, overlay.countdown_time+1)

    def after_cdwn(self, dt):
        self.sound_music1.play()
        self.start_game()

    def increase_difficulty(self, dt):
        print("speed: " + str(self.SPEED) + " movement speed: " + str(self.SPEED_X))
        if self.state_game_has_started:
            self.SPEED += 0.1
            self.SPEED_X += 0.5
            print("speed: " + str(self.SPEED) + " movement speed: " + str(self.SPEED_X))
        elif self.state_game_over:
            self.SPEED = self.spd_val
            self.SPEED_X = self.spd_x

    def high_score_output(self):
        def save_txt(text):
            with open('high_score.txt', 'w') as file:
                text = str(text)
                file.write(text)
                print("saved")

        def read_txt():
            try:
                with open('high_score.txt', 'r') as file:
                    content = file.read()
                    if content.isdigit() or (
                            content and content[0] == '-' and content[1:].isdigit()):  # Handles negative numbers
                        print("read from file")
                        return content
            except FileNotFoundError:
                return 0

        saved_score = read_txt()
        if self.current_y_loop >= int(saved_score):
            self.high_score_val = int(self.current_y_loop)
            self.high_score = "High Score: " + str(self.high_score_val)
            save_txt(self.high_score_val)
        else:
            self.high_score = "High Score: " + saved_score

    def update(self, dt):
        # print("delta Time: "+str(dt*60))
        time_factor = dt * 60
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        if not self.state_game_over and self.state_game_has_started:

            speed_y = self.SPEED * self.height / 100
            self.current_offset_y += speed_y * time_factor

            spacing_y = self.H_LINES_SPACING * self.height
            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.generate_tiles_coordinates()
                # print("loop : " + str(self.current_y_loop))
                self.score_txt = "SCORE: " + str(self.current_y_loop)

            speed_x = self.current_speed_x * self.width / 100
            self.current_offset_x += speed_x * time_factor

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.high_score_output()
            self.menu_title = "G  A  M  E    O  V  E  R"
            self.menu_btn_title = "RESTART"
            self.menu_widget.opacity = 1
            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            Clock.schedule_once(self.play_game_over_voice_sound, 3)
            print("GAME OVER")

    def play_game_over_voice_sound(self, dt):
        if self.state_game_over:
            self.sound_gameover_voice.play()

    def on_menu_button_pressed(self):
        print("Button")
        if self.paused is False:
            if self.state_game_over:
                self.sound_restart.play()
            else:
                self.sound_begin.play()
            self.sound_music1.loop = True
            self.sound_music1.play()
            self.reset_game()
            self.state_game_has_started = True
            self.menu_widget.opacity = 0
        else:
            self.resume_game()


class CountDownDisplay(BoxLayout):
    countdown_time = NumericProperty(3)  # Default countdown time
    opacity_value = NumericProperty(1)  # Opacity starts at 1 (fully visible)

    def on_touch_down(self, touch):
        return True

    def start_countdown(self):
        self.opacity_value = 0.5 # Reset opacity when countdown starts
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        if self.countdown_time > 0:
            self.countdown_time -= 1
            # self.opacity_value = self.countdown_time / 5.0  # Gradually decrease opacity
        else:
            Clock.unschedule(self.update_countdown)
            # self.opacity_value = 0  # Make overlay completely transparent
            parent = self.parent
            MainWidget.countdown_complete = True
            print("done")
            if parent:
                parent.remove_widget(self)



class SpaceDougeApp(App):
    pass


SpaceDougeApp().run()
