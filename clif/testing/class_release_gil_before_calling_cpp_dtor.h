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

// Similar to pybind11/tests/test_class_release_gil_before_calling_cpp_dtor.cpp

#ifndef CLIF_TESTING_CLASS_RELEASE_GIL_BEFORE_CALLING_CPP_DTOR_H_
#define CLIF_TESTING_CLASS_RELEASE_GIL_BEFORE_CALLING_CPP_DTOR_H_

#include <Python.h>

#include <string>
#include <unordered_map>

namespace clif_testing::class_release_gil_before_calling_cpp_dtor {

using RegistryType = std::unordered_map<std::string, int>;

inline RegistryType &PyGILState_Check_Results() {
  static auto *singleton = new RegistryType();
  return *singleton;
}

struct ProbeType {
 private:
  std::string unique_key;

 public:
  explicit ProbeType(const std::string &unique_key) : unique_key{unique_key} {}

  ~ProbeType() {
    RegistryType &reg = PyGILState_Check_Results();
    assert(reg.count(unique_key) == 0);
    reg[unique_key] = PyGILState_Check();
  }
};

std::string PopPyGILState_Check_Result(const std::string &unique_key) {
  RegistryType &reg = PyGILState_Check_Results();
  if (reg.count(unique_key) == 0) {
    return "MISSING";
  }
  int res = reg[unique_key];
  reg.erase(unique_key);
  return std::to_string(res);
}

}  // namespace clif_testing::class_release_gil_before_calling_cpp_dtor

#endif  // CLIF_TESTING_CLASS_RELEASE_GIL_BEFORE_CALLING_CPP_DTOR_H_
