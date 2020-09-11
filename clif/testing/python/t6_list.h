/*
 * Copyright 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_TESTING_PYTHON_T6_LIST_H_
#define CLIF_TESTING_PYTHON_T6_LIST_H_

// Provide CLIF extension for std::list<int>.
// (It's a helper for t6_test.)
// CLIF use `std::list<int>` as list_int

#include <list>
#include "clif/python/stltypes.h"

namespace clif {

PyObject* Clif_PyObjFrom(const std::list<int>& c, const py::PostConv& pc) {
  return py::ListFromSizableCont(c, pc);
}

bool Clif_PyObjAs(PyObject* py, std::list<int>* c) {
  return py::IterToCont<int>(py, [&c](int&& i) { c->push_back(i); });  //NOLINT: build/c++11
}
}  // namespace clif

#endif  // CLIF_TESTING_PYTHON_T6_LIST_H_
