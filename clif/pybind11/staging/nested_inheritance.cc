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

#include "clif/testing/nested_inheritance.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(nested_inheritance, m) {
  py::class_<::clif_testing::Nested> nested(m, "Nested");
  nested.def(py::init<>());
  nested.def_property("a", &::clif_testing::Nested::get_a,
                      &::clif_testing::Nested::set_a);

  py::class_<::clif_testing::Nested::Inner> nested_inner(nested, "Inner");
  nested_inner.def(py::init<>());
  nested_inner.def_property("a", &::clif_testing::Nested::Inner::get_a,
                            &::clif_testing::Nested::Inner::set_a);

  py::class_<::clif_testing::InheritInner, ::clif_testing::Nested::Inner>
    inheritinner(m, "InheritInner");
  inheritinner.def(py::init<>());
}
