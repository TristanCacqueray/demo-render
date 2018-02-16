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
Multiplication table on a circle as explained in
https://www.youtube.com/watch?v=-X49VQgi86E
"""

import colorsys
import math

import pygame
from pygame.locals import KEYUP, K_ESCAPE, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_p
import pygame.draw
import pygame.image

WINSIZE = [800,  800]
CENTER = list(map(lambda x: x/2, WINSIZE))
RADIUS = WINSIZE[0] / 2 - 2


def circle_point(mod, point, radius=RADIUS):
    # Return coordinate of a point on a mod circle
    angle = ((point % mod) * 360 / float(mod)) * math.pi / 180.0
    return (int(CENTER[0] + radius * math.sin(angle)),
            int(CENTER[1] + radius * math.cos(angle)))


def draw_msg(msg, coord=(5, 780), color=(180, 180, 255)):
    text = font.render(msg, True, color)
    screen.blit(text, coord)


class CircleRender:
    def __init__(self, mod, start_mult, step, hue=0.4):
        self.mod, self.mult, self.step, self.hue = mod, start_mult, step, hue

    def draw(self, frame):
        for j in range(1, self.mod):
            # Draw a line between two mult points
            s = circle_point(self.mod, j)
            d = circle_point(self.mod, j * self.mult)
            hue = self.hue + (j % 100) / 300.0
            color = list(map(lambda x: x * 255, colorsys.hsv_to_rgb(
                hue, 0.5, 0.2 + j / (float(self.mod)*1.5))))
            pygame.draw.line(screen, color, s, d, 1)
        self.mult += self.step


clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode(WINSIZE)
font = pygame.font.SysFont(u'dejavusansmono', 12)

frame = 0
scene = CircleRender(mod=701, start_mult=70, step=0.01, hue=0.2)
while True:
    screen.fill((0, 0, 0))

    draw_msg("Up/Down:    change mult step", coord=(5, 5))
    draw_msg("Left/Right: change mod", coord=(5, 20))
    draw_msg("p: save image", coord=(5, 35))
    draw_msg("%04d: Mod %d, Mult %.2f (step %.3f)" % (
        frame, scene.mod, scene.mult, scene.step))
    scene.draw(frame)

    pygame.display.update()
    frame += 1

    for e in pygame.event.get():
        if e.type != KEYUP:
            continue
        if e.key == K_ESCAPE:
            exit(0)
        if e.key == K_p:
            filename = "./mult%d-mod%d.png" % (scene.mult, scene.mod)
            pygame.image.save(screen, filename)
            print("Saved to %s" % filename)
        elif e.key == K_UP:
            scene.step += 0.005
        elif e.key == K_DOWN:
            scene.step -= 0.005
        elif e.key == K_LEFT:
            scene.mod -= 5
        elif e.key == K_RIGHT:
            scene.mod += 5

    clock.tick(25)
