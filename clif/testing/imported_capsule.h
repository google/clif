/*
 * Copyright 2022 Google LLC
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
#ifndef THIRD_PARTY_CLIF_TESTING_IMPORTED_CAPSULE_H_
#define THIRD_PARTY_CLIF_TESTING_IMPORTED_CAPSULE_H_

#include "clif/testing/special_classes.h"

namespace clif_testing {

inline int ConsumePythonCapsule(special_classes::ExportedCapsule* c) {
  return c->get_value();
}

inline special_classes::ExportedCapsule* CreatePythonCapsule() {
  static special_classes::ExportedCapsule obj;
  return &obj;
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_IMPORTED_CAPSULE_H_
