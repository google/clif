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

#include "clif/pybind11/staging/concrete_derived.h"

namespace py = pybind11;

PYBIND11_MODULE(concrete_derived, m) {
  py::classh<clif_testing::derived_in_other_header::ConcreteDerivedEmpty,
             clif_testing::derived_in_other_header::ConcreteBaseEmpty>(
      m, "ConcreteDerivedEmpty")
      .def(py::init<>())
      .def("Get",
           (int (
               clif_testing::derived_in_other_header::ConcreteDerivedEmpty::*)()
                const) &
               clif_testing::derived_in_other_header::ConcreteDerivedEmpty::Get)
      .def(
          "BaseGet",
          (int (clif_testing::derived_in_other_header::ConcreteDerivedEmpty::*)(
              const clif_testing::derived_in_other_header::
                  ConcreteBaseEmpty*)) &
              clif_testing::derived_in_other_header::ConcreteDerivedEmpty::
                  BaseGet);
}
