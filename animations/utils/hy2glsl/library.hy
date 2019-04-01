;; hy2glsl.library -- Collection of shader
;;
;; This library is free software: you can redistribute it and/or
;; modify it under the terms of the GNU Lesser General Public License
;; as published by the Free Software Foundation, either version 3 of
;; the License, or (at your option) any later version.
;;
;; This library is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
;; Lesser General Public License for more details.
;;
;; You should have received a copy of the GNU Lesser General Public
;; License along with this program. If not, see <http://www.gnu.org/licenses/>.

(defn vertex-dumb [&optional [attribute-name 'position]]
  `(shader
     (attribute vec2 ~attribute-name)
     (defn main []
       (setv gl_Position (vec4 ~attribute-name 0. 1.)))))
(setv vertex-dumb-attributes {"position" [[-1 -1] [-1 1] [1 -1] [1 1]]})

(defn contrast-saturation-brightness [&optional
                                      [gamma 1.0]
                                      [exposure 1.0]
                                      [brightness 0.5]
                                      [contrast 0.4]]
  ;; Based on: http://mouaif.wordpress.com/2009/01/22/photoshop-gamma-correction-shader/
  (setv gamma (float gamma)
        exposure (float exposure))
  `(defn post-process [col]
     ~(unless (= exposure 1.0)
        `(setv col (* col ~exposure)))
     ~(unless (= gamma 1.0)
        `(setv col (pow col (vec3 (/ 1.0 ~gamma)))))
     (setv brightness (* col ~brightness))
     (setv intensify (vec3 (dot brightness (vec3 0.2125 0.7154 0.0721))))
     (setv saturation (mix intensify brightness ~contrast))
     (setv contrast (mix (vec3 0.5) saturation ~contrast))
     (clamp contrast 0.0 1.0)))

(defn fragment-plane [color-code &optional
                      [invert-xy False]
                      [post-process None]
                      [res-name 'iResolution]
                      [center-name 'center]
                      [range-name 'range]
                      [super-sampling 1]]
  (when (not (instance? HyExpression (get color-code 0)))
    (setv color-code (HyExpression [color-code])))
  ;; Get last function name
  (if (in (get (get color-code 0) 0) ['shader 'do])
      (setv color-code (cut (get color-code 0) 1)))
  (setv color-func-name
        (get (get (list (filter (fn [x] (and x (= (get x 0) 'defn)))
                                color-code)) 0) 1))
  `(shader
     (uniform vec2 ~res-name)
     (uniform vec2 ~center-name)
     (uniform float ~range-name)
     ~@color-code
     ~(when post-process
        post-process)
     (defn main []
       (setv col (vec3 0.0))
       ~(if (= super-sampling 1)
            `(do
              (setv uv (- (* (/ gl_FragCoord.xy (.xy ~res-name)) 2.) 1.0))
              (setv uv.y (* uv.y (- (/ (.y ~res-name) (.x ~res-name)))))
              (setv pos (+ ~center-name (* uv ~range-name)))
              ~(when invert-xy
                '(setv pos (vec2 pos.y pos.x)))
              (setv col (~color-func-name pos)))
             `(do
               (setv m 0)
               (while (< m ~super-sampling)
                 (setv n 0)
                 (while (< n ~super-sampling)
                   (setv uv
                         (- (* (/ (+ gl_FragCoord.xy
                                     (- (/ (vec2 (float m) (float n))
                                           (float ~super-sampling))
                                        0.5))
                                  (.xy ~res-name)) 2.) 1.0))
                   (setv uv.y (* uv.y (- (/ (.y ~res-name) (.x ~res-name)))))
                   (setv pos (+ ~center-name (* uv ~range-name)))
                   ~(when invert-xy
                      '(setv pos (vec2 pos.y pos.x)))
                   (setv col (+ col (~color-func-name pos)))
                   (setv n (+ n 1)))
                 (setv m (+ m 1)))
               (setv col (/ col (float (* ~super-sampling ~super-sampling))))))
       (setv gl_FragColor (vec4 ~(if post-process
                                     '(post-process col)
                                     'col)
                                1.0)))))

(defn r [color] (get color 0))
(defn g [color] (get color 1))
(defn b [color] (get color 2))

(defn color-ifs [ifs-code &optional
                 [julia False]
                 [seed [0.5 0.07]]
                 [color-type 'iq-shadertoy]
                 [color [0 0.4 0.7]]
                 [color-factor 1.0]
                 [color-ratio 1.64706]
                 [pre-iter 0]
                 [max-iter 42]
                 [escape 2]]
  (when (not (instance? HyExpression (get ifs-code 0)))
    (setv ifs-code (HyExpression [ifs-code])))
  (setv color-code None color-code-post None)
  (setv max-iter (float max-iter)
        pre-iter (float pre-iter)
        escape (** 10.0 escape)
        color-factor (float color-factor)
        color-ratio (float color-ratio))
  (cond [(= color-type 'iq-shadertoy)
         ;; Color scheme from Inigo Quilez's Shader Toy
         (setv
           color-code-post
           `(if (< idx ~max-iter)
                (do
                  (setv ci (- (+ idx 1.0) (log2 (* 0.5 (log2 (dot z z))))))
                  (setv ci (sqrt (/ ci 256.0))))
                (return (vec3 0.0))))]
        [(= color-type 'mean-mix-distance)
         (setv
           color-code
           `(if (> idx ~pre-iter)
                (setv ci (mix ci (length z) ~color-factor)))
           color-code-post
           `(setv ci (- 1.0 (log2 (* 0.5 (log2 (/ ci ~color-ratio)))))))]
        [(= color-type 'mean-distance)
         (setv
           color-code
           `(if (> idx ~pre-iter)
                (setv ci (+ ci (length z))))
           color-code-post
           `(do
              (setv ci (/ ci (- idx ~pre-iter)))
              (setv ci (- 1.0 (log2 (* 0.5 (log2 (/ ci ~color-ratio))))))))]
        [True (print "Unknown color-type" color-type)])
  `(shader
     ~(if julia '(uniform vec2 seed))
     (defn color [coord]
       (setv idx 0.0)
       (setv z ~(if julia 'coord '(vec2 0.0)))
       (setv c ~(if julia 'seed 'coord))
       (setv ci 0.0)
       (while (< idx ~max-iter)
         ~ifs-code
         ~color-code
         (if (and ~(if (> pre-iter 0) `(> idx ~pre-iter)) (> (dot z z) ~escape))
             (break))
         (setv idx (+ idx 1.0)))
       ~color-code-post
       (return (vec3
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(r color)))))
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(g color)))))
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(b color))))))))))
