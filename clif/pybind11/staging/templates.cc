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

#include "clif/testing/templates.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

namespace py = pybind11;

PYBIND11_MODULE(templates, m) {
  py::class_<::templates::A>(m, "A")
    .def(py::init<>())
    .def_readwrite("a", &templates::A::a);

  py::class_<::templates::TemplateClass<int>>(m, "TemplateClassInt")
    .def(py::init<>());

  py::class_<::templates::ObjectTypeHolder< ::templates::Vector<float>>>(
      m, "VectorHolder")
    .def(py::init<>())
    .def("MethodUsingTemplateType",
         (int (::templates::ObjectTypeHolder<templates::Vector<float>>::*)(
               ::templates::ObjectTypeHolder<::templates::Vector<float>> *))
         &::templates::ObjectTypeHolder<
             templates::Vector<float>>::MethodUsingTemplateType,
         py::arg("other"));
}
