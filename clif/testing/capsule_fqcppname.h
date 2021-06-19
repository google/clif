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
#ifndef CLIF_TESTING_CAPSULE_FQCPPNAME_H_
#define CLIF_TESTING_CAPSULE_FQCPPNAME_H_

namespace clif_testing_capsule_fqcppname {

struct ForeignType {};

}  // namespace clif_testing_capsule_fqcppname

// Currently this has to be in the global namespace or the C API code generator
// will generate invalid Clif_PyObj*() functions.
inline void UseForeignType(clif_testing_capsule_fqcppname::ForeignType *) {}

#endif  // CLIF_TESTING_CAPSULE_FQCPPNAME_H_
