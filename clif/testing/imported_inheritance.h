/*
 * Copyright 2020 Google LLC
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
#ifndef CLIF_TESTING_IMPPORTED_INHERITANCE_H_
#define CLIF_TESTING_IMPPORTED_INHERITANCE_H_
#include "clif/testing/nested_inheritance.h"
#include "clif/testing/nested_fields.h"
namespace clif_testing {
struct InheritImportedNestedInner : public Nested::Inner {};
struct InheritImportedNested : public Nested {};
struct InheritImportedNestedField : public DD {};
}  // namespace clif_testing
#endif  // CLIF_TESTING_IMPPORTED_INHERITANCE_H_
