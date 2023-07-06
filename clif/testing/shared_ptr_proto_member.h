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
#ifndef CLIF_TESTING_SHARED_PTR_PROTO_MEMBER_H_
#define CLIF_TESTING_SHARED_PTR_PROTO_MEMBER_H_

#include <memory>
#include <string_view>

// AST proto conveniently doubles as test object.
#include "clif/protos/ast.pb.h"

namespace proto2 = google::protobuf;

namespace clif_testing {
namespace shared_ptr_proto_member {

class ProtoHolderByValue {
 public:
  // ProtoHolderByValue(const clif::protos::AST&) leads to matcher failure.
  ProtoHolderByValue(clif::protos::AST ast) : by_val_ast_{ast} {}

  clif::protos::AST GetByValue() const { return by_val_ast_; }
  const clif::protos::AST& GetConstRef() const { return by_val_ast_; }
  void ResetSource(std::string_view new_source) {
    by_val_ast_.set_source(std::string(new_source));
  }

 private:
  clif::protos::AST by_val_ast_;
};

class ProtoHolderUniquePtr {
 public:
  ProtoHolderUniquePtr(std::unique_ptr<clif::protos::AST> ast)
      : uq_ptr_ast_{std::move(ast)} {}

  std::unique_ptr<clif::protos::AST> GetUniquePtr() {
    return std::move(uq_ptr_ast_);
  }
  void ResetSource(std::string_view new_source) {
    uq_ptr_ast_->set_source(std::string(new_source));
  }

 private:
  std::unique_ptr<clif::protos::AST> uq_ptr_ast_;
};

class ProtoHolderSharedPtr {
 public:
  // NO Clif_PyObjAs() for shared_ptr:
  // ProtoHolderSharedPtr(std::shared_ptr<clif::protos::AST> ast)
  // But this works:
  ProtoHolderSharedPtr(std::unique_ptr<clif::protos::AST> ast)
      : sh_ptr_ast_{std::move(ast)} {}

  std::shared_ptr<clif::protos::AST> GetSharedPtr() const {
    return sh_ptr_ast_;
  }
  void ResetSource(std::string_view new_source) {
    sh_ptr_ast_->set_source(std::string(new_source));
  }

  std::size_t GetSharedPtrUseCount() const { return sh_ptr_ast_.use_count(); }

 private:
  std::shared_ptr<clif::protos::AST> sh_ptr_ast_;
};

}  // namespace shared_ptr_proto_member
}  // namespace clif_testing

#endif  // CLIF_TESTING_SHARED_PTR_PROTO_MEMBER_H_
