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
#ifndef CLIF_TESTING_T7_H_
#define CLIF_TESTING_T7_H_

#include <memory>
#include <string>

char settled[20] = "not set";

inline std::string get_settled() { return settled; }

inline void set_callback(std::function<std::string(int)> cb) {
  strcpy(settled, cb(1).c_str());
}

inline std::function<int()> get_callback() {
  return []() { return strlen(settled); };
}

inline std::function<int(bool)> get_callback1() {
  return [](bool v) {
    if (v)
        return static_cast<int>(strlen(settled));
    else
        return 0;
  };
}

inline int take_std_string(const std::string s) {
  return s.size();
}

inline int take_std_string_ref(const std::string& s) {
  return s.size();
}


#endif  // CLIF_TESTING_T7_H_
