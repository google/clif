/*
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_EXAMPLES_EXTEND_FROM_CLIFAUX_PYTHON_EXAMPLE_CLIF_AUX_H_
#define CLIF_EXAMPLES_EXTEND_FROM_CLIFAUX_PYTHON_EXAMPLE_CLIF_AUX_H_

#include "extend_from_clifaux/example.h"

namespace clif_examples {
namespace extend_from_clifaux {

inline void MyClass__extend__g(MyClass& self) {}

inline int MyClass__extend__h(MyClass& self) { return 2; }

inline void MyClass__extend__i(MyClass& self, int x) {}

inline int MyClass__extend__j(MyClass& self, int x) { return 2 * x; }

inline int MyClass__extend__k(MyClass& self, int x, int y) { return 2 * x + y; }

}  // namespace extend_from_clifaux
}  // namespace clif_examples

#endif  // CLIF_EXAMPLES_EXTEND_FROM_CLIFAUX_PYTHON_EXAMPLE_CLIF_AUX_H_
