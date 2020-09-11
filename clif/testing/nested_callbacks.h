/*
 * Copyright 2019 Google Inc.
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
#ifndef CLIF_TESTING_NESTED_CALLBACKS_H_
#define CLIF_TESTING_NESTED_CALLBACKS_H_

#include <functional>

namespace clif_testing_nested_callbacks {

inline int times10(int num) { return num * 10; }

inline int nested_cb(std::function<int(std::function<int(int)>, int)> cb,
                     int num) {
  return cb(times10, num + 2);
}

// Based on cl/272290922.
class VirtualBase {
 public:
  virtual ~VirtualBase() {}
  virtual int virtual_method(std::function<int(int)> cb, int num) const = 0;
};

inline int call_virtual_method_from_cpp(const VirtualBase& vb) {
  return vb.virtual_method(times10, 3) + 4;
}

}  // namespace clif_testing_nested_callbacks

#endif  // CLIF_TESTING_NESTED_CALLBACKS_H_
