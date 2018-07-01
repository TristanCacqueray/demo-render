#!/usr/bin/env python
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

"""
Recaman series represented on a circle, inspired from this video:
https://www.youtube.com/watch?v=FGC5TdIiT9U
"""

import collections
import colorsys
import math

from utils import animation
from utils import game
from utils import audio

params = {
    'seeds': 42,
    'ratio': 1e-5,
    'hue': 0.1,
    'size': 1,
    'distance': 1,
    'mods': {
        'seeds': {
            'type': 'int',
            'min': 1,
            'max': 600,
            'resolution': 1,
            'sliders': True},
    },
}


class RecamanCircle(game.Window):
    def __init__(self, winsize, params):
        game.Window.__init__(self, winsize)
        self.params = params
        self.series = collections.deque(maxlen=512)
        self.mod = 84

    def circle_point(self, mod, point):
        # Return coordinate of a point on a mod circle
        angle = ((point % mod) * 360 / float(mod)) * math.pi / 180.0
        return (int(self.window_size[0] / 2 + self.radius * math.sin(angle)),
                int(self.window_size[1] / 2 + self.radius * math.cos(angle)))

    def render(self, frame):
        self.fill()
        v = 1
        deltav = 0.8 / (len(self.series) + 1)
        deltau = 0.4 / (len(self.series) + 1)
        draw_call = []
        width = 4
        for j in range(len(self.series) - 1, 0, -1):
            s = self.circle_point(self.mod, self.series[j])
            e = self.circle_point(self.mod, self.series[j - 1])
            color = list(map(lambda x: x * 255, colorsys.hsv_to_rgb(
                self.hue, v, v)))
            self.hue += deltau
            v -= deltav
            draw_call.append((s, e, color, width))
            width = 1
        for s, e, color, width in reversed(draw_call):
            self.draw_line(s, e, color, width)
        if self.series:
            print(self.series[-1])
        return True


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [16000, None],
            [0, self.intro]
        ]
        super().__init__(params)

    def updateMidi(self, midi_events):
        for k in midi_events:
            if k['track'] == 'Recaman':
                self.scene.series.append(list(k['ev'][0]['pitch'].keys())[0])

    def setAudio(self, obj):
        self.audio = obj
        self.spectre = audio.SpectroGram(obj.audio_frame_size)
        self.audio_events = {
            "low": audio.AudioMod((0, 24), "max"),
            "mid": audio.AudioMod((25, 75), "avg"),
            "hgh": audio.AudioMod((373, 500), "max"),
        }

    def intro(self, frame):
        if self.scene_init:
            self.base_radius = self.scene.window_size[1] / 2 - 2
            self.base_hue = 0.5

        self.scene.radius = self.base_radius - self.base_radius / 10 * self.low
        self.scene.hue = self.base_hue #+ 0.1 * self.hgh
        self.base_hue += 1e-3


if __name__ == "__main__":
    animation.run_main(Demo(), RecamanCircle)
