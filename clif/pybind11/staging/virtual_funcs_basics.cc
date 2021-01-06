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

#include "clif/testing/virtual_funcs_basics.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"
#include "third_party/pybind11/include/pybind11/stl.h"

namespace py = pybind11;

class PyB : public B {
 public:
  using B::B;
  void set_c(int i) override {
    PYBIND11_OVERRIDE(
        void,      /* Return type */
        B,         /* Parent class */
        set_c,     /* Name of function in C++ (must match Python name) */
        i          /* Argument(s) */
    );
  }
};

PYBIND11_MODULE(virtual_funcs_basics, m) {
  py::class_<B, PyB>(m, "B")
    .def(py::init<>())
    .def_readwrite("c", &B::c)
    .def("set_c", &B::set_c)
    .def_property("pos_c", &B::get_c, &B::set_c);

  m.def("Bset", &Bset);

  py::class_<D, B>(m, "D")
    .def(py::init<>());
}
