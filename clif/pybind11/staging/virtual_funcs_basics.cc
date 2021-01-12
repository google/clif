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
#include "third_party/pybind11/include/pybind11/stl.h"

#include "clif/testing/virtual_funcs_basics.h"

#include <vector>  // NOLINT

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

class PyK : public K {
 public:
  using K::K;
  void inc(int delta) override {
    // Currently we are not able to differentiate "PYBIND11_OVERRIDE_PURE" and
    // "PYBIND11_OVERRIDE" from CLIF ast.
    PYBIND11_OVERRIDE_PURE(
        void,      /* Return type */
        K,         /* Parent class */
        inc,       /* Name of function in C++ (must match Python name) */
        delta      /* Argument(s) */
    );
  }
};

class PyQ : public Q {
 public:
  using Q::Q;
  bool PossiblyPush(int data) override {
    PYBIND11_OVERRIDE_PURE(
        bool,          /* Return type */
        Q,             /* Parent class */
        PossiblyPush,  /* Name of function in C++ (must match Python name) */
        data           /* Argument(s) */
    );
  }
};

class PyAbstractClassNonDefConst : public AbstractClassNonDefConst {
 public:
  using AbstractClassNonDefConst::AbstractClassNonDefConst;
  int DoSomething() const override {
    PYBIND11_OVERRIDE_PURE(
        int,  /* Return type */
        AbstractClassNonDefConst,  /* Parent class */
        DoSomething,  /* Name of function in C++ (must match Python name) */
    );
  }
};

class PyClassNonDefConst : public ClassNonDefConst {
 public:
  using ClassNonDefConst::ClassNonDefConst;
  int DoSomething() const override {
    PYBIND11_OVERRIDE(
        int,  /* Return type */
        ClassNonDefConst,  /* Parent class */
        DoSomething,  /* Name of function in C++ (must match Python name) */
    );
  }
};

PYBIND11_MODULE(virtual_funcs_basics, m) {
  py::class_<B, PyB>(m, "B")
    .def(py::init<>())
    .def_readwrite("c", &B::c)
    .def("set_c", (void (B::*)(int))&B::set_c, py::arg("i"))
    .def_property("pos_c", &B::get_c, &B::set_c);

  m.def("Bset", &Bset);

  py::class_<D, B>(m, "D")
    .def(py::init<>());

  py::class_<K, PyK>(m, "K")
    .def(py::init<>())
    .def_readwrite("i", &K::i)
    .def("inc", (void (K::*)(int))&K::inc, py::arg("delta"));

  m.def("seq", (std::vector<int> (*)(K*, int, int))&Kseq, py::arg("k"),
        py::arg("step"), py::arg("stop"));

  py::class_<Q, PyQ>(m, "Q")
    .def(py::init<>())
    .def("PossiblyPush", (bool (Q::*)(int))&Q::PossiblyPush, py::arg("data"));

  m.def("add_seq", (int (*)(Q*, int, int))&add_seq, py::arg("q"),
        py::arg("step"), py::arg("stop"));

  py::class_<AbstractClassNonDefConst, PyAbstractClassNonDefConst>(
      m, "AbstractClassNonDefConst")
    .def(py::init<int, int>())
    .def_readwrite("a", &AbstractClassNonDefConst::my_a)
    .def_readwrite("b", &AbstractClassNonDefConst::my_b)
    .def("DoSomething",
         (int (AbstractClassNonDefConst::*)() const)
         &AbstractClassNonDefConst::DoSomething);

  m.def("DoSomething1",
        (int (*)(const AbstractClassNonDefConst&)) &DoSomething,
        py::arg("a"));

  py::class_<ClassNonDefConst, PyClassNonDefConst>(
      m, "ClassNonDefConst")
    .def(py::init<int, int>())
    .def_readwrite("a", &ClassNonDefConst::my_a)
    .def_readwrite("b", &ClassNonDefConst::my_b)
    .def("DoSomething",
         (int (ClassNonDefConst::*)() const)
          &ClassNonDefConst::DoSomething);

  m.def("DoSomething2",
        (int (*)(const ClassNonDefConst&)) &DoSomething,
        py::arg("a"));
}
