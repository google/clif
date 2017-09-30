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
// Builds the input for the compiler from clif_ast and type_table.
// Strangely relevant implementation detail when thinking about C++
// compiles and their interaction with clif: this code generates a
// string of the form:
//
// #include "file1.h"
// #include "file2.h"
// #include "..."
// #include "fileN.h"
// namespace clif {
//   typedef <extracted cpp_type> clif_type_0;
//   typedef <extracted cpp_type> clif_type_1;
//   ...
//   typedef <extracted cpp_type> clif_type_N;
// }

#ifndef CLIF_BACKEND_CODE_BUILDER_H_
#define CLIF_BACKEND_CODE_BUILDER_H_

#include <unordered_map>

#include "clif/protos/ast.pb.h"


namespace clif {

using protos::AST;
using protos::ClassDecl;
using protos::Decl;
using protos::FuncDecl;
using protos::Name;
using protos::Type;

typedef ::google::protobuf::RepeatedPtrField<Decl> DeclList;

class CodeBuilder {
 public:
  typedef std::unordered_map<std::string, std::string> NameMap;

  const std::string& BuildCode(protos::AST* clif_ast);

  // Returns a mapping from the code builder declared typedefs to their
  // fully qualified names.
  const NameMap& FullyQualifiedTypedefs() const { return fq_typedefs_; }

  // Returns a mapping from the code builder declared typedefs to their
  // original names in the input proto.
  const NameMap& OriginalNames() const { return original_names_; }

 private:
  friend class ClifMatcherTest;

  // A class to generate unique internal names that the code builder uses
  // to declare/define types and classes.
  class NameGenerator {
   public:
    NameGenerator()
        : class_count_(0), template_arg_count_(0), typedef_count_(0) {}

    std::string NextClassName();
    std::string NextTemplateArgName();
    std::string NextTypedefName();

   private:
    int class_count_;
    int template_arg_count_;
    int typedef_count_;
  };

  // Adds all the namespace and boilerplate that surrounds a list of
  // top level decls.
  void BuildCodeForTopLevelDecls(DeclList* decls);

  // Generate the specific code needed for a single decl, ignoring
  // namespaces and related issues.
  void BuildCodeForDecl(Decl* decl);

  std::string GenerateTypedefString(const std::string& raw_type);

  void BuildCodeForName(Name* name);

  void BuildCodeForClass(ClassDecl* decl);

  // Return the complete cpp_type made by code builder for the type.
  std::string BuildCodeForType(Type* type);

  // Return the complete cpp_type made by code builder for the function decl.
  std::string BuildCodeForFunc(FuncDecl* decl);

  // Return the complete cpp_type made by code builder for the container.
  std::string BuildCodeForContainer(Type* type);

  std::string BuildCodeForContainerHelper(Type* type);

  std::string code_;
  std::vector<std::string> scoped_name_stack_;
  std::vector<int> current_line_;
  std::vector<std::string> current_file_;
  NameGenerator name_gen_;
  NameMap fq_typedefs_;
  NameMap original_names_;
};
}  // namespace clif

#endif  // CLIF_BACKEND_CODE_BUILDER_H_
