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

import argparse
import collections
import json
import time
import math
import os
import numpy as np
import copy
from PIL import Image

from glumpy import app, gl, glm, gloo
from glumpy.app.window import key
from glumpy.app.window.event import EventDispatcher

from . controller import Controller
from . audio import Audio, NoAudio, SpectroGram
from . midi import Midi, NoMidi


class Window(EventDispatcher):
    alive = True
    draw = True

    def __init__(self, winsize, screen):
        self.winsize = winsize
        self.window = screen
        self.init_program()
        self.fbuffer = np.zeros(
            (self.window.height, self.window.width * 3), dtype=np.uint8)
        super().__init__()

    def capture(self, filename):
        gl.glReadPixels(
            0, 0, self.window.width, self.window.height,
            gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.fbuffer)
        image = Image.frombytes("RGB", self.winsize, np.ascontiguousarray(np.flip(self.fbuffer, 0)))
        image.save(filename, 'png')

    def on_draw(self, dt):
        pass

    def on_resize(self, width, height):
        pass

    def on_key_press(self, k, modifiers):
        if k == key.ESCAPE:
            self.alive = False
        elif k == key.SPACE:
            self.paused = not self.paused
        self.draw = True


def fragment_loader(fragment: str, export: bool, filename=None):
    final = []
    uniforms = {"mods": {}}
    shadertoy = False

    def loader(lines: list):
        for line in lines:
            if line.startswith("#include"):
                loader(open(os.path.join(os.path.dirname(filename),
                                         line.split()[1][1:-1])
                            ).read().split('\n'))
            else:
                export_line = ""
                if line.lstrip().startswith('uniform'):
                    param = line.split()[2][:-1]
                    param_type = line.split()[1]
                    if param_type == "float":
                        val = 0.
                    elif param_type in ("vec2", "dvec2"):
                        val = [0., 0.]
                    elif param_type == "vec3":
                        val = [0., 0., 0.]
                    elif param_type == "vec4":
                        val = [0., 0., 0., 0.]
                    elif param_type == "mat4":
                        val = np.eye(4, dtype=np.float32)
                    else:
                        raise RuntimeError("Unknown uniform %s" % line)
                    if '//' in line:
                        if 'slider' in line:
                            slider_str = line[line.index('slider'):].split(
                                '[')[1].split(']')[0]
                            smi, sma, sre = list(map(
                                float, slider_str.split(',')))
                            uniforms["mods"][param] = {
                                "type": param_type,
                                "sliders": True,
                                "min": smi,
                                "max": sma,
                                "resolution": sre,
                            }
                        val_str = line.split()[-1]
                        if param_type == "float":
                            val = float(val_str)
                        elif param_type in ("vec2", "vec3"):
                            val = list(map(float, val_str.split(',')))
                        uniforms[param] = val
                        if shadertoy:
                            if param_type.startswith("vec"):
                                val_str = "%s%s" % (param_type, tuple(val))
                            else:
                                val_str = str(val)
                            export_line = "const %s %s = %s;" % (
                                param_type, param, val_str
                            )
                    else:
                        uniforms[param] = val
                if export and export_line:
                    final.append(export_line)
                else:
                    final.append(line)
    if "void mainImage(" in fragment:
        shadertoy = True
        if not export:
            final.append("""uniform vec2 iResolution;
uniform vec4 iMouse;
uniform float iTime;
void mainImage(out vec4 fragColor, in vec2 fragCoord);
void main(void) {mainImage(gl_FragColor, gl_FragCoord.xy);}""")
    loader(fragment.split('\n'))
    return "\n".join(final), uniforms


class FragmentShader(Window):
    """A class to simplify raymarcher/DE experiment"""
    vertex = """
attribute vec2 position;

void main(void) {
  gl_Position = vec4(position, 0., 1.);
}
"""
    dot_vertex = """
attribute vec2 position;
attribute float age;
varying float v_age;

void main(void) {
  v_age = age;
  gl_Position = vec4(position, 0., 1.);
  gl_PointSize = 4.0;
}
"""
    dot_fragment = """
varying float v_age;
void main() {
    float sd = length(gl_PointCoord.xy - vec2(.5))  - 2 * v_age;
    if (sd < 0.) {
      gl_FragColor = vec4(1.0);
    } else {
      discard;
    }
}
"""
    buttons = {
        app.window.mouse.NONE: 0,
        app.window.mouse.LEFT: 1,
        app.window.mouse.MIDDLE: 2,
        app.window.mouse.RIGHT: 3
    }

    def __init__(self, args, fragment=None, winsize=None, title=None):
        self.fps = args.fps
        self.record = args.record
        self.old_program = None
        if fragment is None:
            fragment = args.fragment
        if winsize:
            args.winsize = list(map(int, winsize))
        self.title = title
        self.load_program(fragment, args.export)
        self.params = args.params
        if self.params:
            self.program_params = set(self._params.keys()).intersection(
                set(self.params.keys())) - {"mods"}
        else:
            self.params = self._params
            self.program_params = set(self._params.keys()) - {"mods"}
        self.iMat = self.params.get("iMat")
        # Gimbal mode, always looking at the center
        self.gimbal = True
        if self.gimbal:
            self.params.setdefault("horizontal_angle", 0.)
            self.params.setdefault("vertical_angle", 0.)
            self.params.setdefault("distance", 10.)
        if self.iMat is not None:
            self.horizontal_angle = self.params.get("horizontal_angle", 0.)
            self.vertical_angle = self.params.get("vertical_angle", 0.)
            self.setDirection()
            if self.gimbal:
                self.position = np.array([.0, .0, self.params["distance"]])
            else:
                self.position = np.array([.0, .0, 10.2])
        if title != "Map":
            self.controller = Controller(self.params, default={})
        else:
            self.controller = None
        self.screen = app.Window(
            width=args.winsize[0], height=args.winsize[1], title=title)
        super().__init__(args.winsize, self.screen)
        if self.controller:
            self.controller.set(self.screen, self)
        self.screen.attach(self)
        self.paused = False
        self.prev_params = {}

    def load_program(self, fragment_path, export=False):
        if os.path.exists(fragment_path):
            fragment = open(fragment_path).read()
            fn = fragment_path
            self.fragment_path = fragment_path
            self.fragment_mtime = os.stat(fragment_path).st_mtime
        else:
            fragment = fragment_path
            fn = None
            self.fragment_mtime = None

        self.fragment, self._params = fragment_loader(fragment, export, fn)
        self.iTime = "iTime" in self.fragment
        self.iMouse = "iMouse" in self.fragment
        if export:
            print(self.fragment)
            exit(0)

    def init_program(self):
        # Ensure size is set
        #print("program param: ", self.program_params)
        #print("---[")
        #print(self.fragment)
        #print("]---")
        self.program = gloo.Program(self.vertex, self.fragment, count=4, version="450")
        self.program['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        if self.title == "Map":
            self.point_history = collections.deque(maxlen=250)
            self.point_program = gloo.Program(
                self.dot_vertex,
                self.dot_fragment,
                count=self.point_history.maxlen)
            self.point_program['position'] = np.zeros(
                (self.point_history.maxlen, 2), dtype=np.float32) - 2.0
            self.point_program['age'] = np.zeros(self.point_history.maxlen,
                                                 dtype=np.float32)
        # TODO: make those setting parameter
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.on_resize(*self.winsize)
        if self.iMouse:
            self.program["iMouse"] = self.iMouse

    def update(self, frame):
        if self.fragment_mtime:
            mtime = os.stat(self.fragment_path).st_mtime
            if mtime > self.fragment_mtime:
                self.old_program = self.program
                self.load_program(self.fragment_path)
                self.init_program()
        if self.controller and self.controller.root:
            self.controller.root.update()
        if self.title == "Map":
            # Check for new seed position
            if not len(self.point_history) or \
               self.point_history[-1] != self.params["seed"]:
                self.add_point(copy.copy(self.params["seed"]))
                self.draw = True
        try:
            if self.prev_params != self.params:
                self.draw = True
        except ValueError:
            pass
        if self.paused:
            return self.draw
        self.draw = True
        return self.draw

    def render(self, dt):
        self.window.activate()
        self.window.clear()
        if self.iMat is not None:
            self.iMat = np.eye(4, dtype=np.float32)
            if not self.gimbal:
                glm.xrotate(self.iMat, self.horizontal_angle)
                glm.yrotate(self.iMat, self.vertical_angle)
            else:
                self.position = [0., 0., self.params["distance"]]
            glm.translate(self.iMat, *self.position)
            if self.gimbal:
                glm.xrotate(self.iMat, self.params["horizontal_angle"])
                glm.yrotate(self.iMat, self.params["vertical_angle"])
            self.params["iMat"] = self.iMat
        for p in self.program_params:
            self.program[p] = self.params[p]
        dt = dt / self.fps

        if self.iTime:
            self.program["iTime"] = dt
        try:
            self.program.draw(gl.GL_TRIANGLE_STRIP)
            if self.old_program:
                self.old_program.delete()
                del self.old_program
                self.old_program = None
                print("Loaded new program!")
        except RuntimeError:
            if not self.old_program:
                raise
            self.old_program.draw(gl.GL_TRIANGLE_STRIP)
            self.program.delete()
            del self.program
            self.program = self.old_program
            self.old_program = None
            self.paused = True

        if self.title == "Map":
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_ONE_MINUS_DST_COLOR, gl.GL_ZERO)
            self.point_program.draw(gl.GL_POINTS)
        self.prev_params = copy.deepcopy(self.params)

    def on_resize(self, width, height):
        self.program["iResolution"] = width, height
        self.winsize = (width, height)
        self.draw = True

    def setDirection(self):
        v = math.radians(self.vertical_angle) * -1
        h = math.radians(self.horizontal_angle)
        if self.vertical_angle > 90 or self.vertical_angle < -90:
            # Not sure why this is needed...
            h *= -1
        self.front_direction = np.array([
            math.sin(v),
            math.cos(v) * math.sin(h),
            math.cos(v) * math.cos(h),
        ])
        self.right_direction = np.array([
            math.sin(v - math.pi / 2.),
            0,
            math.cos(v - math.pi / 2.)
        ])
        self.up_direction = np.cross(
            self.right_direction, self.front_direction)
        #print("vert %.1f, horz %.1f, front_direction: %s" % (
        #    self.vertical_angle, self.horizontal_angle,
        #    ",".join(list(map(lambda x: "%.1f" % x, self.front_direction)))))

    def on_mouse_drag(self, x, y, dx, dy, button):
        if self.iMat is not None:
            self.horizontal_angle += dy / 5
            self.vertical_angle += dx / 10
            # Prevent being up side down
            #if self.horizontal_angle > 90:
            #    self.horizontal_angle = 90
            #elif self.horizontal_angle < -90:
            #    self.horizontal_angle = -90
            # Clamp angle from -180 to 180
            self.horizontal_angle = (180 + self.horizontal_angle) % 360 - 180
            self.vertical_angle = (180 + self.vertical_angle) % 360 - 180
            if self.gimbal:
                self.params["horizontal_angle"] = \
                    (180 + self.params["horizontal_angle"] + dy / 5) % 360 - 180
                self.params["vertical_angle"] = \
                    (180 + self.params["vertical_angle"] + dx / 10) % 360 - 180
            self.setDirection()
        elif self.iMouse:
            self.iMouse = x, self.winsize[1] - y, self.buttons[button], 0
            self.program["iMouse"] = self.iMouse
            if "pitch" in self.params:
                self.params["pitch"] -= dy / 50
            if "yaw" in self.params:
                self.params["yaw"] += dx / 50
        self.draw = True

    def normalizeCoord(self, x, y):
        uv = [
            2 * x / self.winsize[0] - 1,
            2 * y / self.winsize[1] - 1,
        ]
        uv[1] *= self.winsize[1] / self.winsize[0]
        return uv

    def add_point(self, seed):
        center = self.params["map_center"]
        ratio = self.winsize[1] / self.winsize[0]
        self.point_history.append(seed)
        if seed[0] < (center[0] - self.params["map_range"]) or \
           seed[0] > (center[0] + self.params["map_range"]) or \
           seed[1] < (center[1] - self.params["map_range"] * ratio) or \
           seed[1] > (center[1] + self.params["map_range"] * ratio):
            print("Recentering the map")
            self.params["map_center"] = seed
        self.update_points_position()

    def update_points_position(self):
        center = self.params["map_center"]
        mrange = self.params["map_range"]
        ratio = self.winsize[1] / self.winsize[0]
        count = len(self.point_history)
        for idx in range(count):
            seed = self.point_history[idx]
            self.point_program["position"][idx] = [
                (seed[0] - center[0]) / (mrange),
                -1 * (seed[1] - center[1]) / (mrange * ratio)
            ]
            self.point_program["age"][idx] = (idx + 1) / count

    def updateCenter(self, x, y):
        uv = self.normalizeCoord(x, y)
        if self.title == 'Map':
            self.update_points_position()
            prefix = 'map_'
            range = self.params["map_range"]
        else:
            prefix = ''
            range = self.params["range"]
        self.params[prefix + "center"] = [
            self.params[prefix + "center"][0] + uv[0] * range,
            self.params[prefix + "center"][1] + uv[1] * range,
        ]

    def updateSeed(self, x, y):
        uv = self.normalizeCoord(x, y)
        self.params["seed"] = [
            self.params["map_center"][0] + uv[0] * self.params["map_range"],
            self.params["map_center"][1] + uv[1] * self.params["map_range"],
        ]

    def on_mouse_press(self, x, y, button):
        if self.title == "Map" and button == 4:
            self.updateSeed(x, y)
        if "center" in self.params and button != 4:
            self.updateCenter(x, y)
            self.draw = True
        if self.title == "Map" and button != 4:
            self.update_points_position()

    def on_mouse_release(self, x, y, button):
        if self.iMouse:
            self.program["iMouse"] = x, self.winsize[1] - y, 0, 0

    def on_mouse_scroll(self, x, y, dx, dy):
        if "range" in self.params:
            if self.title == 'Map':
                range = 'map_range'
            else:
                range = 'range'
            self.params[range] -= self.params[range] / 10 * dy
            if self.title == "Map":
                self.update_points_position()
            self.gimbal = False
        if self.gimbal:
            self.params["distance"] -= 0.1 * dy
        if "fov" in self.params:
            self.params["fov"] += self.params["fov"] / 10 * dy
        self.draw = True

    def on_key_press(self, k, modifiers):
        super().on_key_press(k, modifiers)
        if self.iMat is not None:
            s = 0.1
            if k == 87:    # z
                self.position -= self.front_direction * s
            elif k == 83:  # s
                self.position += self.front_direction * s
            elif k == 65:  # a
                self.position += self.right_direction * s
            elif k == 68:  # d
                self.position -= self.right_direction * s
            elif k == 69:  # a
                self.position += self.up_direction * s
            elif k == 81:  # b
                self.position -= self.up_direction * s
            # print(",".join(list(map(lambda x: "%.1f" % x, self.position))))
        elif "cam" in self.params:
            s = 0.1
            if k == 87:  # z
                self.params['cam'][2] += s
            if k == 83:  # s
                self.params['cam'][2] -= s
            if k == 65:  # a
                self.params['cam'][0] -= s
            if k == 68:  # d
                self.params['cam'][0] += s
            if k == 69:  # a
                self.params["cam"][1] += s
            if k == 81:  # b
                self.params["cam"][1] -= s
        elif "seed" in self.params:
            idx = None
            if k == 87:  # z
                idx = 1
                d = -1
            if k == 83:  # s
                idx = 1
                d = 1
            if k == 65:  # a
                idx = 0
                d = -1
            if k == 68:  # d
                idx = 0
                d = 1
            if idx is not None:
                self.params["seed"][idx] += d * self.params["map_range"] / 10
        self.draw = True


def usage():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paused", action='store_true')
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--super-sampling", type=int, default=1,
                        help="super sampling mode")
    parser.add_argument("--wav", metavar="FILE")
    parser.add_argument("--midi", metavar="FILE")
    parser.add_argument("--midi_skip", type=int, default=0)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--skip", default=0, type=int, metavar="FRAMES_NUMBER")
    parser.add_argument("--size", type=float, default=8,
                        help="render size")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--params", help="manual parameters")
    parser.add_argument("fragment", help="fragment file",
                        nargs='?')
    args = parser.parse_args()

    if args.params is not None:
        if os.path.exists(args.params):
            args.params = json.loads(open(args.params))
        else:
            args.params = json.loads(args.params)
    else:
        args.params = {}

    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.map_size = list(map(lambda x: x//5, args.winsize))
    return args


def main(modulator):
    args = usage()
    scene = FragmentShader(args)
    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)
    scene.alive = True
    frame = args.skip
    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = NoMidi()

    mod = modulator(scene.params)
    scene.controller.update_sliders()

    spectre = SpectroGram(audio.blocksize)

    audio.play = False
    for skip in range(args.skip):
        audio_buf = audio.get(frame)
        spectre.transform(audio_buf)
        mod(skip, spectre, midi.get(args.midi_skip + skip))
    audio.play = not args.record

    scene.alive = True

    if args.paused:
        scene.paused = True
        args.paused = False

    frame = args.skip
    while scene.alive:
        start_time = time.monotonic()
        if not scene.paused:
            audio_buf = audio.get(frame)
            if audio_buf is not None:
                spectre.transform(audio_buf)
            midi_events = midi.get(args.midi_skip + frame)
            if midi_events:
                print(midi_events)
            if mod(frame, spectre, midi.get(args.midi_skip + frame)):
                print("Setting alive to false")
                scene.alive = False
            frame += 1
            scene.controller.update_sliders()
        scene.controller.root.update()
        if scene.update(frame):
            scene.render(frame)

            if args.record:
                scene.capture(os.path.join(args.record, "%04d.png" % frame))

            print("%04d: %.2f sec '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(scene.controller.get(), sort_keys=True)))
            scene.draw = False

        backend.process(clock.tick())

    if args.record:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/render.mp4" % (args.record)]
        print("Running: %s" % " ".join(cmd))
        subprocess.Popen(cmd).wait()


def run_main(demo, Scene):
    args = usage()
    screen = app.Window(width=args.winsize[0], height=args.winsize[1])
    scene = Scene(args.winsize, screen)
    screen.attach(scene)

    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    demo.setAudio(audio)

    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = NoMidi()
    demo.setMidi(midi, args.midi_skip)
    demo.set(screen, scene)

    import pygame
    pygame.init()
    scene.render(0)
    audio.play = False
    demo.silent = True
    for skip in range(args.skip):
        demo.update(skip)
    demo.silent = False
    audio.play = not args.record
    demo.update_sliders()

    scene.alive = True

    if args.paused:
        demo.paused = True
        args.paused = False

    frame = args.skip
    while scene.alive:
        start_time = time.monotonic()
        demo.update(frame)

        if not demo.paused:
            frame += 1
        if scene.render(frame):
            print("%04d: %.2f sec '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(demo.get(), sort_keys=True)))

        if args.record:
            scene.capture(os.path.join(args.record, "%04d.png" % frame))

        backend.process(clock.tick())

    if args.record:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/render.mp4" % (args.record)]
        print("Running: %s" % " ".join(cmd))
        subprocess.Popen(cmd).wait()
