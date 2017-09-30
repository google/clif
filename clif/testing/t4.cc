// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "clif/testing/t4.h"
#include "clif/python/ptr_util.h"

namespace clif_testing {

std::vector<AST*> all_ast_borrowed() {
  std::vector<AST*> r;
  for (const char* p="123"; *p; ++p) {
    AST* ast(new AST);
    ast->set_source(p, 1);
    r.push_back(ast);
  }
  return r;
}

std::vector<std::unique_ptr<AST>> all_ast_holds() {
  std::vector<std::unique_ptr<AST>> r;
  for (const char* p="123"; *p; ++p) {
    std::unique_ptr<AST> ast(new AST);
    ast->set_source(p, 1);
    r.push_back(std::move(ast));
  }
  return r;
}

std::unique_ptr<std::vector<std::unique_ptr<AST>>> all_ast_holds_p() {
  return gtl::MakeUnique<std::vector<std::unique_ptr<AST>>>(all_ast_holds());
}
}  // namespace clif_testing
