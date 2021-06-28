/*
 * Copyright 2021 Google LLC
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

#ifndef THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_CLIF_CONVERSION_H_
#define THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_CLIF_CONVERSION_H_

#include "clif/python/postconv.h"
#include "clif/python/types.h"
#include "clif/testing/value_holder.h"

namespace clif_testing {

// CLIF use `::clif_testing::ValueHolder` as ValueHolder
inline bool Clif_PyObjAs(PyObject* obj, ValueHolder* c) {
  PyObject *tmp = PyNumber_Long(obj);
  if (!tmp) {
    return false;
  }
  c->value = PyLong_AsLong(tmp);
  ++(c->value);
  return true;
}

inline PyObject* Clif_PyObjFrom(const ValueHolder& c,
                                const clif::py::PostConv& pc) {
  return clif::Clif_PyObjFrom(c.value + 1, {});
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_CLIF_CONVERSION_H_
