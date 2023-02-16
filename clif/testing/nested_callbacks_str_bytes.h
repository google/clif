/*
 * Copyright 2023 Google LLC
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
#ifndef CLIF_TESTING_NESTED_CALLBACKS_STR_BYTES_H_
#define CLIF_TESTING_NESTED_CALLBACKS_STR_BYTES_H_

#include <functional>
#include <string>
#include <utility>

// Workaround b/118736768: template arguments not namespace qualified
// TODO: Cleanup.
template <typename... T>
using function = std::function<T...>;
using string = std::string;

namespace clif_testing_nested_callbacks_str_bytes {

inline std::string level_0_si(int num) {
  return "level_0_si_" + std::to_string(num);
}

using level_1_callback_si = std::function<std::string(int)>;
using level_2_callback_si = std::function<std::string(level_1_callback_si)>;
using level_3_callback_si = std::function<std::string(level_2_callback_si)>;
using level_4_callback_si = std::function<std::string(level_3_callback_si)>;

inline std::string call_level_1_callback_si(level_1_callback_si cb) {
  return cb(1001);
}
inline std::string call_level_2_callback_si(level_2_callback_si cb) {
  return cb(level_0_si);
}
inline std::string call_level_3_callback_si(level_3_callback_si cb) {
  return cb(call_level_1_callback_si);
}
inline std::string call_level_4_callback_si(level_4_callback_si cb) {
  return cb(call_level_2_callback_si);
}

}  // namespace clif_testing_nested_callbacks_str_bytes

#endif  // CLIF_TESTING_NESTED_CALLBACKS_STR_BYTES_H_
