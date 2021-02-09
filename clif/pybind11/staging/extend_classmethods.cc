// Copyright 2021 Google LLC
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

#include <memory>
#include "clif/testing/python/extend_classmethods_clif_aux.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(extend_classmethods, m) {
  py::class_<clif_testing::Abc, std::shared_ptr<clif_testing::Abc>>
      (m, "Abc")
    .def(py::init<>())
    .def("get_value",
       (int (clif_testing::Abc::*)())&clif_testing::Abc::get_value)
    .def_static("from_value",
       (clif_testing::Abc (*)(int))
       &clif_testing::Abc__extend__from_value, py::arg("v"))
    .def_static("get_static_value",
       (int (*)())&clif_testing::Abc__extend__get_static_value)
    .def_static("set_static_value",
       (clif_testing::Abc (*)(int))
       &clif_testing::Abc__extend__set_static_value, py::arg("v"));
}
