#!/bin/env hy
; Licensed under the Apache License, Version 2.0 (the "License"); you may
; not use this file except in compliance with the License. You may obtain
; a copy of the License at
;
;      http://www.apache.org/licenses/LICENSE-2.0
;
; Unless required by applicable law or agreed to in writing, software
; distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
; WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
; License for the specific language governing permissions and limitations
; under the License.

;; Video generated using:
;; ./marble-menger.hy marble-menger.glsl --size 9 --wav tounex.wav --midi tounex.mid --record /tmp/

;; This fixes https://github.com/hylang/hy/issues/1753
(import hy sys)
(setv sys.executable hy.sys_executable)

(import [utils.modulations [PitchModulator NoteModulator]])
(import numpy)

(defn linspace [start end length]
  (numpy.linspace start end length))
(defn logspace [start end length]
  (numpy.logspace (numpy.log10 start) (numpy.log10 end) length))

(defmacro scene [end &rest body]
  `(do
     (when (and (>= frame begin) (< frame ~end))
       (setv scene-length (- ~end begin))
       (setv scene-pos (- frame begin))
       ~@body)
     (setv begin ~end)))
(defmacro pan [proc start stop]
  `(get (~proc ~start ~stop scene-length) scene-pos))

(defn anim [params]
  ;; Starting parameters
  (assoc params
         "horizontal_angle" 90.
         "vertical_angle" 90.
         "iFracAng1" -9.3
         "iFracAng2" -0.21659701378741286
         "iFracShift" [-3.57 0.09 2.95]
         "iFracCol" [.75 .55 .50]
         "distance" 4.2)
  (defn set-param [name value]
    (assoc params name value))
  (defn update [name change]
    (set-param name (+ (get params name) change)))
  (defn update-list [name index change]
    (assoc (get params name)
           index
           (+ (get (get params name) index) change)))
  (setv midi-mod
        {
         "bass" (PitchModulator "DirtyBass" :decay 40)
         "piano" (PitchModulator "SpacePiano1")
         "piano-high" (PitchModulator "SpacePiano")
         "nap" (PitchModulator "Nap TEST" :decay 120)
         "kick" (NoteModulator "Redrum 1 copy" 36)
         "snare" (NoteModulator "Redrum 1 copy" 37)
         "high-hat" (NoteModulator "Redrum 1 copy" 43 :decay 2)
         "open-hat" (NoteModulator "Redrum 1 copy" 40 :decay 5)
         })
  (fn [frame audio-events midi-events]
    (setv begin 0)
    ;; TODO: figure out a macro to generate those variables
    (setv piano ((get midi-mod "piano") midi-events))
    (setv piano-high ((get midi-mod "piano-high") midi-events))
    (setv nap ((get midi-mod "nap") midi-events))
    (setv bass ((get midi-mod "bass") midi-events))
    (setv snare ((get midi-mod "snare") midi-events))
    (setv kick ((get midi-mod "kick") midi-events))
    (setv high-hat ((get midi-mod "high-hat") midi-events))
    (setv open-hat ((get midi-mod "open-hat") midi-events))

    (scene 898
           (update "iFracAng1" (- (/ piano 750)))
           (update "iFracAng2" (/ piano-high 100))
           (update-list "iFracShift" 0 (/ kick 5000)))
           ;(update-list "iFracShift" 2 (/ high-hat 10000)))
    (scene 1350
           ;(update "iFracAng1" (- (/ snare 10000)))
           ;(update-list "iFracShift" 0 (- (/ kick 5000)))
           (update-list "iFracShift" 1 (- (/ kick 5000)))
           (update-list "iFracShift" 0 (- (/ snare 10000)))
           ;(update-list "iFracShift" 2 (- (/ high-hat 5000)))
           (update "iFracAng1" (- (/ bass 100))))
           ;(update "iFracAng2" (/ piano-high 100))
           ;(update "distance" 0.005))
    (scene 1498
           (set-param "distance" (pan logspace 4.2 4.79))
           (update "iFracAng2" (- (/ piano 130)))
           ;(update "iFracAng2" (/ piano-high 50))
           )
    (scene 1950
           (update "iFracAng2" (- (/ piano 200)))
           ;(update "iFracAng1" (- (/ open-hat 300000)))
           (update-list "iFracShift" 0 (- (/ bass 300)))
           (update-list "iFracShift" 2 (- (/ kick 10000))))
    (scene 2098
           (set-param "distance" (pan logspace 4.79 7.9))
           (update "iFracAng2" (* piano (pan linspace 1e-4 1e-2)))
           ;(set-param "iFracAng2" (pan linspace -0.27761356191471925 -0.32))
           )
    (scene 3092
           (update "iFracAng1" (/ piano 200))
           (update "iFracAng2" (- (/ piano-high 100)))
           (update "iFracAng1" (/ nap 200))
           (update-list "iFracShift" 2 (- (/ kick 10000))))
    (scene 4350
           (update "iFracAng1" (/ bass 80))
           (update "iFracAng2" (/ nap 100))
           (update-list "iFracShift" 1 (/ snare 1000))
           (update-list "iFracShift" 2 (/ piano 300)))
    (when (> frame 3975)
      (update "distance" -0.01)
      (update-list "iFracShift" 1 0.008))
    (when (> frame 2098)
      (update "horizontal_angle" -0.3)
      (update "vertical_angle" 0.2))
    (if (>= frame 4350)
        (return "over"))))

(import utils.gamegl)
(utils.gamegl.main anim)
