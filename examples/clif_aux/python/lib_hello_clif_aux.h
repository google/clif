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
#ifndef THIRD_PARTY_CLIF_EXAMPLES_CLIF_AUX_PYTHON_LIB_HELLO_CLIF_AUX_H_
#define THIRD_PARTY_CLIF_EXAMPLES_CLIF_AUX_PYTHON_LIB_HELLO_CLIF_AUX_H_

#include <string>

#include "clif_aux/lib_hello.h"

namespace clif_examples {
namespace clif_aux {

inline std::string hello_and_bye(const std::string& who) {
  return hello(who) + " Bye, " + who + "!";
}

}  // namespace clif_aux
}  // namespace clif_examples

#endif  // THIRD_PARTY_CLIF_EXAMPLES_CLIF_AUX_PYTHON_LIB_HELLO_CLIF_AUX_H_
