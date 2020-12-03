// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "clif/testing/variables.h"

#include "third_party/pybind11/include/pybind11/complex.h"
#include "third_party/pybind11/include/pybind11/pybind11.h"
#include "third_party/pybind11/include/pybind11/stl.h"

namespace py = pybind11;

PYBIND11_MODULE(variables, m) {
  // Simple types
  m.attr("kMyConstInt") = clif_testing::variables::kMyConstInt;
  m.attr("const_int") = clif_testing::variables::kMyConstIntRenamed;
  m.attr("kMyConstFloat") = clif_testing::variables::kMyConstFloat;
  m.attr("kMyConstDouble") = clif_testing::variables::kMyConstDouble;
  m.attr("kMyConstBool") = clif_testing::variables::kMyConstBool;
  m.attr("kMyConstPair") = clif_testing::variables::kMyConstPair;

  // Binding vector<T>, unordered_set<T>, unordered_map<T> and other stl
  // containers can be automatically processed by pybind11.
  m.attr("kMyConstIntArray") = py::list(
      py::cast(clif_testing::variables::kMyConstIntArray));
  m.attr("kMyConstMap") = py::dict(
      py::cast(clif_testing::variables::kMyConstMap));
  m.attr("kMyConstSet") = py::set(
      py::cast(clif_testing::variables::kMyConstSet));

  // Binding complex numbers requires
  // '#include "third_party/pybind11/include/pybind11/complex.h"'
  m.attr("kMyConstComplex") = py::cast(
      clif_testing::variables::kMyConstComplex);
}
