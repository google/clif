/*
 * Copyright 2023 Google LLC
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
#ifndef CLIF_TESTING_UNSPECIFIED_INHERITANCE_UNSPEC_BASE_H_
#define CLIF_TESTING_UNSPECIFIED_INHERITANCE_UNSPEC_BASE_H_

namespace clif_testing {
namespace unspecified_inheritance {

struct UnspecBase {
  virtual ~UnspecBase() = default;
  virtual int Get() const { return 100; }
};

inline int PassUnspecBase(const UnspecBase& sb) { return sb.Get() + 30; }

}  // namespace unspecified_inheritance
}  // namespace clif_testing

#endif  // CLIF_TESTING_UNSPECIFIED_INHERITANCE_UNSPEC_BASE_H_
