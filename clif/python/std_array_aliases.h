/*
 * Copyright 2024 Google LLC
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
#ifndef CLIF_PYTHON_STD_ARRAY_ALIASES_H_
#define CLIF_PYTHON_STD_ARRAY_ALIASES_H_

#include <array>

namespace clif {

// These aliases are to help working around a major PyCLIF limitation.
//
// This is best understood starting with a common simple example:
//     C++ type:
//         std::array<std::string, 3>
//
//     Corresponding binding definition in a .clif file:
//         `::clif::std_array_T_3` as list<`std::string` as bytes>
//
// The PyCLIF limitation goes back to how processing of
//
//     `cpp_container_type` as py_container_type<
//         `cpp_element_type` as py_element_type>
//
// is implemented. To run the clif_matcher, PyCLIF simply pastes the type names
// like this:
//
//     cpp_container_type<cpp_element_type>
//
// For the `std::array<std::string, 3>` example, without the helper aliases,
// the simple pasting mechanism would have to be generalized, maybe
// (speculative!):
//
//     `std::array<%, 3>` as list<`std::string` as bytes>
//
// Until something like this is implemented, the aliases below are needed as
// a workaround.

#define CLIF_LOCAL_DEFINE(N) \
  template <typename T>      \
  using std_array_T_##N = std::array<T, N>;

CLIF_LOCAL_DEFINE(1)
CLIF_LOCAL_DEFINE(2)
CLIF_LOCAL_DEFINE(3)
CLIF_LOCAL_DEFINE(4)
CLIF_LOCAL_DEFINE(5)
CLIF_LOCAL_DEFINE(6)
CLIF_LOCAL_DEFINE(7)
CLIF_LOCAL_DEFINE(8)
CLIF_LOCAL_DEFINE(9)
CLIF_LOCAL_DEFINE(10)
CLIF_LOCAL_DEFINE(11)
CLIF_LOCAL_DEFINE(12)
CLIF_LOCAL_DEFINE(13)
CLIF_LOCAL_DEFINE(14)
CLIF_LOCAL_DEFINE(15)
CLIF_LOCAL_DEFINE(16)
CLIF_LOCAL_DEFINE(17)

#undef CLIF_LOCAL_DEFINE

}  // namespace clif

#endif  // CLIF_PYTHON_STD_ARRAY_ALIASES_H_
