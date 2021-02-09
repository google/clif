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
#include "clif/testing/python/extend_init_clif_aux.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(extend_init, m) {
  py::class_<clif_testing::TestCase1, std::shared_ptr<clif_testing::TestCase1>>
      (m, "TestCase1")
    .def(py::init([](int v) {
      return clif_testing::TestCase1__extend__init__(v);
    }), py::arg("v"))
    .def("get_value",
       (int (clif_testing::TestCase1::*)())&clif_testing::TestCase1::get_value)
    .def("set_value",
       (void (clif_testing::TestCase1::*)(int))
       &clif_testing::TestCase1::set_value, py::arg("v"));

  py::class_<clif_testing::TestCase2, std::shared_ptr<clif_testing::TestCase2>>
      (m, "TestCase2")
    .def(py::init([](int i, int j, int k) {
      return clif_testing::TestCase2__extend__init__(i, j, k);
    }), py::arg("i"), py::arg("j"), py::arg("k"))
    .def("get_i",
       (int (clif_testing::TestCase2::*)())&clif_testing::TestCase2::get_i)
    .def("set_i",
       (void (clif_testing::TestCase2::*)(int))
       &clif_testing::TestCase2::set_i, py::arg("i"))
    .def("get_j",
       (int (clif_testing::TestCase2::*)())&clif_testing::TestCase2::get_j)
    .def("set_j",
       (void (clif_testing::TestCase2::*)(int))
       &clif_testing::TestCase2::set_j, py::arg("j"))
    .def("get_k",
       (int (clif_testing::TestCase2::*)())&clif_testing::TestCase2::get_k)
    .def("set_k",
       (void (clif_testing::TestCase2::*)(int))
       &clif_testing::TestCase2::set_k, py::arg("k"));

  py::class_<clif_testing::TestCase3, std::shared_ptr<clif_testing::TestCase3>>
      (m, "TestCase3")
    .def(py::init([](int v) {
      return clif_testing::TestCase3__extend__init__(v);
    }), py::arg("v"))
    .def("get_value",
       (int (clif_testing::TestCase3::*)())&clif_testing::TestCase3::get_value)
    .def("set_value",
       (void (clif_testing::TestCase3::*)(int))
       &clif_testing::TestCase3::set_value, py::arg("v"));

  py::class_<clif_testing::TestNoDefaultConstructor,
             std::shared_ptr<clif_testing::TestNoDefaultConstructor>>
      (m, "TestNoDefaultConstructor")
    .def(py::init([]() {
      return clif_testing::TestNoDefaultConstructor__extend__init__();
    }))
    .def("get_value",
       (int (clif_testing::TestNoDefaultConstructor::*)())
       &clif_testing::TestNoDefaultConstructor::get_value)
    .def("set_value",
       (void (clif_testing::TestNoDefaultConstructor::*)(int))
       &clif_testing::TestNoDefaultConstructor::set_value, py::arg("v"));
}
