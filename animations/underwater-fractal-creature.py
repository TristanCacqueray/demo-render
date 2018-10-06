#!/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import numpy as np

from glumpy import gl, gloo
from glumpy.app.window import key

from utils import gamegl
from utils import animation
from utils.midi import MidiMod


vertex = """
attribute vec2 position;

void main (void)
{
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment = open("underwater-fractal-creature.glsl").read()


class Shader(gamegl.Window):
    def init_program(self):
        self.program = gloo.Program(vertex, fragment, count=4)
        self.program['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        # Render
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def render(self, dt):
        if not self.draw:
            return False

        self.window.clear()
        self.program["Julia"] = (
            self.params["jx"], self.params["jy"], self.params["jz"])
        self.program['pitch'] = self.params['pitch']
        self.program['yaw'] = self.params['yaw']
        self.program["zoom"] = self.params["zoom"]
        self.program["koff"] = self.params["koff"]
        self.program["view_y"] = self.params["view_y"]
        self.program["clamp_fix"] = self.params["cf"]
        self.program["swim_angle"] = self.params["kang"]
        self.program["Amplitude"] = self.params["amp"]
        self.program.draw(gl.GL_TRIANGLE_STRIP)
        self.draw = False
        return True

    def on_resize(self, width, height):
        self.program["size"] = width, height
        self.winsize = (width, height)
        self.draw = True

    def on_mouse_drag(self, x, y, dx, dy, button):
        self.params["pitch"] -= dy / 50
        self.params["yaw"] += dx / 50
        self.draw = True
        print(x, y, dx, dy, button)

    def on_mouse_scroll(self, x, y, dx, dy):
        x = (x - self.winsize[0] / 2) / self.winsize[0]
        y = (y - self.winsize[1] / 2) / self.winsize[1] * -1
        self.params["zoom"] += self.params["zoom"] / 10 * dy
        self.params["view_x"] += x * self.params["zoom"]
        self.params["view_y"] += y * self.params["zoom"]
        self.draw = True

    def on_key_press(self, k, modifiers):
        super().on_key_press(k, modifiers)
        s = 0.1
        if k == key.UP:
            self.params['amp'] += self.params["i_step"]
        if k == key.DOWN:
            self.params['amp'] -= self.params["i_step"]
        if k == key.LEFT:
            self.params['koff'] += self.params["r_step"]
        if k == key.RIGHT:
            self.params['koff'] -= self.params["r_step"]
        elif k == 69:
            self.params["cZ"] += s
        elif k == 81:
            self.params["cZ"] -= s
        elif k == 65:
            self.params["power"] += .1
        elif k == 68:
            self.params["power"] -= .1
        self.draw = True


params = {
    'pitch': 0,
    'yaw': 0,
    "zoom": 0.7,  # 1.0 / 250.0
    "view_x": 0,  # -0.53,
    "view_y": 0,  # 0.52,
    "c_real": -0.78,
    "c_imag": -0.14,
    "i_step": 0.1,
    "r_step": 0.1,
    "cf": 0.001,

    "jx": -3.,
    "jy": -1.5,
    "jz": -0.5,

    "amp": 0.5,
    "koff": 0,
    "kang": 0,

    "mods": {
        "jx": {
            "type": "float",
            "sliders": True,
            "min": -15,
            "max": 5,
            "resolution": 0.1,
        },
        "jy": {
            "type": "float",
            "sliders": True,
            "min": -5,
            "max": 5,
            "resolution": 0.1,
        },
        "jz": {
            "type": "float",
            "sliders": True,
            "min": -10,
            "max": 5,
            "resolution": 0.1,
        },
        "amp": {
            "type": "float",
            "sliders": True,
            "min": 0,
            "max": 2,
            "resolution": 0.01,
        }
    }
}


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [3000, None],
            [2624, self.ending],
            [2374, self.db2],
            [2124, self.brk2],
            [1625, self.db],
            [1375, self.brk],
            [874,  self.verse1],
            [624,  self.strings],
            [0,    self.intro],
        ]
        super().__init__(params)

    def ending(self, frame):
        if self.scene_init:
            self.a_mod = self.logspace(self.params["amp"], 0.69)
        self.params["amp"] = self.a_mod[self.scene_pos]
        self.params["zoom"] += 2e-3
        self.params["koff"] += 1e-2 * self.rhode

    def db2(self, frame):
        if self.scene_init:
            self.cf_mod = self.logspace(self.params["cf"], 0.001)
        self.params["cf"] = self.cf_mod[self.scene_pos]
        self.params["koff"] += .8e-1 * self.dbass
        self.params["amp"] += 1e-3 * self.bass
        self.params["pitch"] += .3e-2

    def brk2(self, frame):
        if self.scene_init:
            self.a_mod = self.logspace(self.params["amp"], 0.23)
        self.params["pitch"] += .3e-2
        self.params["jx"] -= 3.8e-2 * self.bass
        self.params["jy"] += 1.5e-2 * self.bass
        self.params["amp"] = self.a_mod[self.scene_pos]

    def db(self, frame):
        if self.scene_init:
            self.x_mod = self.logspace(self.params["jx"] + 20, -2.6 + 20)
            self.p_mod = self.logspace(self.params["pitch"] + 10, 0 + 10)
            self.z_mod = self.logspace(self.params["zoom"], 1.29)
        self.params["pitch"] = self.p_mod[self.scene_pos] - 10
        self.params["jx"] = self.x_mod[self.scene_pos] - 20
        self.params["zoom"] = self.z_mod[self.scene_pos]
        self.params["koff"] += 1e-1 * self.dbass
        self.params["amp"] -= 1e-3 * self.rhode

    def brk(self, frame):
        if self.scene_init:
            self.k_mod = self.linspace(
                self.params["koff"], self.params["koff"] + np.pi)
            self.cf_mod = self.logspace(self.params["cf"], 0.5)
        self.params["cf"] = self.cf_mod[self.scene_pos]
        self.params["koff"] = self.k_mod[self.scene_pos]
        self.params["jx"] += 1e-3 * self.rhode
        self.params["jz"] += 1e-3 * self.rhode
        self.params["amp"] += 1e-3 * self.rhode

    def verse1(self, frame):
        if self.scene_init:
            self.z_mod = self.logspace(self.params["zoom"], 1.71)
            self.a_mod = self.logspace(self.params["amp"], 0.1)
            self.p_mod = self.logspace(0.1, 1)
        self.params["amp"] -= (1e-3 * self.rhode + 1e-3 * self.snare)
        self.params["jy"] += 1e-2 * self.bass #+ 3e-2 * self.snare

    def strings(self, frame):
        if self.scene_init:
            self.p_mod = self.logspace(self.params["pitch"], 0.99)
            self.z_mod = self.logspace(self.params["zoom"], 1.61)
            self.view_mod = self.logspace(1, 10)
            self.base_y = self.params["jy"]
            self.y_mod = 0
        self.params["koff"] -= 1e-3 * self.rhode
        self.params["amp"] += 1e-3 * self.kick
        self.params["zoom"] = self.z_mod[self.scene_pos]
        self.params["jy"] -= 3e-1 * self.snare

    def intro(self, frame):
        if self.scene_init:
            self.params["yaw"] = -0.08
            self.params["pitch"] = np.pi / 2
            self.params["jx"] = -0.2
            self.params["jy"] = -2.6
            self.params["jz"] = 1.2
            self.params["amp"] = 0.1
            self.z_mod = self.linspace(0.005, 1.14)
        self.params["jx"] -= 4e-2 * self.rhode
        self.params["jz"] -= 2e-2 * self.string
        self.params["amp"] += 8e-3 * self.string
        self.params["zoom"] = self.z_mod[self.scene_pos]

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 0
        self.midi_events = {
            "dbass": MidiMod("DirtyBass", mod="one-off"),
            "bass": MidiMod("Rhodes bass", mod="one-off"),
            "rhode": MidiMod(["Rhodes mel"], mod="one-off", decay=20),
            "string": MidiMod("Strings", mod="one-off", decay=20),
            "kick": MidiMod("Kick", mod="one-off"),
            "snare": MidiMod("snare", mod="one-off"),
            "hats": MidiMod("Hats", mod="one-off"),
        }


if __name__ == "__main__":
    gamegl.run_main(Demo(), Shader)
