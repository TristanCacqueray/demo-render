;; hy2glsl -- Hy to GLSL Language Translator
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

;; Missing core procedures discussed in: https://github.com/hylang/hy/pull/1762
(defn expression? [e]
  (instance? HyExpression e))
(defn list? [l]
  (instance? HyList l))

(setv gl-types '[int float vec2 vec3 vec4 mat2 mat3 mat4]
      gl-proc {'dot 'float 'atan 'float 'cos 'float 'sin 'float}
      builtins
      '(shader
         (defn cSquare [c]
           (vec2 (- (* c.x c.x) (* c.y c.y))
                 (* 2.0 c.x c.y)))
         (defn crDiv [r c]
           (if (<= (abs c.x) (abs c.y))
               (do
                 (setv ratio (/ c.x c.y))
                 (setv denom (* c.y (+ 1 (* ratio ratio))))
                 (return (vec2 (/ (* r ratio) denom)
                               (- (/ r denom)))))
               (do
                 (setv ratio (/ c.y c.x))
                 (setv denom (* c.x (+ 1 (* ratio ratio))))
                 (return (vec2 (/ r denom) (/ (- (* r ratio)) denom))))))
         (defn hypot [c]
           (setv x (abs c.x))
           (setv y (abs c.y))
           (setv t (min x y))
           (setv x (max x y))
           (setv t (/ t x))
           (if (and (= c.x 0.0) (= c.y 0.0))
               (return 0.0)
               (return (* x (sqrt (+ 1.0 (* t t)))))))
         (defn cAbs [c]
           (hypot c))
         (defn cPowr [c r]
           (setv x (exp (* (log (hypot c)) r)))
           (setv y (* (atan c.y c.x) r))
           (vec2 (* x (cos y)) (* x (sin y))))
         (defn cLog [c]
           (vec2 (log (hypot c)) (atan c.x c.y)))))
(defn builtin? [name]
  (for [builtin (cut builtins 1)]
    (if (= (get builtin 1) name)
        (return builtin))))

(defn hy2glsl [code]
  (setv shader []
        function-arguments-types {}
        used-builtins {})
  (defn make-gl-env []
        {"gl_FragCoord" "vec2"
         "gl_FragColor" "vec4"
         "gl_Position" "vec4"})
  (defn translate [expr env &optional [indent 0] [term True]]
    (defn append [&rest code &kwargs kwargs]
      (unless (in "no-code-gen" env)
        (.append shader (+ (* " " (* 2 (if (in "indent" kwargs)
                                           (get kwargs "indent")
                                           indent)))
                           (.join "" (map str code))))))

    ;; Environment procedures to manage variables scope
    (defn mangle-var [var-name]
      ;; GLSL '.' are valid
      (.join "." (map mangle (.split var-name '.))))
    (defn lookup [var-name &optional [env env]]
      "Return variable type from the environment"
      (setv var-name (mangle (get (.split var-name '.) 0)))
      (cond [(in var-name gl-env)
             (get gl-env var-name)]
            [(in var-name env)
             (get env var-name)]
            [True None]))
    (defn define [var-name var-type &optional [env env]]
      "Set a variable type"
      (setv var-name (mangle (get (.split var-name '.) 0)))
      (when (lookup var-name env)
        (print "warning: var" var-name "shadow the environment!"))
      (assoc env var-name (name var-type)))
    (defn copy-env [&optional [env env]]
      "Copy the environment"
      (setv result {})
      (for [k env]
        (assoc result k (get env k)))
      result)

    (defn infer-type [expr &optional [env env]]
      "Return the type of an expression"
      ;; Very primitive type inference...
      (defn infer [expr &optional [no-symbol False]]
        (cond [(and (expression? expr) (in (get expr 0) gl-types))
               (get expr 0)]
              [(and (expression? expr) (in (get expr 0) gl-proc))
               (get gl-proc (get expr 0))]
              [(expression? expr)
               ;; First look for any known variables type
               (for [e expr]
                 (setv expr-type (infer e :no-symbol True))
                 (when expr-type
                   (return expr-type)))
               ;; Then look for symbols
               (for [e expr]
                 (setv expr-type (infer e))
                 (when expr-type
                   (return expr-type)))
               ]
              [(and (not no-symbol) (float? expr))
               'float]
              [(and (not no-symbol) (integer? expr))
               'int]
              [(and (not no-symbol) (none? expr))
               'void]
              [(and (symbol? expr) (lookup expr env))
               ;; TODO: support different accessor type
               (if (or (.endswith expr '.x) (.endswith expr '.y))
                   'float
                   (lookup expr env))]
              [True None]))
      (setv inferred-type (infer expr))
      (when (not inferred-type)
        (print "Error: couldn't infer type of" expr))
      inferred-type)

    (cond [(expression? expr)
           (setv operator (get expr 0))
           (when (and used-builtins
                      (not (expression? operator))
                      (not (in operator '(shader do version uniform attribute)))
                      (not (in "no-code-gen" env)))
             ;; Inject any used-builtin first
             (setv builtins (list (.values used-builtins)))
             (.clear used-builtins)
             (for [e builtins]
               (translate e env)))
           (cond
             ;; Hy Functions/variables to glsl
             [(= operator 'defn)
              #_(comment
                  Syntax: (defn name [arg ...] (code))
                  )
              (when (len (get expr 2))
                ;; Function arguments type shall exists after first-pass
                ;; TODO: check for missing function call and print error
                (setv arg-types (get function-arguments-types (get expr 1))))

              ;; TODO: use translate operand to set those special environment
              (setv new-env {"in-function-body" True})
              (when (in "infer-function-type" env)
                (assoc new-env "infer-function-type" True)
                (assoc new-env "no-code-gen" True))

              ;; Add function argument to environment
              (for [arg (get expr 2)]
                (if (lookup arg new-env)
                    (print "warning: shadow var:" arg))
                (assoc new-env arg (get arg-types (.index (get expr 2) arg))))

              ;; Inject return operator if last expr is not a return
              (when (or (not (expression? (last expr)))
                        (not (in (get (last expr) 0) '[if do setv return])))
                ;; TODO: walk if/do expression to inject return there too
                (setv (get expr -1) (quasiquote
                                      (return (unquote (last expr))))))

              (setv return-type "void")
              (unless (in "infer-function-type" env)
                ;; Do a first pass on function body to discover the type of
                ;; the last expression
                (setv tmp-env (copy-env new-env))
                ;; TODO: use translate operand to set no-code-gen
                (assoc tmp-env "no-code-gen" True)
                (translate (cut expr 3) tmp-env)
                (defn get-return [expr]
                  "Get the first return expression"
                  (when (expression? expr)
                    (if (= (get expr 0) 'return)
                        (return (get expr 1))
                        (for [e expr]
                          (setv ret (get-return e))
                          (if ret (return ret)))))
                  None)
                (setv return-type (infer-type (get-return expr) tmp-env))

                ;; Add function name to global environment
                (define (get expr 1) return-type :env gl-env))

              (append "\n" :indent 0)
              (append return-type " " (mangle (get expr 1)) "("
                      (if (len (get expr 2))
                          (.join ", " (map (fn [arg]
                                             (+ (get
                                                  arg-types
                                                  (.index (get expr 2) arg))
                                                " " arg))
                                           (get expr 2)))
                          "void")
                      ") {\n")
              (translate (cut expr 3) new-env (inc indent))
              (append "}\n")]
             [(= operator 'setv)
              #_(comment
                  Syntax: (setv var value)
                  Type is inferred from the value
                  )
              (if (lookup (get expr 1))
                  (setv type-str "")
                  (do
                    (define
                      (get expr 1)
                      (infer-type (get expr 2))
                      :env (if (in "in-function-body" env) env gl-env))
                    (setv type-str (+ (lookup (get expr 1)) " "))))
              (append type-str (mangle-var (get expr 1)) " = ")
              (translate (get expr 2) env :term False)
              (append ";\n" :indent 0)]

             ;; GLSL specific procedure
             [(= operator 'version)
              #_(comment
                  Syntax: (version number)
                  )
              (append "#version " (get expr 1) "\n")]
             [(= operator 'extension)
              #_(comment
                  Syntax: (extension name)
                  )
              ;; TODO: support different extension keyword like 'enable
              (append "#extension " (get expr 1) " : require\n")]
             [(= operator 'output)
              #_(comment
                  Syntax: (output type name)
                  )
              (define (mangle (get expr 2)) (get expr 1))
              (append "out " (get expr 1)
                      " " (mangle (get expr 2)) ";\n")]
             [(= operator 'uniform)
              #_(comment
                  Syntax: (uniform type name)
                  )
              (define (mangle (get expr 2)) (get expr 1) :env gl-env)
              (append "uniform " (get expr 1)
                      " " (mangle (get expr 2)) ";\n")]
             [(= operator 'attribute)
              #_(comment
                  Syntax: (attribute type name)
                  )
              (define (mangle (get expr 2)) (get expr 1) :env gl-env)
              (append "attribute " (get expr 1)
                      " " (mangle (get expr 2)) ";\n")]

             ;; Control flow
             [(= operator 'if)
              (append "if (")
              (translate (get expr 1) env :term False)
              (append ") {\n" :indent 0)
              (setv new-env (copy-env))
              (translate (get expr 2) (copy-env new-env) (inc indent))
              (append "}")
              (when (> (len expr) 3)
                (append " else {\n" :indent 0)
                (translate (get expr 3) new-env (inc indent))
                (append "}"))
              (append "\n" :indent 0)]
             [(= operator 'while)
              (append "while (")
              (translate (get expr 1) env :term False)
              (append ") {\n" :indent 0)
              (setv new-env (copy-env))
              (translate (cut expr 2) new-env (inc indent))
              (append "}\n")]
             [(= operator 'do)
              (translate (cut expr 1) env indent)]
             [(= operator 'return)
              (append "return ")
              (translate (get expr 1) env :term False)
              (append ";\n" :indent 0)]
             [(= operator 'break)
              (append "break;\n")]

             ;; Boolean logic
             [(= operator '=)
              (translate (get expr 1) env :term False)
              (append " == ")
              (translate (get expr 2) env :term False)]
             [(= operator 'or)
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " || ")
                (translate operand env :term False))]
             [(= operator 'and)
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " && ")
                (translate operand env :term False))]

             ;; Logic
             [(= operator '<)
              (translate (get expr 1) env :term False)
              (append " < ")
              (translate (get expr 2) env :term False)]
             [(= operator '>)
              (translate (get expr 1) env :term False)
              (append " > ")
              (translate (get expr 2) env :term False)]
             [(= operator '<=)
              (translate (get expr 1) env :term False)
              (append " <= ")
              (translate (get expr 2) env :term False)]
             [(= operator '>=)
              (translate (get expr 1) env :term False)
              (append " >= ")
              (translate (get expr 2) env :term False)]

             ;; Arithmetic
             [(= operator '+)
              (append "(")
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " + ")
                (translate operand env :term False))
              (append ")")]
             [(= operator '-)
              (if (= (len expr) 2)
                  (append "-")
                  (append "("))
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " - ")
                (translate operand env :term False))
              (when (not (= (len expr) 2))
                (append ")"))]
             [(= operator '*)
              (append "(")
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " * ")
                (translate operand env :term False))
              (append ")")]
             [(= operator '/)
              (append "(")
              (translate (get expr 1) env :term False)
              (for [operand (cut expr 2)]
                (append " / ")
                (translate operand env :term False))
              (append ")")]

             ;; Member access
             [(and (symbol? operator) (= (get operator 0) '.))
              (append (get expr 1) operator)]

             ;; Function call
             [(symbol? operator)
              ;; TODO: check for unknown function
              (when (in "infer-function-type" env)
                (assoc function-arguments-types operator [])
                (for [operand (cut expr 1)]
                  (.append
                    (get function-arguments-types operator)
                    (infer-type operand)))
                (setv builtin (builtin? operator))
                (when (and builtin (not (in operator used-builtins)))
                  (translate builtin env)
                  (assoc used-builtins operator builtin)))
              (append (mangle operator) "(")
              (when (> (len expr) 1)
                (translate (get expr 1) env :term False))
              (for [operand (cut expr 2)]
                (append ", ")
                (translate operand env :term False))
              (append ")" :indent 0)
              (when term (append ";\n" :indent 0))]

             [(expression? operator)
              ;; This is an expression list, like a procedure body
              (for [e expr]
                (translate e env indent))]

             [True (print "error: unknown expresion:" expr)])]

          ;; Symbols
          [(or (symbol? expr) (numeric? expr))
           (cond
             [(in expr '[True False])
              (append (if (= expr 'True) 'true 'false))]
             [True (append expr)])]

          [True (print "error: unknown symbol:" expr)]))
  ;; Shift shader symbol
  (when (= (get code 0) 'shader)
    (setv code (cut code 1)))

  (defn trim-none [code]
    "Remove None expression from macro expansion"
    (setv result (HyExpression))
    (for [expr code]
      (when (= expr None)
        (continue))
      (.append result (if (expression? expr)
                          (trim-none expr)
                          expr)))
    result)
  (setv code (trim-none code))

  ;; Infer function argument type in reverse order
  (setv reverse (HyExpression) func-pos 0)
  (for [expr code]
    ;; Keep global at the top, function at the bottom in reverse order
    (setv operator (get expr 0))
    (cond [(= operator 'defn) (.insert reverse func-pos expr)]
          [True
           (.insert reverse func-pos expr)
           (setv func-pos (inc func-pos))]))
  (setv gl-env (make-gl-env))
  ;; TODO: use translate operand to set no-code-gen or infer-function-type
  (translate reverse {"no-code-gen" True "infer-function-type" True})

  (setv gl-env (make-gl-env))
  (translate code {})

  ;; Return shader string
  (.join "" shader))
