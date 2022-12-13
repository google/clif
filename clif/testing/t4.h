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
#ifndef CLIF_TESTING_T4_H_
#define CLIF_TESTING_T4_H_

#include <memory>
#include <vector>
#include "absl/memory/memory.h"
#include "clif/protos/ast.pb.h"
#include "clif/testing/nested.pb.h"

namespace proto2 = google::protobuf;

namespace clif_testing {

using clif::protos::AST;
using clif::protos::Decl;

inline
int walk_ast(const AST& pb) { return pb.decls_size(); }

inline int size_ast(const AST* pb) { return pb ? pb->decls_size() : 0; }

inline Decl::Type decl_type(const Decl& pb) { return pb.decltype_(); }
inline Decl::Type decl_type_uniq_in(std::unique_ptr<Decl> t) {
  return t->decltype_();
}

inline long size_any_ref(const ::proto2::Message& pb) {  // NOLINT
  return pb.ByteSizeLong();
}
inline long size_any_ptr(const ::proto2::Message* pb) {  // NOLINT
  return pb->ByteSizeLong();
}

std::vector<AST*> all_ast_borrowed();
std::vector<std::unique_ptr<AST>> all_ast_holds();
std::unique_ptr<std::vector<std::unique_ptr<AST>>> all_ast_holds_p();

using clif::testing::Outer;
inline Outer::Inner::Nested nested(const Outer::Inner& pb) { return pb.val(); }

inline std::unique_ptr<Decl> GetUniquePtr(const Decl& pb) {
  return std::make_unique<Decl>(pb);
}
inline std::shared_ptr<Decl> GetSharedPtr(const Decl& pb) {
  return std::make_shared<Decl>(pb);
}

inline Outer::Inner ReturnProto(const Outer::Inner& pb) { return pb; }
}  // namespace clif_testing
#endif  // CLIF_TESTING_T4_H_
