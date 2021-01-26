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

#include "third_party/pybind11/include/pybind11/pybind11.h"

#include "clif/testing/operators.h"

#include <pybind11/operators.h>  // NOLINT

namespace py = pybind11;

PYBIND11_MODULE(operators, m) {
  py::class_<clif_ops_test::Abc>(m, "Abc")
    .def(py::init<::uint8_t, ::uint8_t>())
    .def("__bool__",
         (bool (::clif_ops_test::Abc::*)())
         &::clif_ops_test::Abc::operator bool)
    .def(py::self == py::self)  // eq
    .def(py::self != py::self)  // ne
    .def(py::self < py::self)  // lt
    .def(py::self <= py::self)  // le
    .def(py::self > py::self)  // gt
    .def(py::self >= py::self)  // ge
    .def(int_(py::self))  // int
    .def(float_(py::self))  // float
    .def(py::self += int())  // iadd
    .def("__len__",
         (int (::clif_ops_test::Abc::*)())
         &::clif_ops_test::Abc::length)  // __len__

    // This does not work for negative indexes.
    .def("__getitem__",
         (char (::clif_ops_test::Abc::*)(int))
         &::clif_ops_test::Abc::operator[])  // __getitem__
    .def("__contains__",
         (bool (*)(const ::clif_ops_test::Abc &, ::uint8_t))
         &::clif_ops_test::Abc_has, py::arg("k"));  // __getitem__

  py::class_<clif_ops_test::Num>(m, "Num")
    .def(py::init<>())
    .def(py::self + int())  // add
    .def(int() - py::self)  // rsub
    .def(py::self % int())  // mod
    .def(int() % py::self);  // rmod
}
