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
#include "clif/testing/python/extend_default_value_clif_aux.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(extend_default_value, m) {
  py::class_<clif_testing::Abc, std::shared_ptr<clif_testing::Abc>>(m, "Abc")
    .def(py::init<int>(), py::arg("v"))
    .def("get_value",
       (int (clif_testing::Abc::*)())&clif_testing::Abc::get_value)
    .def("sum_and_set_values",
       (void (*)(clif_testing::Abc&, int, int))
       &clif_testing::Abc__extend__sum_and_set_values,
       py::arg("v1") = 10, py::arg("v2") = 100);

  py::class_<clif_testing::DefaultValueInConstructor,
             std::shared_ptr<clif_testing::DefaultValueInConstructor>>
      (m, "DefaultValueInConstructor")
    .def(py::init([](int v) {
      return clif_testing::DefaultValueInConstructor__extend__init__(v);
    }), py::arg("v") = 10)
    .def_readwrite("value", &clif_testing::DefaultValueInConstructor::value);
}
