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

;; This fixes https://github.com/hylang/hy/issues/1753
(import glumpy hy sys os io json time numpy subprocess)
(setv sys.executable hy.sys_executable)

(import [utils.hy2glsl [hy2glsl library]]
        [utils.gamegl [usage FragmentShader]]
        [utils.audio [Audio SpectroGram]]
        [utils.midi [Midi]]
        [utils.modulations [combine PitchModulator]])

(defn shader [&optional map-mode super-sampling]
  (setv max-iter 64.0
        color-ratio 50.2
        blue  '(vec3 0.373 0.694 0.961)
        red   '(vec3 0.824 0.235 0.306)
        white '(vec3 0.918 0.961 0.980)
        color
        `(shader
           (uniform float trap1_offset)
           (uniform float trap2_offset)
           (uniform float color_power)
           ~(when (not map-mode) '(uniform vec2 seed))
           (defn color [coord]
             (setv idx 0.0)
             (setv z ~(if-not map-mode 'coord '(vec2 0.0)))
             (setv c ~(if-not map-mode 'seed 'coord))
             (setv ci 0.0)
             ;; Orbit trap based on https://www.shadertoy.com/view/4lGXDK
             ;; Created by Piotr Borys - utak3r/2017
             (setv trap (vec4 1e20))
             (while (< idx ~max-iter)
               (setv z.y (abs z.y))
               (setv z (cLog (+ z c)))
               (setv trap
                     (min trap
                          (vec4
                            (abs (+ z.y (* 0.5 (sin (+ trap1_offset z.x)))))
                            (abs (+ z.x (* 0.5 (sin (+ trap2_offset z.y)))))
                            (dot z z)
                            (length (- (fract z) 0.5)))))
               (setv ci (+ ci (length z)))
               (setv idx (+ idx 1.0)))
             (setv ci (- 1.0 (log2 (* 0.5 (log2 (/ ci color_power))))))
             ;(setv col (vec3 trap.w))
             (setv col (vec3 ci))
             (setv col (mix col ~blue  (min 1.0 (pow (* 0.5 trap.x) 0.50))))
             (setv col (mix col ~white (min 1.0 (pow (* 10.5 trap.y) 0.50))))
             (setv col (mix col ~red (- 1.0 (min 1.0
                                                 (pow (* 1.00 trap.z) 0.15)))))
             (return (pow (* col col) (vec3 1.3))))))
  (hy2glsl
    (library.fragment-plane color
                            :invert-xy (not map-mode)
                            :super-sampling super-sampling
                            :center-name (if map-mode 'map_center 'center)
                            :range-name (if map-mode 'map_range 'range))))

;; TODO: move those common procedures to a module
(defn linspace [start end length]
  (numpy.linspace start end length))
(defn logspace [start end length]
  (numpy.logspace (numpy.log10 start) (numpy.log10 end) length))

(defmacro scene [name next &rest body]
  `(do
     (setv scene-idx (inc scene-idx))
     (when (and (>= frame begin) (< frame (get scenes ~name)))
       (setv scene-name ~name)
       (print scene-name :end ": ")
       (setv scene-length (- (get scenes ~name) begin))
       (setv scene-pos (- frame begin))
       (setv scene-ratio (/ scene-pos scene-length))
       (setv next ~next)
       (when (= scene-pos 0)
         (assoc params "base-seed" [(get (get params "seed") 0)
                                    (get (get params "seed") 1)]))
       ~@body)
     (when (= frame (get scenes ~name))
       (setv (get prev-seed 0) (get (get params "seed") 0)
             (get prev-seed 1) (get (get params "seed") 1)))
     (setv begin (get scenes ~name))))
(defmacro pan [proc start stop]
  `(get (~proc ~start ~stop scene-length) scene-pos))
(defmacro move [object mod start stop]
  `(do
     (setv modulation-total
           (get (get pre-compute (str (quote ~mod))) (- scene-idx 1)))
     (setv move-ratio (* (/ (- ~stop ~start) modulation-total) ~mod))
     (setv ~object (+ ~object move-ratio))))
(defmacro move-seed [axis mod &optional offset]
  `(do
     (move (get (get params ~(if offset "base-seed" "seed")) ~axis) ~mod
           (get prev-seed ~axis) (get next ~axis))
     ~(when offset
        `(setv (get (get params "seed") ~axis)
               (+ (get (get params "base-seed") ~axis)
                  ~offset)))))

;; The main animation code
(defn anim [params audio midi]
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
         "bass" (PitchModulator "livet bass" :decay 20)
         "bass-comp" (PitchModulator "livet LCH")
         "scream" (PitchModulator "livet HCH")
         "rhode" (PitchModulator "livet FX")
         "snare" (PitchModulator "psy snare" :decay 30)
         "perc" (combine (PitchModulator "Big kit kick")
                         (PitchModulator "Teckno KICK"))
         })
  (setv scenes {
                "intro" 500
                "verse1" 1000
                "verse2" 1749
                "verse3" 2499
                "verse4" 2750
                "verse5" 2999
                "verse6" 3249
                "outro" 3500
                "ending" 3700
               })

  ;; Pre-compute scene modulation content to be used by the move macro
  (setv pre-compute {})
  (for [mod midi-mod]
    (assoc pre-compute mod []))
  (setv audio.play False idx 0)
  (for [scene (sorted (.values scenes))]
    (setv scene-amount {})
    (for [mod midi-mod]
      (assoc scene-amount mod 0))
    (for [frame (range idx scene)]
      (setv midi-events (.get midi (+ 124 frame)))
      (for [mod midi-mod]
        (assoc scene-amount mod (+ (get scene-amount mod)
                                   ((get midi-mod mod) midi-events)))))
    (setv idx scene)
    (for [mod midi-mod]
      (.append (get pre-compute mod) (get scene-amount mod))))

  ;; Starting parameters
  (setv to-check [-0.8074846040477959, -1.1414005936145428])
  (setv prev-seed [0.27037068398348113, -0.876273440486836])
  (setv prev-seed [-0.09542549812975187, -1.130157373495923])
  (setv start-color 32.0)
  (assoc params
         "map_center" [-1.6148519961054462 -2.073398906791356]
         "map_range" 0.07
         "trap1_offset" 0.0
         "trap2_offset" 0.0
         "center" [0. 1.2]
         "range" 1626.
         "seed" [(get prev-seed 0) (get prev-seed 1)]
         "color_power" start-color
         )
  (fn [frame]
    (.get audio frame)
    (setv begin 0 scene-idx 0 midi-events (.get midi (+ 124 frame))
          ;; TODO: figure out a way to generate those variable
          bass-comp ((get midi-mod "bass-comp") midi-events)
          scream ((get midi-mod "scream") midi-events)
          rhode ((get midi-mod "rhode") midi-events)
          perc ((get midi-mod "perc") midi-events)
          snare ((get midi-mod "snare") midi-events)
          bass ((get midi-mod "bass") midi-events))

    (when midi-events
      (print midi-events))

    (scene "intro" [-0.7466245477796871, -1.929687395146181]
           (move-seed 0 rhode)
           (move-seed 1 bass-comp)
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* scream 1e-1))
           (set-param "range" (pan logspace 1626 56.85)))
    (scene "verse1" [-0.940858616879124, -2.049495775369529]
           (move (get params "color_power") bass start-color 24.0)
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* scream 1e-1))
           (move-seed 0 perc)
           (move-seed 1 rhode))
    (scene "verse2" [-0.963630557643355, -2.2922264636640275]
           (set-param "range" (pan logspace 56.85 4.))
           (move-seed 0 rhode (* snare -5e-2))
           (move-seed 1 perc))
    (scene "verse3" [-0.9573242729836607, -1.4460901208934784]
           (set-param "range" (pan logspace 4. 12.))
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* bass-comp -1e-1))
           (move-seed 0 rhode (* snare -1e-1))
           (move-seed 1 perc))
    (scene "verse4" to-check ; [-0.9743526071831612, -1.2923686994929036]
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* snare 1e-1))
           (set-param "range" (pan logspace 12. 52.85))
           (move-seed 0 rhode)
           (move-seed 1 perc))
    (scene "verse5" [-0.9391296705972548, -1.1983572287896447]
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* bass-comp 1e-1))
           (move-seed 0 rhode)
           (move-seed 1 perc))
    (scene "verse6" [-0.9904508087893369, -1.059220298019503]
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* bass-comp 1e-1))
           (set-param "range" (pan logspace 52.85 7.81))
           (setv (get (get params "center") 1) (pan logspace 1.2 0.87))
           (move-seed 0 perc)
           (move-seed 0 bass))
    (scene "outro" [-0.8634995209724121, -0.39352490807702245]
           (update "trap1_offset" (* bass 1e-1))
           (update "trap2_offset" (* bass-comp 1e-1))
           (move-seed 1 perc)
           (move-seed 0 rhode))
    (scene "ending" None
           (set-param "range" (pan logspace 7.81 20.0))
           (update-list "seed" 1 -1e-3)
           (update-list "seed" 0 -1e-2))))


(setv args (usage))
(.update args.params
         {"mods" {"color_power" {"type" "ratio"
                                 "sliders" True
                                 "min" 0
                                 "max" 150
                                 "resolution" 0.1}}})

(setv
  audio (Audio args.wav args.fps)
  midi (Midi args.midi args.fps)
  spectre (SpectroGram audio.blocksize)
  mod (anim args.params audio midi)
  scene (FragmentShader args (shader :super-sampling args.super-sampling)
                        :title "Fractal")
  mapscene (if (not args.record)
               (FragmentShader args (shader :map-mode True :super-sampling 1)
                               :winsize (list (numpy.divide args.winsize 4))
                               :title "Map"))
  backend glumpy.app.__backend__
  clock (glumpy.app.__init__ :backend backend :framerate args.fps)
  scene.alive True
  scene.paused args.paused
  frame args.skip)

(setv audio.play False)
(for [skip (range args.skip)]
  (mod skip))
(setv audio.play (not args.record))

(while (and scene.alive (< frame 3700))
  (setv start-time (time.monotonic)
        updated False)
  (when (not scene.paused)
      (mod frame))
  (when (scene.update frame)
    (scene.render frame)
    (scene.controller.update_sliders)
    (setv scene.draw False updated True)
    (if args.record
        (scene.capture (os.path.join args.record
                                     (.format "{:04d}.png" frame)))))
  (when (and (not args.record) scene.alive (mapscene.update frame))
    (mapscene.render frame)
    (setv mapscene.draw False))
  (when updated
    (print (.format "{:04}: {:.2f} sec '{}'"
                    frame
                    (- (time.monotonic) start-time)
                    (json.dumps (scene.controller.get) :sort_keys True))))

  (when (not scene.paused)
    (setv frame (inc frame)))
  (backend.process (clock.tick)))

(when args.record
    (setv ffmpeg-command [
                "ffmpeg"
                "-y"
                "-framerate" (str args.fps)
                "-i" (.format "{}/%04d.png" args.record)
                "-i" args.wav
                "-c:a" "libvorbis" "-c:v" "copy"
                (.format "{}/render.mp4" args.record)
                ])
    (print "Running" (.join " " ffmpeg-command))
    (.wait (subprocess.Popen ffmpeg-command)))
