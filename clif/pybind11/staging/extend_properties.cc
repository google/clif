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
#include "clif/testing/python/extend_properties_clif_aux.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(extend_properties, m) {
  py::class_<clif_testing::PropertyHolder,
             std::shared_ptr<clif_testing::PropertyHolder>>
      (m, "PropertyHolder")
    .def(py::init<int>())
    .def_property_readonly("value",
        &clif_testing::extend_properties::PropertyHolder__extend__get_value)
    .def_property_readonly("value_times_ten",
        &clif_testing::extend_properties::
         PropertyHolder__extend__get_value_times_ten)
    .def_property("value_gs",
        &clif_testing::extend_properties::PropertyHolder__extend__get_value_gs,
        &clif_testing::extend_properties::PropertyHolder__extend__set_value_gs);
}
