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
Flower seeds distribution representation based on this video
https://www.youtube.com/watch?v=sj8Sg8qnjOg
"""

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


class FlowerSeeds(game.Window):
    def __init__(self, winsize, params):
        game.Window.__init__(self, winsize)
        self.params = params

    def seed(self, angle, distance):
        # Return coordinate of a point on a mod circle
        return (int(self.window_size[0] / 2 + distance * math.sin(angle)),
                int(self.window_size[1] / 2 + distance * math.cos(angle)))

    def render(self, frame):
        self.fill()
        seeds, ratio = self.params["seeds"], self.params["ratio"]
        size, base_hue = self.params["size"], self.params["hue"]
        angle = 0
        distance = 5
        for j in range(0, seeds):
            coord = self.seed(angle, distance)
            angle += math.pi * ratio * 2
            distance += self.params["distance"]
            hue = base_hue + (j % 100) / 300.0
            color = list(map(lambda x: x * 255, colorsys.hsv_to_rgb(
                hue + 0.001 * j, 0.7, 0.7)))
            self.draw_circle(coord, size, color)
        self.draw_msg("Ratio: %.8f" % self.params["ratio"])
        return True


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [6200, None],
            [0, self.intro]
        ]
        super().__init__(params)

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
            self.params["ratio"] = (1+math.sqrt(5))/2.0 - 0.05
            self.params["distance"] = 1
            self.base_speed = 1e-5
            self.base_seed = 1
            self.base_size = 2
        self.params["seeds"] = int(self.base_seed + 300 * self.hgh)
        self.params["ratio"] += self.base_speed + 1e-5 * self.low
        self.params["size"] = int(self.base_size + 5 * self.mid)
        if frame >= 1280:
            self.params["distance"] = 1 - 0.9 * self.mid
        self.params["hue"] += 1e-2
        self.base_seed += 0.3


if __name__ == "__main__":
    animation.run_main(Demo(), FlowerSeeds)
