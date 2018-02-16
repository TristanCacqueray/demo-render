#!/bin/env python3
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
SIZE=6
# lm95 anim:
# 0 - 1125    intro
./lm95p1.py --record /tmp/anim --wav ../render_data/lm95p1.wav  --steps 1125 --anim zoom  --size $SIZE
# 1125 - 1575 transition
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 420 --anim zoom2 --frame_start 1125   --size $SIZE
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 30 --anim tr1 --frame_start 1545   --size $SIZE
# 1575 - 2500 part1
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 925 --anim traveling --frame_start  1575  --size $SIZE
# 2500 - 2950 part2
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 18 --anim tr2 --frame_start 2500 --size $SIZE
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 875 --anim trippy --frame_start 2518 --size $SIZE
# 3293 - 4018 zoomout
./lm95p1.py --record /tmp/anim/ --wav ../render_data/lm95p1.wav  --steps 625 --anim zoomout --frame_start 3393  --size $SIZE
"""

import random

import pygame
import numpy as np

from utils_v1.common import usage_cli_complex, run_main
from utils_v1.pygame_utils import Screen
from utils_v1.julia_set import JuliaSet
from utils_v1.scipy_utils import AudioMod


def jiggle(args, audio_mod=None):
    modulations = {
        "zoom": {
            "begin": {
                #  "c": (-1.9672144721067721+3.72412944951802e-12j),
                "c": (-1.8822299686241232+0.001j),  # +3.72412944951802e-12j),
                "radius": 0.300338745117,
            },
            "end": {
                "c": (-1.7822299686241232+0.001j),  # 3.72412944951802e-12j),
                "radius": 3.01697554849e-02,
            },
            "radius_space": "log",
            "audio_mod": {
                "c_imag": -0.0015,
            },
            # "space": "log",
            "max_iter": 2048,
        },
        "zoom2": {
            "begin": {
                "c": (-1.7822299686241232+0.0005166571710672173j),
                "radius": 0.0301697554849,
                "audio_mod": 1,
            },
            "end": {
                "c": (-1.7810844610161822+2.729043964254327e-07j),
                # "radius": 0.00088688411246, #  0.00330763749309,  # 1.70280390934e-05,
                "radius": 0.002,
                "audio_mod": 0.02,
            },
            "radius_space": "-log",
            "audio_mod": {
                "c_real": 0.002,
            },
            "skip_real": True,
            "max_iter": 2048,
        },
        "tr1": {
            "begin": {
                "c": -1.7822231418976315+2.729043964254327e-07j,
                "radius": 0.002,
            },
            "end": {
                "c": -1.7822206200202013+2.729043964254327e-07j,
                "radius": 0.00088688411246,
            },
            "radius_space": "log",
            "max_iter": 2048,
        },
        "traveling": {
            "begin": {
                "c": -1.7822206200202013+2.729043964254327e-07j,
                "radius": 0.000888688411246,
            },
            "end": {
                "c": -1.782191182216574-0j,
                "radius":  0.000888688411246,
            },
            "c_space_image": "log",
            "audio_mod": {
                "color": 2,
                "c_real": 0.000002,
            },
            "max_iter": 2048,
        },
        "tr2": {
            "begin": {
                "c": -1.7821907956568581+0j,
                "radius":  0.000888688411246,
            },
            "end": {
                "radius": 0.000281186567621,
                "c": -1.7821911201074472-1e-12j,
            },
            "max_iter": 2048,
        },
        "trippy": {
            "begin": {
                "c": -1.7821911173201472-1e-12j,
                "radius": 0.000281186567621,
            },
            "end": {
                "c": -1.7821911201074472-8e-10j,
            },
            "audio_mod": {
                "c_real": -0.00000005
            },
            "max_iter": 4096,
        },
        "zoomout": {
            "begin": {
                "c": -1.78219112855035-8e-10j,
                "radius": 0.000281186567621,
                "audio_mod": 0.1,
            },
            "end": {
                "c": -1.7821911201074472-8e-08j,
                "radius": 0.3,
                "audio_mod": 3000000,
            },
            "audio_mod": {
                "c_real": 0.0000005,
                "c_imag": 0.0000005,
            },
            "audio_mod_space": "log",
            "radius_space": "log",
        },
        "spiral": {
            "begin": {
                "c": (-0.788+0.052j),
                "radius": 0.2,
                #  "c": (-0.758+0.052j), # thighter
            },
            "end": {
                "c": (-0.7535+0.056j),
            },
            "audio_mod": {
                "c_real": 0.065,
                "c_imag": 0.04,
            },
            "skip_imag": True,
            "center": complex(-0.41, -0.0554),
            "max_iter": 600,
            "loop": True
        },
        "new": {
            "begin": {
                "c": (-1.789228770017097+9.647348357832448e-13j),
            },
            "end": {
                "c": (-1.789228770017097+9.647348357832448e-13j),
                # "c": None,
            },
            "seed": (0.4699999999999999-0.23j),
            # "only_imag": True,
            "range": 0.04,
            "center": 0,
            "max_iter": 1000,
            "radius": 9.5458991964e-06,
        }
    }
    if args.anim is None:
        mod = random.choice(modulations.values())
    else:
        mod = modulations[args.anim]

    path_steps = args.steps
    if mod.get("loop"):
        path_steps = path_steps // 2

    def get_path(begin, end, space="lin"):
        if space == "log":
            if space == "-log":
                begin, end = end, begin
            path = np.geomspace(begin, end, path_steps)
            if space == "-log":
                path = path[::-1]
        else:
            path = np.linspace(begin, end, path_steps)
        return path

    def loop_path(path):
        return np.append(np.append(path, path[:-1][::-1]), path[:1])

    mod_rad, mod_real, mod_imag, mod_pow = None, None, None, None
    if mod.get("begin") and mod.get("end"):
        if mod["begin"].get("c"):
            mod["seed"] = mod["begin"]["c"]
        if mod["begin"].get("c") and mod["end"].get("c"):
            mod_real = get_path(mod["begin"]["c"].real, mod["end"]["c"].real,
                                mod.get("c_space_real", "lin"))
            mod_imag = get_path(mod["begin"]["c"].imag, mod["end"]["c"].imag,
                                mod.get("c_space_imag", "lin"))
        if mod["begin"].get("radius") and mod["end"].get("radius"):
            mod_rad = get_path(mod["begin"]["radius"], mod["end"]["radius"],
                               mod.get("radius_space", "lin"))
        if mod["begin"].get("audio_mod"):
            mod_pow = get_path(mod["begin"]["audio_mod"],
                               mod["end"]["audio_mod"],
                               mod.get("audio_mod_space", "-log"))

    if mod.get("loop"):
        mod_real = loop_path(mod_real)
        mod_imag = loop_path(mod_imag)
        if mod_rad:
            mod_rad = loop_path(mod_rad)

    def update_view(scene, frame):
        radius = mod["begin"].get("radius", 1)
        if mod_rad is not None:
            radius = mod_rad[frame]
        center = mod.get("center")
        scene.set_view(center=center, radius=radius)
        scene.max_iter = mod.get("max_iter", args.max_iter)

        if mod.get("skip_imag"):
            seed_imag = mod["begin"]["c"].imag
        else:
            seed_imag = mod_imag[frame]
        if mod.get("skip_real"):
            seed_real = mod["begin"]["c"].real
        else:
            seed_real = mod_real[frame]
        if audio_mod and mod.get("audio_mod"):
            amod = audio_mod.get(frame + args.frame_start)
            if mod_pow is not None:
                p = mod_pow[frame]
            else:
                p = 1
            if mod["audio_mod"].get("c_imag"):
                seed_imag += amod * mod["audio_mod"]["c_imag"] * p
            if mod["audio_mod"].get("c_real"):
                seed_real += amod * mod["audio_mod"]["c_real"] * p
            if mod["audio_mod"].get("color"):
                cmod = mod["audio_mod"]["color"] * amod
                scene.color_vector = np.vectorize(args.color(args.max_iter,
                                                             cmod))

        scene.c = complex(seed_real, seed_imag)
    return update_view


def main():
    args = usage_cli_complex(worker=1)
    if not args.steps:
        print("Set --steps for the number of frame")
        exit(1)

    audio_mod = AudioMod("lm95p1.wav", 4019, 1)

    screen = Screen(args.winsize)
    scene = JuliaSet(args)
    screen.add(scene)
    clock = pygame.time.Clock()

    if not args.anim:
        args.anim = "spiral"
        audio_mod = None

    animation = jiggle(args, audio_mod)

    for frame in range(args.skip, args.steps):
        animation(scene, frame)
        scene.render(frame)
        screen.update()
        pygame.display.update()
        if args.record:
            screen.capture(args.record, frame + args.frame_start)

        clock.tick(args.fps)

    if args.video and args.record:
        import subprocess
        subprocess.Popen([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-start_number", str(args.skip),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "libvpx", "-threads", "4",
            "-b:v", "5M",
            "%s/%04d-%s.webm" % (args.record, args.skip, args.anim)
        ]).wait()


if __name__ == "__main__":
    run_main(main)
