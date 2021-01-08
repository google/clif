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

#include "clif/testing/special_classes.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(special_classes, m) {
  py::class_<::clif_testing::special_classes::Abstract> abstract(m, "Abstract");
  abstract.def_readonly_static(
      "KIND", &::clif_testing::special_classes::Abstract::KIND);
  abstract.def("Future",
               (int (::clif_testing::special_classes::Abstract::*)())
                &::clif_testing::special_classes::Abstract::Future);

  m.def("InconstructibleF",
        (int (*)())
         ::clif_testing::special_classes::Inconstructible::F);

  py::class_<::clif_testing::special_classes::NoDefaultConstructor>
      nodefaultconstructor(m, "NoDefaultConstructor");
  nodefaultconstructor.def_property_readonly(
      "a", &::clif_testing::special_classes::NoDefaultConstructor::A);

  py::class_<::clif_testing::special_classes::NoCopy> nocopy(m, "NoCopy");
  nocopy.def(py::init<int>(), py::arg("a") = 0);
  nocopy.def_property_readonly(
      "a", &::clif_testing::special_classes::NoCopy::A);

  py::class_<::clif_testing::special_classes::NoMove> nomove(m, "NoMove");
  nomove.def(py::init<int>(), py::arg("a") = 0);
  nomove.def_property_readonly(
      "a", &::clif_testing::special_classes::NoMove::A);
}
