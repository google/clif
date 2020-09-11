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
#ifndef CLIF_TESTING_T10_H_
#define CLIF_TESTING_T10_H_

#include <Python.h>

#include "clif/testing/t2.h"
#include "clif/testing/t9.h"

void TakeBase(std::unique_ptr<t9::Base>) {}

K* CreateK() { return new K(0); }

struct A : K {
  A() : K(0) {}
#if PY_MAJOR_VERSION < 3
  PyObject* __str__() { return PyString_FromString("A"); }
#else
  PyObject* __str__() { return PyUnicode_FromString("A"); }
#endif
};

inline PyObject* ConversionFunctionCheck(PyObject* x) { return x; }

#endif  // CLIF_TESTING_T10_H_
