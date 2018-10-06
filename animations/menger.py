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

fragment = open("menger.glsl").read()


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
        self.program["iTime"] = self.params["iTime"]
        self.program["p1"] = self.params["p1"]
        self.program["p2"] = self.params["p2"]
        self.program["p3"] = self.params["p3"]
        self.program["p4"] = self.params["p4"]
        self.program["hue"] = self.params["hue"]
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
    "iTime": 0,
    "p1": 1,
    "p2": 1,
    "p3": 1,
    "p4": 0,
    "hue": 0.6,
    "mods": {
        "p4": {
            "type": "float",
            "sliders": True,
            "min": 0.5,
            "max": 3,
            "resolution": 0.01,
        },
        "p2": {
            "type": "float",
            "sliders": True,
            "min": 0.5,
            "max": 3,
            "resolution": 0.01,
        },
        "p3": {
            "type": "float",
            "sliders": True,
            "min": 0.5,
            "max": 3,
            "resolution": 0.01,
        },
    }
}


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [2600, None],
            [0,    self.intro],
        ]
        super().__init__(params)

    def intro(self, frame):
        if self.scene_init:
            self.p1_mod = 0
            self.p2_mod = 0
            self.p4_mod = 0
        self.params["iTime"] += 0.02 * (self.mid + 0.5 * self.low) / 2
        self.p2_mod += .8e-2 * self.low
        self.p4_mod += 2.5e-2 * self.hgh
        self.params["p2"] = 0.89 + 0.5 * np.abs(np.sin(self.p2_mod))
        self.params["p3"] = 1.9 - 1 * self.low
        self.params["p4"] = 0 + 0.5 * np.abs(np.sin(self.p4_mod))
        self.params["hue"] += 1e-2 * self.hats
        pass

    def setAudio(self, obj):
        self.audio = obj
        self.spectre = audio.SpectroGram(obj.audio_frame_size)
        max_freq = obj.audio_frame_size // 2
        self.audio_events = {
            "hats": audio.AudioMod((575, max_freq), "mean", decay=5),
            "hgh": audio.AudioMod((273, 293), "max", decay=30, threshold=0.5),
            "mid": audio.AudioMod((132, 146), "max", decay=30, threshold=0.5),
            "low": audio.AudioMod((0, 4), "max", decay=30, threshold=0.6),
        }


if __name__ == "__main__":
    gamegl.run_main(Demo(), Shader)
