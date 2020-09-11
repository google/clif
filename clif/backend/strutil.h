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
#ifndef CLIF_BACKEND_STRUTIL_H_
#define CLIF_BACKEND_STRUTIL_H_

#include <string>
#include <vector>

#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/StringExtras.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/Twine.h"

namespace clif {

inline void StrAppend(std::string* str) {}

template <typename Arg1, typename... Args>
void StrAppend(std::string* str, Arg1&& p, Args&&... pieces) {
  str->append(llvm::Twine(p).str());
  StrAppend(str, std::forward<Args>(pieces)...);
}

// Utility class to get the names of the enclosing namespaces by
// removing all scoping operators.
//
// If namespace_name = ::foo::bar::bat, then create a vector like so:
// (foo, bar, bat).
//
// Splitting qualified-names like this violates the CLIF design-goal
// to never parse C++ code without an industrial strength compiler,
// but this bit is unavoidable, and not one of the complicated cases.
class NamespaceVector {
 public:
  typedef llvm::SmallVector<llvm::StringRef, 4> ComponentsVector;
  explicit NamespaceVector(const std::string& namespaces) :
      namespace_data_(namespaces) {
    SplitNamespaces();
  }

  explicit NamespaceVector(const llvm::StringRef& namespaces) :
      namespace_data_(namespaces) {
    SplitNamespaces();
  }

  ComponentsVector::iterator begin() noexcept {
    return namespace_vector_.begin();
  }

  ComponentsVector::iterator end() noexcept {
    return namespace_vector_.end();
  }

  llvm::StringRef& back() {
    return namespace_vector_.back();
  }

  void pop_back() {
    namespace_vector_.pop_back();
  }

  bool empty() const noexcept {
    return namespace_vector_.empty();
  }

 private:
  void SplitNamespaces() {
    llvm::StringRef(namespace_data_).split(
        namespace_vector_,
        llvm::StringRef("::"),
        -1,  // no maximum split count.
        false);  // Don't keep empty entries.
  }
  std::string namespace_data_;
  ComponentsVector namespace_vector_;
};

}  // namespace clif

#endif  // CLIF_BACKEND_STRUTIL_H_
