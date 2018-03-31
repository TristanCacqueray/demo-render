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

import colorsys
import math


MAX_SHORT = float((2 ** (2 * 8)) // 2)
PHI = (1+math.sqrt(5))/2.0


def rgb(r, g, b):
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def rgb250(r, g, b):
    return int(b) | int(g) << 8 | int(r) << 16


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def rotate_point(point, angle):
    return complex(point[0] * math.cos(angle) - point[1] * math.sin(angle),
                   point[0] * math.sin(angle) + point[1] * math.cos(angle))


def run_main(main):
    try:
        main()
    except KeyboardInterrupt:
        pass
