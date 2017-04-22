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
#ifndef CLIF_EXAMPLES_WRAPPOD_WRAPPOD_H_
#define CLIF_EXAMPLES_WRAPPOD_WRAPPOD_H_

#include <string>
#include <vector>

namespace clif_example {
namespace wrappod {

struct MyClass {
 public:
  int a;  // Available in Python as an int value
  float f;  // Available in Python as a float value
  std::string s;  // Available in Python as a bytes object

  std::vector<int> v;  // Available in Python as a list of int values via
                       // getter and setter methods.
  std::pair<int, int> p;  // Available in Python as a 2-tuple

  double d;  // Not available in wrapped Python.
};

}  // namespace wrappod
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_WRAPPOD_WRAPPOD_H_
