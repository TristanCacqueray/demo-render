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
import time
from . pygame_utils import Window, ComplexPlane
from . opencl_complex import calc_fractal_opencl, BUFALO_SHIP, DUCK, POWDUCK


class BurningJuliaSet(Window, ComplexPlane):
    def __init__(self, args, variant=""):
        Window.__init__(self, args.winsize)
        self.c = args.c
        self.args = args
        self.max_iter = args.max_iter
        self.color = args.color
        self.variant = variant
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame, draw_info=False):
        start_time = time.monotonic()
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        q = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        f = None
        if self.variant == "bufalo":
            f = BUFALO_SHIP
        elif self.variant == "duck":
            f = DUCK
        elif self.variant == "powduck":
            f = POWDUCK
        nparray = calc_fractal_opencl(q, "juliaship", self.max_iter, self.args,
                                      seed=self.c, f=f)
        self.blit(nparray)
        if draw_info:
            self.draw_axis()
            self.draw_function_msg()
            self.draw_cpoint()
        print("%04d: %.2f sec: ./burning_julia.py --max_iter '%s' --c '%s' "
              "--center '%s' "
              "--radius %s --gradient_frequency %f" % (
                    frame, time.monotonic() - start_time,
                    int(self.max_iter),
                    self.c,
                    self.center, self.radius, self.args.gradient_frequency))

    def draw_function_msg(self):
        if self.c.real >= 0:
            r_sign = "+"
        else:
            r_sign = ""
        if self.c.imag >= 0:
            i_sign = "+"
        else:
            i_sign = ""
        self.c_str = "z*z%s%.5f%s%.5fj" % (
            r_sign, self.c.real, i_sign, self.c.imag)
        self.draw_msg(self.c_str)

    def draw_cpoint(self):
        self.draw_complex(self.c, (255, 0, 0))
