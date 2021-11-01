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
#ifndef CLIF_TESTING_PYTHON_EXTEND_FROM_CLIFAUX_CLIF_AUX_H_
#define CLIF_TESTING_PYTHON_EXTEND_FROM_CLIFAUX_CLIF_AUX_H_

#include <Python.h>

#include <memory>

#include "clif/testing/extend_from_clifaux.h"

namespace clif_testing {
namespace extend_from_clifaux {

inline void WhatHappened__extend__void_raw_ptr(WhatHappened* self) {
  self->Record("* -> void");
}
inline void WhatHappened__extend__void_shared_ptr(
    std::shared_ptr<WhatHappened> self) {
  self->Record("shared_ptr -> void");
}
inline void WhatHappened__extend__void_by_value(WhatHappened self) {
  self.Record("will get lost");
}
inline void WhatHappened__extend__void_cref(const WhatHappened& self) {
  self.Record("const& -> void");
}
inline void WhatHappened__extend__void_ref(WhatHappened& self) {
  self.Record("& -> void");
}

inline int WhatHappened__extend__int_raw_ptr(WhatHappened* self) {
  self->Record("* -> int");
  return 1;
}
inline int WhatHappened__extend__int_shared_ptr(
    std::shared_ptr<WhatHappened> self) {
  self->Record("shared_ptr -> int");
  return 2;
}
inline int WhatHappened__extend__int_by_value(WhatHappened self) {
  self.Record("will get lost");
  return 3;
}
inline int WhatHappened__extend__int_cref(const WhatHappened& self) {
  self.Record("const& -> int");
  return 4;
}
inline int WhatHappened__extend__int_ref(WhatHappened& self) {
  self.Record("& -> int");
  return 5;
}

inline void WhatHappened__extend__void_raw_ptr_int(WhatHappened* self, int i) {
  self->Record("*, " + std::to_string(i) + " -> void");
}
inline void WhatHappened__extend__void_shared_ptr_int(
    std::shared_ptr<WhatHappened> self, int i) {
  self->Record("shared_ptr, " + std::to_string(i) + " -> void");
}
inline void WhatHappened__extend__void_by_value_int(WhatHappened self, int i) {
  self.Record("will get lost");
}
inline void WhatHappened__extend__void_cref_int(const WhatHappened& self,
                                                int i) {
  self.Record("const&, " + std::to_string(i) + " -> void");
}
inline void WhatHappened__extend__void_ref_int(WhatHappened& self, int i) {
  self.Record("&, " + std::to_string(i) + " -> void");
}

inline int WhatHappened__extend__int_raw_ptr_int(WhatHappened* self, int i) {
  self->Record("*, " + std::to_string(i) + " -> int");
  return 1;
}
inline int WhatHappened__extend__int_shared_ptr_int(
    std::shared_ptr<WhatHappened> self, int i) {
  self->Record("shared_ptr, " + std::to_string(i) + " -> int");
  return 2;
}
inline int WhatHappened__extend__int_by_value_int(WhatHappened self, int i) {
  self.Record("will get lost");
  return 3;
}
inline int WhatHappened__extend__int_cref_int(const WhatHappened& self, int i) {
  self.Record("const&, " + std::to_string(i) + " -> int");
  return 4;
}
inline int WhatHappened__extend__int_ref_int(WhatHappened& self, int i) {
  self.Record("&, " + std::to_string(i) + " -> int");
  return 5;
}

inline int WhatHappened__extend__int_raw_ptr_int_int(WhatHappened* self, int i,
                                                     int j) {
  self->Record("*, " + std::to_string(i + j) + " -> int");
  return 1;
}
inline int WhatHappened__extend__int_shared_ptr_int_int(
    std::shared_ptr<WhatHappened> self, int i, int j) {
  self->Record("shared_ptr, " + std::to_string(i + j) + " -> int");
  return 2;
}
inline int WhatHappened__extend__int_by_value_int_int(WhatHappened self, int i,
                                                      int j) {
  self.Record("will get lost");
  return 3;
}
inline int WhatHappened__extend__int_cref_int_int(const WhatHappened& self,
                                                  int i, int j) {
  self.Record("const&, " + std::to_string(i + j) + " -> int");
  return 4;
}
inline int WhatHappened__extend__int_ref_int_int(WhatHappened& self, int i,
                                                 int j) {
  self.Record("&, " + std::to_string(i + j) + " -> int");
  return 5;
}

inline int custom_function_name(WhatHappened* self, int i, int j) {
  self->Record("custom_function_name(*, " + std::to_string(i + j) + ") -> int");
  return 6;
}

namespace ns_down {

inline int function(WhatHappened* self, int i, int j) {
  self->Record("ns_down::function(*, " + std::to_string(i + j) + ") -> int");
  return 7;
}

}  // namespace ns_down

}  // namespace extend_from_clifaux

inline int ns_up_function(extend_from_clifaux::WhatHappened* self, int i,
                          int j) {
  self->Record("ns_up_function(*, " + std::to_string(i + j) + ") -> int");
  return 8;
}

namespace extend_from_clifaux {

inline int RenamedForPython__extend__int_raw_ptr_int_int(ToBeRenamed* self,
                                                         int i, int j) {
  self->Record("ToBeRenamed*, " + std::to_string(i + j) + " -> int");
  return 11;
}

// Unique name needed. The matcher gets confused otherwise.
inline int tbr_custom_function_name(ToBeRenamed* self, int i, int j) {
  self->Record("tbr_custom_function_name(ToBeRenamed*, " +
               std::to_string(i + j) + ") -> int");
  return 12;
}

namespace ns_down {

inline int tbr_function(ToBeRenamed* self, int i, int j) {
  self->Record("ns_down::tbr_function(ToBeRenamed*, " + std::to_string(i + j) +
               ") -> int");
  return 13;
}

}  // namespace ns_down

inline int TestNestedMethod_Inner__extend__get_value(
    const TestNestedMethod::Inner& self) {
  return self.value + 200;
}

inline TestNestedMethod::Inner
TestNestedMethod_Inner__extend__needs_qualified_names(
    const TestNestedMethod::Inner& self,
    const TestNestedMethod::Inner& other) {
  return TestNestedMethod::Inner(300 * self.value + other.value);
}

}  // namespace extend_from_clifaux

}  // namespace clif_testing

#endif  // CLIF_TESTING_PYTHON_EXTEND_FROM_CLIFAUX_CLIF_AUX_H_
