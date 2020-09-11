/*
 * Copyright 2017 Google Inc.
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
#ifndef CLIF_EXAMPLES_INHERITANCE_HIDDEN_BASE_H_
#define CLIF_EXAMPLES_INHERITANCE_HIDDEN_BASE_H_

#include <string>

namespace clif_example {
namespace hidden_base {

class Base {
 public:
  std::string AsString() {
    return "string_rep";
  }
};

class Derived : public Base {
};

}  // namespace hidden_base
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_INHERITANCE_HIDDEN_BASE_H_
