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

#include "clif/testing/t3.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(enums, m) {
  // Unscoped enums
  py::enum_<OldGlobalE>(m, "_Old")
    .value("TOP1", ::OldGlobalE::kTop1)
    .value("TOPn", ::OldGlobalE::kTopN)
    .export_values();

  // Scoped enums. .export values should be skipped. See
  // https://pybind11.readthedocs.io/en/stable/classes.html
  py::enum_<NewGlobalE>(m, "_New")
    .value("BOTTOM", ::NewGlobalE::BOTTOM)
    .value("TOP", ::NewGlobalE::TOP);

  py::class_<::some::K> enum_class(m, "K");
  enum_class.def(py::init<>());
  py::enum_<::some::K::_e>(enum_class, "OldE")
    .value("ONE", ::some::K::kOne)
    .export_values();
  py::enum_<::some::K::E>(enum_class, "NewE")
    .value("ONE", ::some::K::E::kOne)
    .value("TWO", ::some::K::E::kTwo);
  py::class_<::some::K::O>(enum_class, "O")
    .def_readwrite("n", &::some::K::O::n)
    .def_readwrite("f", &::some::K::O::f);
  enum_class.def("M", &::some::K::M);
  enum_class.def_readwrite("i", &::some::K::i_);
  m.def("K2", &some::K::K2);
}
