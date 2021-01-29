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

#include "clif/testing/number_methods.h"

#include <pybind11/operators.h>  // NOLINT

namespace py = pybind11;

PYBIND11_MODULE(number_methods, m) {
  py::class_<clif_testing::Number>(m, "Number")
    .def(py::init<int>())
    .def(py::init<float>())
    .def_readwrite("value", &clif_testing::Number::value)
    .def("__pow__",
        (clif_testing::Number (clif_testing::Number::*)(
         const clif_testing::Number*, const clif_testing::Number*))
         &clif_testing::Number::power,
         py::arg("exponent"), py::arg("modulus") = nullptr)  // __pow__
    .def("__ipow__",
        (clif_testing::Number (clif_testing::Number::*)(
         const clif_testing::Number*, const clif_testing::Number*))
         &clif_testing::Number::inplace_power,
         py::arg("exponent"), py::arg("modulus") = nullptr)  // __ipow__
    .def("__divmod__",
        (std::pair<clif_testing::Number, clif_testing::Number>
         (clif_testing::Number::*)(const clif_testing::Number&))
         &clif_testing::Number::divmod,
         py::arg("other"))  // __divmod__
    .def("__floordiv__",
        (clif_testing::Number (clif_testing::Number::*)(
         const clif_testing::Number&))
         &clif_testing::Number::floor_division,
         py::arg("other"))  // __floordiv__
    .def("__ifloordiv__",
        (clif_testing::Number (clif_testing::Number::*)(
         const clif_testing::Number&))
         &clif_testing::Number::inplace_floor_division,
         py::arg("other"))  // __ifloordiv__
    .def("__index__",
        (int (clif_testing::Number::*)())
         &clif_testing::Number::operator int)  // __index__
    .def(py::self + py::self)  // add
    .def(py::self - py::self)  // sub
    .def(py::self * py::self)  // mul
    .def(py::self / py::self)  // div, truediv
    .def(py::self % py::self)  // mod
    .def(~py::self)  // invert
    .def(py::self << int())  // lshift
    .def(py::self >> int())  // rshift
    .def(py::self & py::self)  // and
    .def(py::self ^ py::self)  // xor
    .def(py::self | py::self)  // or
    .def(py::self += py::self)  // iadd
    .def(py::self -= py::self)  // isub
    .def(py::self *= py::self)  // imul
    .def(py::self /= py::self)  // idiv, itruediv
    .def(py::self %= py::self)  // imod
    .def(py::self <<= py::self)  // ilshift
    .def(py::self >>= py::self)  // irshift
    .def(py::self &= py::self)  // iand
    .def(py::self ^= py::self)  // ixor
    .def(py::self |= py::self)  // ior
    .def(int_(py::self))  // int
    .def(float_(py::self));  // float
}
