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

(import [utils.gamegl [usage FragmentShader]]
        [utils.audio [Audio SpectroGram]]
        [utils.modulations [AudioModulator]])

(defn shader [&optional map-mode super-sampling]
  ;; TODO write a hy2glsl converter :)
  (.format #[[
#extension GL_NV_gpu_shader_fp64 : require

    uniform vec2 iResolution;
    uniform dvec2 seed;
    uniform float {prefix}range;
    uniform vec2 {prefix}center;
    uniform float color_power; // slider[0.1,20.0,0.01] 50.
    float l2 = log(2.);

    #define AA {aa}
    #define MAX_ITER 512.
    void main(void) {{
      vec3 col = vec3(0.0);
      #if AA>1
      for( int m=0; m<AA; m++ )
      for( int n=0; n<AA; n++ ) {{
        vec2 o = vec2(float(m), float(n)) / float(AA) - 0.5;
        vec2 uv = (gl_FragCoord.xy+o) / iResolution.xy * 2. - 1.;
      #else
      vec2 uv = gl_FragCoord.xy/iResolution.xy * 2. - 1.;
      #endif
      uv.y *= -iResolution.y / iResolution.x;
      f64vec2 pos = {prefix}center + f64vec2(uv.xy) * {prefix}range;
      f64vec2 z = {z_value};
      f64vec2 c = {c_value};
      float vtrap = 1e20;
      float htrap = 1e20;
      float idx = 0.0;
      while (idx++ < MAX_ITER) {{
        z = abs(z);
        z = f64vec2( z.x*z.x - z.y*z.y, 2.0*z.x*z.y ) + c;
        htrap = min(htrap, float(abs(z.x)));
        vtrap = min(vtrap, float(abs(z.y)));
        if (dot(z, z) > 500.)
          break;
      }}
      float r = (idx - log(log(float(dot(z, z))) / log(MAX_ITER/2.)) / l2) / MAX_ITER;
      col += vec3(.5) + vec3(.5) * cos(6.2 * (r * color_power +
             vec3(0.2 + 0.1 * clamp(vtrap, 0.0, 1.0), 0.15 + 0.1 * clamp(htrap, 0.0, 1.0), 0.30)));
      #if AA>1
      }}
      col /= float(AA*AA);
      #endif
      gl_FragColor = vec4(col, 1.0 );
    }}
]]
           :z-value (if map-mode "vec2(0.)" "pos")
           :c-value (if map-mode "pos" "seed")
           :prefix (if map-mode "map_" "")
           :aa super-sampling
           ))

;; TODO: move those common procedures to a module
(defn linspace [start end length]
  (numpy.linspace start end length))
(defn logspace [start end length]
  (numpy.logspace (numpy.log10 start) (numpy.log10 end) length))

(defmacro scene [name end &rest body]
  `(do
     (setv scene-idx (inc scene-idx))
     (when (and (>= frame begin) (< frame ~end))
       (setv scene-name ~name)
       (setv scene-length (- ~end begin))
       (setv scene-pos (- frame begin))
       (setv scene-ratio (/ scene-pos scene-length))
       ~@body)
     (when (= frame ~end)
       (setv (get prev-seed 0) (get (get params "seed") 0)
             (get prev-seed 1) (get (get params "seed") 1)))
     (setv begin ~end)))
(defmacro pan [proc start stop]
  `(get (~proc ~start ~stop scene-length) scene-pos))
(defmacro move [object mod start stop]
  `(do
     (setv modulation-total
           (get (get pre-compute (str (quote ~mod))) (- scene-idx 1)))
     (setv move-ratio (* (/ (- ~stop ~start) modulation-total) ~mod))
     (setv ~object (+ ~object move-ratio))))

;; The main animation code
(defn anim [params audio]
  (defn set-param [name value]
    (assoc params name value))
  (defn update [name change]
    (set-param name (+ (get params name) change)))
  (defn update-list [name index change]
    (assoc (get params name)
           index
           (+ (get (get params name) index) change)))

  (setv audio-mod
        {
         "hgh" (AudioModulator [631 836] :peak True)
         "mid" (AudioModulator [125 200] :peak True)
         "low" (AudioModulator [0 11])})

  ;; Pre-compute scene modulation content to be used by the move macro
  (setv pre-compute
        {
         "hgh" []
         "mid" []
         "low" []})
  (setv audio.play False idx 0)
  ;; TODO: figure out a macro to define scene and pre-compute the modulation
  (for [scene [1796 2396 2996 4670 4796 7123]]
    (setv hgh 0 mid 0 low 0)
    (for [frame (range idx scene)]
      (spectre.transform (audio.get frame))
      (setv
        low (+ low ((get audio-mod "low") spectre))
        mid (+ mid ((get audio-mod "mid") spectre))
        hgh (+ hgh ((get audio-mod "hgh") spectre))))
    (setv idx scene)
    (.append (get pre-compute "low") low)
    (.append (get pre-compute "mid") mid)
    (.append (get pre-compute "hgh") hgh))

  ;; Starting parameters
  (setv prev-seed [-6.0 -4.55])
  (assoc params
         "map_center" [-1.6148519961054462 -2.073398906791356]
         "map_range" 7.38
         "center" [0. 0.]
         "range" 4.96
         "seed" [(get prev-seed 0) (get prev-seed 1)]
         "color_power" 62.0
         )
  (fn [frame]
    (try
      (spectre.transform (audio.get frame))
      (except [] True))
    (setv begin 0 scene-idx 0)
    (setv hgh ((get audio-mod "hgh") spectre))
    (setv mid ((get audio-mod "mid") spectre))
    (setv low ((get audio-mod "low") spectre))
    (scene "intro" 1796
           (move (get (get params "seed") 0) hgh (get prev-seed 0)
                 -1.7400857336560096)
           (move (get (get params "seed") 1) low (get prev-seed 1)
                 -0.7036086001975116)
           (move (get params "range") mid 4.96 2.16)
           (set-param "map_range" (pan logspace 7.38 0.2))
           (set-param "color_power" (pan logspace 162. 100.)))
    (scene "intro-cont" 2396
           (when (= scene-pos 0)
             (global next)
             (setv next [-1.6280513765201399 -0.06548933900409834]))
           (move (get params "color_power") low 100. 22.)
           (move (get (get params "seed") 0) low (get prev-seed 0) (get next 0))
           (move (get (get params "seed") 1) hgh (get prev-seed 1) (get next 1))
           (move (get params "range") mid 2.16 0.7))
    (scene "bass" 2996
           (when (= scene-pos 0)
             (setv next [-1.625865025428295, -0.0424483921237513])
             (assoc params "bseed" [(get (get params "seed") 0)
                                    (get (get params "seed") 1)])
             (setv (get params "map_range") 0.01105996425883859))
           (move (get params "color_power") mid 22. 5.0)
           (move (get (get params "bseed") 0) low (get prev-seed 0)
                 (get next 0))
           (move (get (get params "seed") 1) hgh (get prev-seed 1) (get next 1))
           (setv (get (get params "seed") 0) (+ (get (get params "bseed") 0)
                                                (* low 1e-2 (- 1 scene-ratio))))
           (move (get params "range") mid 0.7 0.01))
    (scene "bass-cont" 4670
           (setv next [-1.6259301585032708, -0.04230095973851092])
           (move (get (get params "seed") 0) low (get prev-seed 0) (get next 0))
           (move (get (get params "seed") 1) hgh (get prev-seed 1) (get next 1))
           ;(move (get params "color_power") mid 12.8 7.4)
           )
    (scene "zoom" 4796
           (update-list "seed" 0 (* hgh 1e-9))
           (setv (get params "map_range") 4.729575480846773e-07)
           (move (get params "color_power") mid 5.0 9.0)
           (set-param "range" (pan logspace 0.010000000000000507
                                   0.00020000000000049164))
           )
    (scene "main" 7123
           (setv next [-1.6259302648185674, -0.04230098494239652])
           (move (get (get params "seed") 0) hgh (get prev-seed 0) (get next 0))
           (move (get (get params "seed") 1) low (get prev-seed 1) (get next 1))
           (move (get params "color_power") mid 5.2
                 (if (< frame 6650) 5.2 -14.5)))
    (scene "end" 7550
           (set-param "range" (pan logspace 0.0002 0.48))
           (update-list "seed" 0 (* -1e-7 (/ scene-pos scene-length)))
           (update "color_power" (* 1e-1 (/ scene-pos scene-length))))
    (scene "outro" 7800
           (set-param "range" (pan logspace 0.48 .9))
           (update-list "seed" 0 -3e-3)
           )
    (when (and (> frame 5540) (< frame 6044))
      (update "color_power" (- (* (get params "color_power") 2e-4))))
    ))


(setv args (usage))
(.update args.params
         {"mods" {"color_power" {"type" "ratio"
                                 "sliders" True
                                 "min" 0
                                 "max" 150
                                 "resolution" 0.1}}})

(setv
  audio (Audio args.wav args.fps)
  spectre (SpectroGram audio.blocksize)
  mod (anim args.params audio)
  scene (FragmentShader args (shader :super-sampling args.super-sampling)
                        :title "Fractal")
  mapscene (if (not args.record)
               (FragmentShader args (shader :map-mode True :super-sampling 1)
                               :winsize (list (numpy.divide args.winsize 4))
                               :title "Map"))
  backend glumpy.app.__backend__
  clock (glumpy.app.__init__ :backend backend :framerate args.fps)
  scene.alive True
  frame args.skip)

(setv audio.play False)
(for [skip (range args.skip)]
  (mod skip))
(setv audio.play (not args.record))

(while (and scene.alive (< frame 7800))
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
