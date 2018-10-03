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
from utils import audio
from utils.midi import MidiMod


vertex = """
attribute vec2 position;

void main (void)
{
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment = open("bulb.glsl").read()

p = 8


class MandelBulb(gamegl.Window):
    def init_program(self):
        self.program = gloo.Program(vertex, fragment, count=4)
        self.program['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        if self.dorecord:
            self.program['max_iter'] = 50
            self.program['max_march'] = 200
            self.program['fast'] = 1
        else:
            self.program['max_iter'] = self.params['max_iter']
            self.program['max_march'] = self.params['max_march']
            self.program['fast'] = 0
        # Render
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def render(self, dt):
        if not self.draw:
            return False

        self.window.clear()
        self.program['C'] = [
            self.params['cX'], self.params['cY'], self.params['cZ']]
        self.program['power'] = self.params['power']
        self.program['pitch'] = self.params['pitch']
        self.program['yaw'] = self.params['yaw']
        self.program['zoom'] = self.params['zoom']
        self.program['aO'] = self.params['aO']
        self.program['hue'] = self.params['hue']
        self.program['minDist'] = self.params['min_dist']
        self.program.draw(gl.GL_TRIANGLE_STRIP)
        self.draw = False
        return True

    def on_resize(self, width, height):
        self.program["size"] = width, height
        self.draw = True

    def on_mouse_drag(self, x, y, dx, dy, button):
        self.params["pitch"] -= dy / 50
        self.params["yaw"] += dx / 50
        self.draw = True
        print(x, y, dx, dy, button)

    def on_mouse_scroll(self, x, y, dx, dy):
        self.params["zoom"] += self.params["zoom"] / 10 * dy
        self.draw = True

    def on_key_press(self, k, modifiers):
        super().on_key_press(k, modifiers)
        s = 0.1
        if k == key.UP:
            self.params['cX'] += s
        if k == key.DOWN:
            self.params['cX'] -= s
        if k == key.LEFT:
            self.params['cY'] += s
        if k == key.RIGHT:
            self.params['cY'] -= s
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
    'cX': -.2,
    'cY': -1,
    'cZ': 0,
    'power': 8,
    'pitch': 0,
    'yaw': 0,
    'zoom': -0.59,
    'max_iter': 16,
    'max_march': 150,
    'min_dist': 0.001,
    'aO': 1,
    'hue': .6,
    "mods": {
        "power": {
            "type": "float",
            "sliders": True,
            "min": 0,
            "max": 12,
            "resolution": 0.1,
        },
        "min_dist": {
            "type": "float",
            "sliders": True,
            "min": 0,
            "max": 0.5,
            "resolution": 0.001,
        },
        "cX": {
            "type": "float",
            "sliders": True,
            "min": -5,
            "max": 5,
            "resolution": 0.1,
        },
        "cY": {
            "type": "float",
            "sliders": True,
            "min": -5,
            "max": 5,
            "resolution": 0.1,
        },
        "cZ": {
            "type": "float",
            "sliders": True,
            "min": -5,
            "max": 5,
            "resolution": 0.1,
        },

    }
}


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [3300, None],
            [2751, self.ending],
            [1500, self.sub],
            [1250, self.verse2],
            [500,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(params)

    def ending(self, frame):
        if self.scene_init:
            self.m_mod = self.linspace(self.params["power"], 1.)
            self.x_mod = self.logspace(self.params["cX"] + 10, -2 + 10)
            self.y_mod = self.linspace(self.params["cY"] + 10, 10)
            self.z_mod = self.logspace(self.params["cZ"] + 10, 10.5)
        self.params["power"] = self.m_mod[self.scene_pos]
        self.params["cX"] = self.x_mod[self.scene_pos] - 10
        self.params["cY"] = self.y_mod[self.scene_pos] - 10
        self.params["cZ"] = self.z_mod[self.scene_pos] - 10
        self.params["yaw"] += 0.003

    def sub(self, frame):
        if self.scene_init:
            self.base_x = self.params["cX"]
            self.base_y = self.params["cY"]
            self.base_z = self.params["cZ"]
            self.z_mod = 0
            self.x_mod = 0
            self.y_mod = 0
            self.y_pos = self.logspace(self.params["cY"] + 10, 5.)

        self.params["power"] += 6e-2 * self.bass

        self.x_mod += .1 * self.perc + .01 * self.low
        self.y_mod += .1 * self.bell
        self.z_mod += .05 * self.bell

        self.params["cX"] = self.base_x + 2.6 * np.sin(self.x_mod)
        self.params["cZ"] = self.base_z - 2 * np.abs(np.sin(self.z_mod))
        self.params["cY"] = self.y_pos[self.scene_pos] - 10

        self.params["hue"] += 1e-3 * self.bell

        self.params["yaw"] += 4e-3
        self.params["pitch"] += 2e-3

    def verse2(self, frame):
        if self.scene_init:
            self.y_mod = 0
            self.base_y = self.params["cY"]
            self.z_mod = self.linspace(self.params["zoom"], -.5)
        self.params["zoom"] = self.z_mod[self.scene_pos]
        self.params["power"] -= 1e-2 * self.bell
        self.params["cX"] -= 3e-2 * self.perc
        self.params["cY"] += 3e-2 * self.perc
        self.params["hue"] += 1e-4 * self.bell

    def verse1(self, frame):
        if self.scene_init:
            self.m_mod = self.logspace(self.params["min_dist"] + 10, 0.01 + 10)
            self.z_mod = self.linspace(self.params["cZ"], 1.)
        self.params["hue"] -= 1e-4 * self.hgh
        self.params["power"] += 1e-2 * self.bell
        self.params["cY"] -= 3.8e-3 * self.hgh
        self.params["cZ"] = self.z_mod[self.scene_pos]
        self.params["min_dist"] = self.m_mod[self.scene_pos] - 10

    def intro(self, frame):
        if self.scene_init:
            self.p_mod = self.linspace(1.9000000000000123, 4)
            self.z_mod = self.linspace(-1.47, -1.18)
            self.y_mod = self.linspace(-2, -.1)
            self.base_x = self.params["cX"]
            self.params["power"] = 1.9
            self.params["hue"] = .6
        self.params["power"] += 5e-3 * self.low
        self.params["zoom"] = self.z_mod[self.scene_pos]
        self.params["cY"] = self.y_mod[self.scene_pos]

    def updateMidi(self, midi_events, frame):
        super().updateMidi(midi_events, frame)
        if frame < 775:
            self.midi_events["hgh"].prev_val = 0
            self.hgh = 0

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 0
        self.midi_events = {
            "hgh": MidiMod("perc high", mod="one-off", decay=20),
            "perc": MidiMod("perc low", mod="one-off", decay=5),
            "kick": MidiMod("kick", decay=15),
            "bass": MidiMod("BF sub", decay=23, mod="one-off"),
            "rhode": MidiMod("BF friend"),
            "bell": MidiMod("BF buttons", mod="one-off", decay=42),
            "flute": MidiMod("BFbendy lead"),
        }

    def setAudio(self, obj):
        self.audio = obj
        self.spectre = audio.SpectroGram(obj.audio_frame_size)
        self.audio_events = {
            "low": audio.AudioMod((0, 195), "mean"),
        }


if __name__ == "__main__":
    gamegl.run_main(Demo(), MandelBulb)
