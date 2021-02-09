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
#include "clif/testing/python/extend_from_clifaux_clif_aux.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(extend_from_clifaux, m) {
  // The second template argument switches the default holder type from
  // std::unique_ptr to std::unique_ptr. This is needed because we are using
  // std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened> as
  // function arguments. Pybind11 cannot convert std::unique_ptr to
  // std::shared_ptr.
  // See https://pybind11.readthedocs.io/en/stable/advanced/smart_ptrs.html#std-shared-ptr
  // and https://github.com/pybind/pybind11/blob/master/tests/test_smart_ptr.py#L305
  // For more information.
  py::class_<clif_testing::extend_from_clifaux::WhatHappened,
             std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>>
      (m, "WhatHappened")
    .def(py::init<>())
    .def("Record",
       (void (clif_testing::extend_from_clifaux::WhatHappened::*)
       (const std::string&) const)
       &clif_testing::extend_from_clifaux::WhatHappened::Record)
    .def("Last",
       (std::string (clif_testing::extend_from_clifaux::WhatHappened::*)
       () const)
       &clif_testing::extend_from_clifaux::WhatHappened::Last)
    .def("void_raw_ptr",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened*))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_raw_ptr)
    .def("void_shared_ptr",
       (void (*)
       (std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__void_shared_ptr)
    .def("void_by_value",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_by_value)
    .def("void_cref",
       (void (*)(const clif_testing::extend_from_clifaux::WhatHappened&))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_cref)
    .def("void_ref",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened&))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_ref)
    .def("int_raw_ptr",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_raw_ptr)
    .def("int_shared_ptr",
       (int (*)
       (std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_shared_ptr)
    .def("int_by_value",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_by_value)
    .def("int_cref",
       (int (*)(const clif_testing::extend_from_clifaux::WhatHappened&))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_cref)
    .def("int_ref",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened&))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_ref)
    .def("void_raw_ptr_int",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened*, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__void_raw_ptr_int,
       py::arg("i"))
    .def("void_shared_ptr_int",
       (void (*)
       (std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__void_shared_ptr_int,
       py::arg("i"))
    .def("void_by_value_int",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__void_by_value_int,
       py::arg("i"))
    .def("void_cref_int",
       (void (*)(const clif_testing::extend_from_clifaux::WhatHappened&, int))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_cref_int,
       py::arg("i"))
    .def("void_ref_int",
       (void (*)(clif_testing::extend_from_clifaux::WhatHappened&, int))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__void_ref_int,
       py::arg("i"))
    .def("int_raw_ptr_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_raw_ptr_int,
       py::arg("i"))
    .def("int_shared_ptr_int",
       (int (*)
       (std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_shared_ptr_int,
       py::arg("i"))
    .def("int_by_value_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_by_value_int,
       py::arg("i"))
    .def("int_cref_int",
       (int (*)(const clif_testing::extend_from_clifaux::WhatHappened&, int))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_cref_int,
       py::arg("i"))
    .def("int_ref_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened&, int))
       &clif_testing::extend_from_clifaux::WhatHappened__extend__int_ref_int,
       py::arg("i"))
    .def("int_raw_ptr_int_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*, int, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_raw_ptr_int_int,
       py::arg("i"), py::arg("j"))
    .def("int_shared_ptr_int_int",
       (int (*)
       (std::shared_ptr<clif_testing::extend_from_clifaux::WhatHappened>, int,
        int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_shared_ptr_int_int,
       py::arg("i"), py::arg("j"))
    .def("int_by_value_int_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened, int, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_by_value_int_int,
       py::arg("i"), py::arg("j"))
    .def("int_cref_int_int",
       (int (*)(const clif_testing::extend_from_clifaux::WhatHappened&, int,
                int))
       &clif_testing::extend_from_clifaux::
         WhatHappened__extend__int_cref_int_int,
       py::arg("i"), py::arg("j"))
    .def("int_ref_int_int",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened&, int, int))
       &clif_testing::extend_from_clifaux::
        WhatHappened__extend__int_ref_int_int,
       py::arg("i"), py::arg("j"))
    .def("chosen_method_name",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*, int, int))
       &clif_testing::extend_from_clifaux::custom_function_name,
       py::arg("i"), py::arg("j"))
    .def("ns_down_method",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*, int, int))
       &clif_testing::extend_from_clifaux::ns_down::function,
       py::arg("i"), py::arg("j"))
    .def("ns_up_method",
       (int (*)(clif_testing::extend_from_clifaux::WhatHappened*, int, int))
       &clif_testing::ns_up_function,
       py::arg("i"), py::arg("j"));

  // Derived classes need to declare holder types if its base classes declare
  // non-default holder types.
  // See https://github.com/pybind/pybind11/issues/1317.
  py::class_<clif_testing::extend_from_clifaux::ToBeRenamed,
             clif_testing::extend_from_clifaux::WhatHappened,
             std::shared_ptr<clif_testing::extend_from_clifaux::ToBeRenamed>>
      (m, "RenamedForPython")
    .def(py::init<>())
    .def("int_raw_ptr_int_int",
       (int (*)(clif_testing::extend_from_clifaux::ToBeRenamed*, int, int))
       &clif_testing::extend_from_clifaux::
        RenamedForPython__extend__int_raw_ptr_int_int,
       py::arg("i"), py::arg("j"))
    .def("chosen_method_name",
       (int (*)(clif_testing::extend_from_clifaux::ToBeRenamed*, int, int))
       &clif_testing::extend_from_clifaux::tbr_custom_function_name,
       py::arg("i"), py::arg("j"))
    .def("ns_down_method",
       (int (*)(clif_testing::extend_from_clifaux::ToBeRenamed*, int, int))
       &clif_testing::extend_from_clifaux::ns_down::tbr_function,
       py::arg("i"), py::arg("j"));
}
