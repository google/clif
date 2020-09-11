// Copyright 2019 Abseil Authors and Google LLC.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "clif/testing/std_variant.h"

#include <memory>
#include <optional>

#include "clif/python/types.h"

namespace clif_test {

bool Clif_PyObjAs(PyObject* obj, WithDirectConv* c) {
  using ::clif::Clif_PyObjAs;
  bool success = Clif_PyObjAs(obj, &c->value);
  if (!success || c->value < 0) {
    PyErr_SetString(PyExc_ValueError, "");
    return false;
  }
  ++(c->value);
  return success;
}

bool Clif_PyObjAs(PyObject* obj, ::std::optional<WithOptionalConv>* c) {
  using ::clif::Clif_PyObjAs;
  bool success = Clif_PyObjAs(obj, &c->emplace().value);
  if (!success || c->value().value < 0) {
    PyErr_SetString(PyExc_ValueError, "");
    return false;
  }
  ++(c->value().value);
  return success;
}

bool Clif_PyObjAs(PyObject* obj, std::unique_ptr<WithUniquePtrConv>* c) {
  *c = ::std::make_unique<WithUniquePtrConv>();

  using ::clif::Clif_PyObjAs;
  bool success = Clif_PyObjAs(obj, &(*c)->value);
  if (!success || (*c)->value < 0) {
    PyErr_SetString(PyExc_ValueError, "");
    return false;
  }
  ++((*c)->value);
  return success;
}

}  // namespace clif_test
