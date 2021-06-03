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
#ifndef CLIF_TESTING_POSTPROC_H_
#define CLIF_TESTING_POSTPROC_H_

#include <set>
#include <string>

namespace clif_testing {

inline std::set<std::string> get_set_string(int size) {
  std::set<std::string> ss;
  for (int i = 0; i < size; i++) {
    ss.insert(std::to_string(i * 3 + 5));
  }
  return ss;
}

inline int get_one() {
  return 1;
}

inline bool add_one_if_positive(int input, int* output = nullptr) {
  if (input > 0) {
    *output = input + 1;
  } else {
    *output = input;
  }
  return input > 0;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_POSTPROC_H_
