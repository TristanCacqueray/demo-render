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
from glumpy import gl, gloo, glm
from glumpy.app.window import key

from utils import gamegl
from utils import animation
from utils import audio


vertex = """
#version 120

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

attribute float radius;
attribute float distance;
attribute float cutoff;
attribute vec3  position;

varying float v_radius;
varying float v_distance;
varying float v_cutoff;

void main (void)
{
    v_radius = radius;
    v_distance = distance;
    v_cutoff = cutoff;

    gl_Position = projection * view * model * vec4(position,1.0);
    gl_PointSize = 2 * v_radius;
}
"""

fragment = """
#version 120

varying float v_radius;
varying float v_distance;
varying float v_cutoff;

void main()
{
    float r = (v_radius);
    float signed_distance = length(
        gl_PointCoord.xy - vec2(0.5,0.5)) * 2 * r - v_radius;

    // Inside shape
    if (v_distance > v_cutoff) {
        discard;
    } else if (signed_distance < 0) {
        gl_FragColor = vec4(1, v_distance, v_distance, 1 - v_distance * 0.8);
    // Outside shape
    } else {
        discard;
    }
}
"""

params = {
    'ratio': 1.59,
    'size': 0,
    'distance': 1e-5,
    'posx': 0,
    'posy': 0,
    'posz': 0.7185863684301576,
    'cutoff': 10,
    'phi': 0,
    'theta': 0,
    "mods": {
        "ratio": {
            "type": "ratio",
            "sliders": True,
            "min": 1,
            "max": 2,
            "resolution": 0.001
        },
        }
}

n = 100000


class FlowerSeedsGL(gamegl.Window):
    def init_program(self):
        self.program = gloo.Program(vertex, fragment, count=n)
        self.program['position'] = np.zeros((n, 3), dtype=np.float32)
        self.program['radius'] = 1
        self.program['projection'] = glm.perspective(
            45.0, self.winsize[0] / float(self.winsize[1]), 1.0, 1000.0)
        self.program["distance"] = np.linspace(0, 1, n)

        gl.glEnable(gl.GL_DEPTH_TEST)

        self.posx = 0
        self.posy = 0

    def on_resize(self, width, height):
        self.program['projection'] = glm.perspective(
                45.0, width / float(height), 1.0, 1000.0)

    def on_key_press(self, k, modifiers):
        super().on_key_press(k, modifiers)
        if k == key.UP:
            self.params["posy"] += .01
        elif k == key.DOWN:
            self.params["posy"] -= .01
        elif k == key.LEFT:
            self.params["posx"] += .01
        elif k == key.RIGHT:
            self.params["posx"] -= .01
        elif k == 69:
            self.params["posz"] += .01
        elif k == 81:
            self.params["posz"] -= .01
        elif k == 65:
            self.params["phi"] += .1
        elif k == 68:
            self.params["phi"] -= .1
        else:
            print(k)

    def render(self, dt):
        if not self.draw:
            return False
        # View
        view = np.eye(4, dtype=np.float32)
        glm.translate(
            view,
            self.params["posx"], self.params["posy"], self.params["posz"])
        self.program['view'] = view

        # Model
        model = np.eye(4, dtype=np.float32)
        glm.rotate(model, self.params["theta"], 0, 0, 1)
        glm.rotate(model, self.params["phi"], 0, 1, 0)
        self.program['model'] = model

        # Modulations
        self.program['radius'] = self.params["size"]
        self.program['cutoff'] = self.params['cutoff']

        position = self.program['position']
        angles = np.linspace(0, np.pi * self.params["ratio"] * n, n)
        thet = np.linspace(0, np.pi * self.params["ratio"] * 2, n)
        distances = np.linspace(
            0, (0.00005 + self.params["distance"]) * n, n)

        position[:, 0] = distances * np.sin(angles) * np.cos(thet)
        position[:, 1] = distances * np.sin(angles) * np.sin(thet)
        position[:, 2] = distances * np.cos(angles)

        # Drawing
        self.window.clear()
        self.program.draw(gl.GL_POINTS)
        self.draw = False
        return True


class Demo(animation.Animation):
    def __init__(self):
        self.scenes = [
            [3310, None],
            [2760, self.outro],
            [2300, self.approach],
            [1600, self.zoomin],
            [875, self.zoomout],
            [0, self.intro],
        ]
        super().__init__(params)

    def outro(self, frame):
        if self.scene_init:
            self.z_mod = self.logspace(self.params["posz"] + 15, 1, 300)
            self.d_mod = self.logspace(self.params["distance"], 1e-6)
            self.t_mod = self.linspace(self.params["theta"], -20 * 4)
            self.p_mod = self.linspace(self.params["phi"], -103)
            self.r_mod = self.logspace(self.params["ratio"], 1.44, 300)
            self.c_mod = self.logspace(self.params["cutoff"], 10, 300)
            self.s_mod = self.linspace(3, 1)
        if self.scene_pos < 300:
            self.params["cutoff"] = self.c_mod[self.scene_pos]
            self.params["posz"] = self.z_mod[self.scene_pos] - 15
        self.params["theta"] += .5
        self.params["phi"] += .3
        self.params["distance"] = self.d_mod[self.scene_pos]
        self.params["ratio"] += 2.5e-6
        self.params["size"] = self.s_mod[self.scene_pos]

    def approach(self, frame):
        if self.scene_init:
            self.d_mod = self.logspace(self.params["distance"], 1e-3)
            self.t_mod = self.linspace(self.params["theta"], 89, 200)
            self.p_mod = self.linspace(self.params["phi"], 285, 200)
            self.s_mod = self.linspace(2, 3)
            self.c_mod = self.linspace(self.params["cutoff"], 0.01)
        self.params["cutoff"] = self.c_mod[self.scene_pos]

        self.params["distance"] = self.d_mod[self.scene_pos]
        if self.scene_pos < 200:
            self.params["theta"] = self.t_mod[self.scene_pos]
            self.params["phi"] = self.p_mod[self.scene_pos]
        self.params["ratio"] -= 5e-5 * self.hgh
        self.params["size"] = self.s_mod[self.scene_pos]

    def zoomin(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(1e-7, 1e-6)
            self.z_mod = self.linspace(self.params["posz"] + 15, -1.40 + 15)
            self.s_mod = self.linspace(self.params["size"], 2)
            self.c_mod = self.linspace(self.params["cutoff"], 0.3)
        self.params["cutoff"] = self.c_mod[self.scene_pos]
        self.params["posz"] = self.z_mod[self.scene_pos] - 15
        self.params["ratio"] -= self.r_mod[self.scene_pos] * self.mid
        self.params["theta"] += 0.1
        self.params["phi"] += 0.2
        self.params["size"] = (self.s_mod[self.scene_pos] - 1 * self.hgh)

    def zoomout(self, frame):
        if self.scene_init:
            self.z_mod = self.linspace(self.params["posz"] + 15, 0)
            self.t_mod = self.linspace(1, 20 * 4)
            self.p_mod = self.linspace(1, 103)
            self.s_mod = self.logspace(1, 5)
            self.d_mod = self.logspace(self.params["distance"], 1e-3)
            self.b_size = self.params["size"]

        self.params["size"] = self.b_size + 2 * self.mid
        self.params["posz"] = self.z_mod[self.scene_pos] - 15
        self.params["theta"] = self.t_mod[self.scene_pos] - 1
        self.params["phi"] = self.p_mod[self.scene_pos] - 1
        self.params["ratio"] += 1e-7 * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.params["ratio"] = 1.440
            self.z_mod = self.linspace(self.params["posz"] + 15, 13)
            self.s_mod = self.logspace(4, 1)
        self.params["posz"] = self.z_mod[self.scene_pos] - 15
        self.params["size"] = self.s_mod[self.scene_pos]
        self.params["ratio"] -= 1e-7 * self.hgh
        self.params["dist"] = -10 + np.cos(frame / 500) * 8.5

    def setAudio(self, obj):
        self.audio = obj
        self.spectre = audio.SpectroGram(obj.audio_frame_size)
        self.audio_events = {
            "low": audio.AudioMod((0, 24), "avg"),
            "mid": audio.AudioMod((25, 75), "avg"),
            "hgh": audio.AudioMod((373, 500), "max"),
        }


if __name__ == "__main__":
    gamegl.run_main(Demo(), FlowerSeedsGL)
