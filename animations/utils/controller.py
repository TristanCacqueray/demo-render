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

import copy
import pprint
import time

import numpy as np
import pygame
import pygame.locals
try:
    import tkinter
    tk_ftw = True
except ImportError:
    print("Install tkinter for controller gui")
    tk_ftw = False


DEFAULT_PARAMETERS = {
    # Kernel
    "kernel": "escape-time-gradient",
    "kernel_params": "",
    "kernel_params_mod": [],
    "kernel_variables": "",
    "super_sampling": 1,
    "formula": "z = cdouble_add(cdouble_mul(z, z), c);",
    "gradient": "AG_coldfire.ggr",
    "gradient_length": 512,
    "escape_distance": 4242.0,
    "xyinverted": False,
    "inner_point": '0',
    "julia": False,
    "center_real": 0.0,
    "center_imag": 0.0,
    "radius": 2.3,
    "show_map": True,
    "map_center_real": 0.0,
    "map_center_imag": 0.0,
    "map_radius": 2.3,
    "c_real": 0.0,
    "c_imag": 0.0,
    "r_step": 1e-1,
    "i_step": 1e-1,
    "max_iter": 256,
    "grad_freq": 1.0,
    "mods": {
        "r_step": {
            "type": "fine",
            "sliders": True,
        },
        "i_step": {
            "type": "fine",
            "sliders": True,
        },
        "max_iter": {
            "type": "int",
            "keys": ['i', 'k'],
            "sliders": True,
            "min": 1,
            "max": 10000,
            "resolution": 2,
            "key_resolution": 1,
        },
        "grad_freq": {
            "type": "int",
            "sliders": True,
            "min": 0.01,
            "max": 42,
            "resolution": 0.05,
        },
        "radius": {
            "type": "ratio",
            "keys": ['a', 'e'],
            "key_resolution": 4,
        },
        "map_radius": {
            "type": "ratio",
            "keys": ['w', 'x'],
            "key_resolution": 4,
            "map_redraw": True,
            "map_center": True,
        },
    }
}

KEY2CODE = {
    'a': 24, 'e': 26,
    'q': 38, 'd': 40, 'z': 25, 's': 39,
    'i': 31, 'k': 45,
    'w': 52, 'x': 53,
    'o': 32,
    'm': 47,
    'ESCAPE': 9,
    'SPACE': 65,
}
CODE2KEY = {}
for k, v in KEY2CODE.items():
    CODE2KEY[v] = k


class Controller:
    def __init__(self, params, variant=None):
        for k, v in DEFAULT_PARAMETERS.items():
            if k not in params:
                params[k] = v
        for k, v in DEFAULT_PARAMETERS["mods"].items():
            if k not in params.get("mods", {}):
                params.setdefault("mods", {})[k] = v
        self.start_params = copy.copy(params)
        # Apply variant
        if variant:
            for k, v in variant.items():
                params[k] = v
        self.last_key_press = None
        self.last_key_press_time = 0
        self.params = params
        self.keymaps = {}
        self.paused = False
        for mod, mod_param in self.params["mods"].items():
            if not mod_param.get("keys"):
                continue
            keys = list(map(lambda x: KEY2CODE[x], mod_param.get("keys")))
            res = mod_param.get("key_resolution")
            if mod_param.get("type") == "int":
                self.keymaps[keys[0]] = [mod, "add", res]
                self.keymaps[keys[1]] = [mod, "add", -1 * res]
            elif mod_param.get("type") == "ratio":
                self.keymaps[keys[0]] = [mod, "mul", (res+1)/res]
                self.keymaps[keys[1]] = [mod, "mul", (res-1)/res]
        if not tk_ftw:
            self.root = None
            return
        self.root = tkinter.Tk()
        self.controllers = []
        self.width = 900
        self.location_pos = 0
        for mod, mod_param in self.params["mods"].items():
            if not mod_param.get("sliders"):
                continue
            if mod_param.get("type") == "fine":
                self.add_fine(mod)
            else:
                self.add_float(mod,
                               mod_param["min"], mod_param["max"],
                               mod_param["resolution"])
        # Give tcl/tk sometime to reserve resources
        self.root.update()
        time.sleep(0.23)

    def set(self, screen, scene):
        """Set provided params"""
        self.screen = screen
        self.scene = scene
        self.update_sliders()

    def update_sliders(self):
        # Set sliders position
        if not self.root:
            return
        for t, n, v in self.controllers:
            value = self.params[n]
            if t == "float":
                v.set(value)
            else:
                val, magnitude = list(map(lambda x: int(x.split('.')[0]),
                                          "{:1e}".format(value).split('e')))
                v[0].set(val)
                v[1].set(magnitude)

        self.root.update()

    def _get_row(self):
        row = 0
        for controller in self.controllers:
            if controller[0] == "fine":
                row += 2
            else:
                row += 1
        return row

    def add_float(self, name, from_, to, resolution=1):
        """Add simple slider"""
        r = self._get_row()

        param = tkinter.Scale(self.root,
                              from_=from_, to=to, resolution=resolution,
                              orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text=name).grid(row=r, column=0)
        param.grid(row=r, column=1)
        param.bind("<ButtonRelease-1>", self.on_tkclic)
        self.controllers.append(["float", name, param])

    def add_fine(self, name):
        """Add 2 sliders, one for value, one for magnitude order"""
        r = self._get_row()
        param = tkinter.Scale(self.root,
                              from_=0, to=10, resolution=1,
                              orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text='%s value' % name).grid(row=r, column=0)
        param.grid(row=r, column=1)
        param.bind("<ButtonRelease-1>", self.on_tkclic)

        param_mag = tkinter.Scale(self.root,
                                  from_=-15, to=15, resolution=1,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text='%s mag' % name).grid(row=r+1, column=0)
        param_mag.grid(row=r+1, column=1)
        param_mag.bind("<ButtonRelease-1>", self.on_tkclic)
        self.controllers.append(["fine", name, (param, param_mag)])

    def on_tkclic(self, ev=None):
        # Read all sliders values
        for t, n, v in self.controllers:
            if t == "fine":
                val = float("%de%d" % (v[0].get(), v[1].get()))
                self.params[n] = val
            if t == "float":
                self.params[n] = v.get()
                print("Setting", n, "to", v.get())
        self.scene.draw = True

    def on_pygame_clic(self, ev):
        plane_coord = self.scene.convert_to_plane(ev.pos)
        if ev.button in (1, 3):
            if ev.button == 1:
                step = 3/4.0
            else:
                step = 4/3.0
            self.params["radius"] *= step
            self.params["center_real"] = plane_coord.real
            self.params["center_imag"] = plane_coord.imag
            self.scene.draw = True
        else:
            print("Clicked", ev.pos, plane_coord)

    def on_key(self, scancode):
        self.scene.draw = True

        if scancode in self.keymaps:
            mod = self.keymaps[scancode]
            if mod[1] == "add":
                self.params[mod[0]] += mod[2] * 100
            elif mod[1] == "mul":
                self.params[mod[0]] *= mod[2]
            if self.params["mods"][mod[0]].get("map_redraw"):
                self.params["i_step"] = self.params["map_radius"] / 10.
                self.params["r_step"] = self.params["map_radius"] / 10.
                self.scene.draw = False
                self.scene.map_scene.draw = True
                if self.params["mods"][mod[0]].get("map_center"):
                    x, y = "real", "imag"
                    if self.params["xyinverted"]:
                        x, y = "imag", "real"
                    self.params["map_center_real"] = self.params["c_" + x]
                    self.params["map_center_imag"] = self.params["c_" + y]
            self.update_sliders()
            return

        direction = 1
        key = CODE2KEY.get(scancode)
        x, y = "real", "imag"
        if self.params.get("xyinverted"):
            x, y = "imag", "real"
        if key == "ESCAPE":
            self.scene.draw = False
            self.scene.alive = False
        elif key in ('q', 'd'):
            if key == 'q':
                direction = -1
            self.params["c_" + x] += direction * self.params["r_step"]
        elif key in ('s', 'z'):
            if key == 'z':
                direction = -1
            self.params["c_" + y] += direction * self.params["i_step"]
        elif key == 'm':
            # Show/hide map
            self.params["show_map"] = not self.params["show_map"]
            main = self.screen.windows[0]
            if self.params["show_map"]:
                if not self.scene.map_scene:
                    self.scene.create_map_scene(self.map_size, self.params)
                self.screen.windows = [main, (self.scene.map_scene, (0, 0))]
            else:
                self.screen.windows = [main]
            self.scene.draw = True
        elif key == 'o':
            from . dialog import NameDialog
            self.last_key_press = None
            diag = NameDialog(self.root)
            if diag.name:
                import yaml
                data = {'variant': {diag.name: self.get()}}
                print(yaml.dump(data, default_flow_style=False))
            diag.destroy()
            self.scene.draw = False
        elif key == 'SPACE':
            self.paused = not self.paused
        elif scancode in (113, 114):
            if scancode == 113:
                direction = -1
            self.params["center_real"] += direction * 10 / self.scene.scale[0]
        elif scancode in (111, 116):
            if scancode == 111:
                direction = -1
            self.params["center_imag"] += direction * 10 / self.scene.scale[1]
        elif scancode == 27:
            self.params["center_real"] = self.start_params["center_real"]
            self.params["center_imag"] = self.start_params["center_imag"]
            self.params["radius"] = self.start_params["radius"]
        elif scancode == 33:
            self.screen.capture("./{time}_{rsign}{r}{isign}{i}i.png".format(
                time=time.strftime("%Y-%m-%d_%H:%M"),
                rsign="" if self.params["c_real"] >= 0 else "-",
                r=abs(self.params["c_real"]),
                isign="+" if self.params["c_imag"] >= 0 else "-",
                i=abs(self.params["c_imag"])))
            self.scene.draw = False
        elif scancode == 53:
            pprint.pprint(self.get())
            self.scene.draw = False
        else:
            self.scene.draw = False

    def update(self, frame):
        if self.root:
            self.root.update()
        for ev in pygame.event.get():
            if ev.type == pygame.locals.KEYDOWN:
                self.last_key_press = ev.dict['scancode']
                self.last_key_press_time = time.monotonic()
                self.on_key(self.last_key_press)
            elif ev.type == pygame.locals.KEYUP:
                self.last_key_press = None
            elif ev.type == pygame.locals.MOUSEBUTTONDOWN:
                self.on_pygame_clic(ev)
        if self.last_key_press is not None and \
           time.monotonic() - self.last_key_press_time > 0.2:
            self.on_key(self.last_key_press)
            self.last_key_press_time = time.monotonic()

    def get(self):
        """Get modified params"""
        params = {}
        for k, v in self.start_params.items():
            if self.params[k] != v:
                params[k] = self.params[k]
        return params

    def set_c(self, c):
        self.params["c_real"] = c.real
        self.params["c_imag"] = c.imag

    def get_c(self):
        return complex(self.params["c_real"], self.params["c_imag"])
