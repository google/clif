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
#include "clif/testing/smart_ptrs.h"

#include "third_party/pybind11/include/pybind11/smart_holder.h"

namespace py = pybind11;

class PyOperation : public ::smart_ptrs::Operation {
 public:
  using ::smart_ptrs::Operation::Operation;
  int Run() override {
    PYBIND11_OVERRIDE_PURE(
        int,      /* Return type */
        ::smart_ptrs::Operation,         /* Parent class */
        Run     /* Name of function in C++ (must match Python name) */
    );
  }
};

PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::A)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::B)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::Operation)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::C1)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::D1)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::WithPrivateDtor)
PYBIND11_SMART_HOLDER_TYPE_CASTERS(::smart_ptrs::X)

PYBIND11_MODULE(smart_ptrs, m) {
  py::classh<::smart_ptrs::A>(m, "A")
    .def(py::init<>())
    .def_readwrite("a", &::smart_ptrs::A::a_);

  py::classh<::smart_ptrs::B>(m, "B")
    .def(py::init<>())
    .def("Get",
         (std::shared_ptr<::smart_ptrs::A> (::smart_ptrs::B::*)())
         &::smart_ptrs::B::Get)
    .def("GetNew",
         (std::unique_ptr<::smart_ptrs::A> (::smart_ptrs::B::*)())
         &::smart_ptrs::B::GetNew)
    .def("Set",
         (void (::smart_ptrs::B::*)(::smart_ptrs::A))
         &::smart_ptrs::B::Set, py::arg("a"))
    .def("SetSP",
         (void (::smart_ptrs::B::*)(std::shared_ptr<::smart_ptrs::A>))
         &::smart_ptrs::B::SetSP, py::arg("a"));

  m.def("Func",
        (::smart_ptrs::B (*)(std::unique_ptr<::smart_ptrs::A>))
        &::smart_ptrs::Func, py::arg("a"));

  py::classh<::smart_ptrs::Operation, PyOperation>(m, "Operation")
    .def(py::init<>())
    .def("Run",
         (int (::smart_ptrs::Operation::*)())&::smart_ptrs::Operation::Run);

  m.def("PerformUP",
        (int (*)(std::unique_ptr<::smart_ptrs::Operation>))
        &::smart_ptrs::PerformUP, py::arg("op"));
  m.def("PerformSP",
        (int (*)(std::shared_ptr<::smart_ptrs::Operation>))
        &::smart_ptrs::PerformSP, py::arg("op"));

  py::classh<::smart_ptrs::C1>(m, "C1")
    .def("Get",
         (int (::smart_ptrs::C1::*)())&::smart_ptrs::C1::Get);

  py::classh<::smart_ptrs::D1, ::smart_ptrs::C1>(m, "D1")
    .def(py::init<int>(), py::arg("i"));

  py::classh<::smart_ptrs::WithPrivateDtor>(m, "WithPrivateDtor")
    .def_static("New",
         (std::shared_ptr<::smart_ptrs::WithPrivateDtor> (*)())
         &::smart_ptrs::WithPrivateDtor::New)
    .def("Get",
         (int (::smart_ptrs::WithPrivateDtor::*)())
         &::smart_ptrs::WithPrivateDtor::Get);

  py::classh<::smart_ptrs::X>(m, "X")
    .def(py::init<>())
    .def_readwrite("y", &::smart_ptrs::X::y);

  m.def("F3",
        (std::unique_ptr<::smart_ptrs::X> (*)(std::unique_ptr<::smart_ptrs::X>))
        &::smart_ptrs::F3, py::arg("x"));
}
