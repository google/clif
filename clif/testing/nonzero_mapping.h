/*
 * Copyright 2020 Google Inc.
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
#ifndef CLIF_TESTING_NONZERO_MAPPING_H_
#define CLIF_TESTING_NONZERO_MAPPING_H_

#include <stdint.h>
#include <stdlib.h>

namespace clif_testing {

struct AlwaysFalse {
  operator bool() const {
    return false;
  }
};

struct MightBeTrue {
  MightBeTrue(bool value): value(value) { }
  bool GetValue() const {
    return value;
  }

  bool value;
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_NONZERO_MAPPING_H_
