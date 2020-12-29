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

#include "clif/testing/classes.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(classes, m) {
  py::class_<clif_testing::classes::K>(m, "Klass")
    .def(py::init<int>())
    .def_readonly_static("C", &clif_testing::classes::K::C)
    .def_static("C2", &clif_testing::classes::K::getCplus2)
    .def("Int1", &clif_testing::classes::K::i1)
    .def_property("i", &clif_testing::classes::K::get,
                  &clif_testing::classes::K::set)
    .def_property_readonly("i2", &clif_testing::classes::K::get2);

  py::class_<clif_testing::classes::Derived, clif_testing::classes::K>(
    m, "Derived", "This class also has a docstring.\n\n      It spans multiple lines.  Plus trailing whitespace.\n\n      None of that should be a problem for the code generator that shoves\n      this text into the tp_doc char* slot C string in the generated code.")  // NOLINT
    // We cannot just simply generate `.def(py::init<>())`, because the Derived
    // class has a constructor with default value for the first parameter.
    .def(py::init<>([]() {
      return clif_testing::classes::Derived();
    }))
    .def("Init", [](int i, int j) {
      return clif_testing::classes::Derived(i, j);
    })
    .def_readwrite("j", &clif_testing::classes::Derived::j)
    .def("__contains__", &clif_testing::classes::Derived::has);
}
