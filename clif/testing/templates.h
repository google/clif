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
#ifndef CLIF_TESTING_TEMPLATES_H_
#define CLIF_TESTING_TEMPLATES_H_

#include <memory>
#include "clif/testing/template_class.h"

namespace templates {

struct A {
 public:
  int a;
};

template<typename T> inline void TemplateParamFunc(std::unique_ptr<T> a) {
}

using TemplateClassInt = TemplateClass<int>;

// Test for wrapping a specialized multi-level template class with a typedef
// inside the class definition.
template <typename Real>
class Vector {};

template <class ObjectType>
class ObjectTypeHolder {
 public:
  // Typedef the nested template argument type.
  typedef ObjectType T;

  ObjectTypeHolder() {}

  int MethodUsingTemplateType(ObjectTypeHolder<T> *other) { return 1; }
};

}  // namespace templates

#endif  // CLIF_TESTING_TEMPLATES_H_
