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

// Generates C++ typedefs from clif protos and maps between them.
//
// We generate all these typedefs and surrounding code for three
// reasons:
//
// 1. To syntax check the C++ fragments the user wrote.
//
// 2. To create types that we can lookup by name. For example,
// vector<int> can't be normally looked up by name, but clif_type_0
// can be: typedef vector<int> clif_type_0;
//
// 3. When users write C++ at all, they want to write code that looks
// like the code they are wrapping, that means they want to use names
// that are not fully qualified.
//
// To solve this problem for each type a user supplies, we declare a
// type of our own that is logically "near" the user-supplied
// type. For types declared in namespaces, we declare them in the same
// namespace, which is easy, because namespaces can be lexically
// reopened any time you like:
//
// namespace A { declare_something... }
// namespace A { declare_something_else... }
//
// Types declared inside other classes are somewhat problematic,
// because class declarations cannot be lexically reopened.
//
// Therefore we create a derived class to acheive the same result.
// Unfortunately, some classes that users want to wrap cannot be
// derived from without care, for example, classes with deleted
// destructors. And some that cannot be derived from at all, such
// as those with final destructors.
//
// Templates to the rescue.
//
// We don't exactly want to derive from these classes. We just need
// some syntax checking and some syntactically correct typedefs.
//
// Therefore we declare template classes that derive from the
// user-supplied classes, and we never instantiate them, neither
// explicitly nor implicitly.
//
// Try it:
//
// class Parent {public: virtual ~Parent() final; };
// class Child : public Parent { }; // <-- Error
// template<class T> class TemplateChild : public Parent { }; // <-- No error
//
// class Parent {public: virtual ~Parent() = delete; };
// class Child : public Parent { }; // <-- Error
// template<class T> class TemplateChild : public Parent { }; // <-- No error
//
// This trick relies on Clif never explicitly instantiating the
// templates and the rules in the C++ standard (14.7.1/10) around
// implicit instantiation.
//
// This trick doesn't work for classes that are final themselves. One
// can argue that clif doesn't want to support those cases though.

#include "clif/backend/code_builder.h"

#include <list>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "clif/backend/strutil.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/raw_ostream.h"

#define DEBUG_TYPE "clif_code_builder"

namespace {

const char kClifClassNamePrefix[] = "clif_class_";
const char kClifTemplateArgPrefix[] = "clif_unused_template_arg_";
const char kClifTypedefPrefix[] = "clif_type_";

}  // anonymous namespace

namespace clif {

std::string CodeBuilder::NameGenerator::NextClassName() {
  return std::string(kClifClassNamePrefix) + std::to_string(class_count_++);
}

std::string CodeBuilder::NameGenerator::NextTemplateArgName() {
  return std::string(kClifTemplateArgPrefix) +
      std::to_string(template_arg_count_++);
}

std::string CodeBuilder::NameGenerator::NextTypedefName() {
  return std::string(kClifTypedefPrefix) + std::to_string(typedef_count_++);
}

std::string CodeBuilder::GenerateTypedefString(const std::string& cpp_type) {
  std::string clif_declared_type = name_gen_.NextTypedefName();
  std::string fully_qualified_name = "::";
  for (const std::string& class_name : scoped_name_stack_) {
    StrAppend(&fully_qualified_name, class_name, "::");
  }
  StrAppend(&fully_qualified_name, clif_declared_type);
  LLVM_DEBUG(llvm::dbgs() << "Inserting cpp_type: " << cpp_type
        << " fq_name " << fully_qualified_name);
  fq_typedefs_.insert({clif_declared_type, fully_qualified_name});
  original_names_.insert({clif_declared_type, cpp_type});
  StrAppend(&code_, "typedef\n");
  if (!current_line_.empty() && !current_file_.empty()) {
    StrAppend(&code_, "#line ", current_line_.back(),
              " \"", current_file_.front(), "\"\n");
  }
  // Keep the actual cpp_type on its own line, so that when there is
  // an error, users will just see what the clif file contained,
  // rather than our surrounding boilerplate.
  StrAppend(&code_, cpp_type, "\n",
            clif_declared_type, ";\n");
  return clif_declared_type;
}

void CodeBuilder::BuildCodeForName(Name* name) {
  if (!name->cpp_name().empty()) {
    name->set_cpp_name(GenerateTypedefString(name->cpp_name()));
  }
}

void CodeBuilder::BuildCodeForClass(ClassDecl* decl) {
  BuildCodeForName(decl->mutable_name());
  // Can't inherit from final classes, so don't attempt to here, and
  // we don't have adl here either.  The user will have to specify the
  // fully qualified names of any types they need.
  if (!decl->final()) {
    std::string clif_class_name = name_gen_.NextClassName();
    scoped_name_stack_.push_back(clif_class_name);
    StrAppend(&code_,
              "template<class ", name_gen_.NextTemplateArgName(), "> class ",
              clif_class_name,
              ": public ", decl->name().cpp_name(), " { public:\n");
  }

  for (int i = 0; i < decl->members_size(); ++i) {
    BuildCodeForDecl(decl->mutable_members(i));
  }

  if (!decl->final()) {
    StrAppend(&code_, "\n };\n");
    scoped_name_stack_.pop_back();
  }
}

std::string CodeBuilder::BuildCodeForType(Type* type,
                                          bool type_selector_enable) {
  if (!type->params().empty()) {
    return BuildCodeForContainer(type);
  }
  if (type->has_callable()) {
    return BuildCodeForFunc(type->mutable_callable());
  }
  const std::string cpp_type_name = type->cpp_type();
  const std::string lang_type_name = type->lang_type();
  auto type_map_iter =
      code_builder_clif_to_clang_type_map_->find(lang_type_name);
  // A type in CLIF AST must specify either [cpp_type] or [lang_type + the
  // corresponding typemap].
  if (cpp_type_name.empty() &&
      type_map_iter == code_builder_clif_to_clang_type_map_->end()) {
    llvm::errs()
        << "Neither [cpp_type] or [lang_type + typemap] is specified for "
        << lang_type_name << " (With C++ type: " << cpp_type_name
        << ")\nPlease specify at least one of them\n";
    // An empty type will cause compiling failure with the above error message.
    // TODO: Adds the error checking for absence of [cpp_type] and
    // [lang_type + the corresponding typemap] in CLIF parser because CLIF
    // parser could also report the exact file and the line where the info is
    // missed. Temporarily keeps this error checking in code builder before
    // adding it in the parser.
    return "";
  }

  // For non template types in automatic type selector:
  // Builds all of the possible cpp_types in the corresponding typemap if
  // the current typemap has not been processed by the code builder.

  // Example:
  // CLIF AST:
  //    "type {lang_type: bytes}"
  //
  // typemap:
  //    "typemaps { "
  //    "  lang_type: bytes"
  //    "  cpp_type: ::absl::Cord"
  //    "  cpp_type: ::absl::string_view"
  //    "  cpp_type: string"
  //    "}"
  //
  // The following process will look up lang_type("bytes") in the hashmap for
  // all of the possible cpp_types. For each possible cpp_type, like
  // "::absl::Cord", the code builder builds a typedef for it like "typedef
  // ::absl::Cord clif_type_*", and replaces the corresponding hashmap's
  // cpp_type with "clif_type_*" to store the mapping information.
  if (cpp_type_name.empty() && type_selector_enable) {
    auto& cpp_type_vector = type_map_iter->second;
    for (auto& cpp_type : cpp_type_vector) {
      if (strncmp(cpp_type.c_str(), kClifTypedefPrefix,
                  strlen(kClifTypedefPrefix))) {
        cpp_type = GenerateTypedefString(cpp_type);
      }
    }
  } else {
    // If the user specifies the cpp_type field of CLIF type, CLIF will use the
    // user-provided cpp_type and disable the automatic type selector.
    type->set_cpp_type(GenerateTypedefString(cpp_type_name));
  }
  return cpp_type_name;
}

// When CLIF automatically type selector is not triggered, to build code for a
// template type, CLIF code builder assembles the cpp_type field both from
// the template type and the nested types, generates a typedef for the
// assembled cpp name.
//
// Example: CLIF AST for a template type:
//   "type {"
//   "  lang_type: set<int> "
//   "  cpp_type: std::set"
//   "  params { "
//   "    lang_type: int "
//   "    cpp_type: int "
//   "  }"
//   "}"
//
// Given the above CLIF input AST, CLIF code builder will assemble the
// cpp_type field from the template type("std::set") and the nested
// type("int"), compose the complete cpp_type as "std::set<int>" and generate
// the typedef as "typedef std::set<int> clif_type_*". The following function
// will return the corresponding "clif_type_*" of the typedef statement.
std::string CodeBuilder::BuildCodeForContainerHelper(Type* type) {
  std::string template_name;
  StrAppend(&template_name, type->cpp_type(), "<");
  for (int idx = 0; idx < type->params().size(); idx++) {
    Type* element = type->mutable_params(idx);
    // If the container contains a callable as a template argument, we should
    // include the callable's type information in the template's cpp_type.
    if (element->has_callable()) {
      std::string func_name = BuildCodeForFunc(element->mutable_callable());
      StrAppend(&template_name, func_name);
    } else if (!element->params().empty()) {
      // Since |element| is a Type, we could just call BuildCodeForType.
      // However, we want the template name of |element| so that we can
      // append it to the parent's template name. Hence, we call this
      // function recursively.
      StrAppend(&template_name, BuildCodeForContainerHelper(element));
    } else {
      StrAppend(&template_name, element->cpp_type());
      BuildCodeForType(element, false);
    }
    if (idx != type->params().size() - 1) {
      StrAppend(&template_name, ", ");
    }
  }
  StrAppend(&template_name, " >");
  type->set_cpp_type(GenerateTypedefString(template_name));
  return template_name;
}

std::string CodeBuilder::BuildCodeForContainer(Type* type) {
  return BuildCodeForContainerHelper(type);
}

std::string CodeBuilder::BuildCodeForFunc(FuncDecl* decl) {
  // Build and return the cpp_type for function decls. The returned
  // func_type_name is only used when we are building the code for templates
  // with callable template arguments, i.e., only when BuildCodeForFunc is
  // invoked by BuildCodeForContainerHelper. If we have a type
  // template_class<std::function<output(intput)>>, the return value
  // func_type_name is expected to be "std::function<output(intput)>".
  std::string func_type_name;
  StrAppend(&func_type_name, "::std::function<");
  for (int i = 0; i < decl->returns_size(); ++i) {
    // If decl is a callable(std::function), returns_size can not be greater
    // than 1. Otherwise, the compiler will report an error.
    std::string type_name =
        BuildCodeForType(decl->mutable_returns(i)->mutable_type(), true);
    StrAppend(&func_type_name, type_name);
    if (i != decl->returns_size() - 1) StrAppend(&func_type_name, ", ");
  }
  if (decl->returns_size() == 0) {
    StrAppend(&func_type_name, "void");
  }
  StrAppend(&func_type_name, "(");
  for (int i = 0; i < decl->params_size(); ++i) {
    std::string type_name =
        BuildCodeForType(decl->mutable_params(i)->mutable_type(), true);
    StrAppend(&func_type_name, type_name);
    if (i != decl->params_size() - 1) StrAppend(&func_type_name, ", ");
  }
  StrAppend(&func_type_name, ")", ">");
  return func_type_name;
}

void CodeBuilder::BuildCodeForDecl(Decl* decl) {
  // line_number is zero based, but every editor on the planet is
  // one based.
  current_line_.push_back(decl->line_number());
  switch (decl->decltype_()) {
    case Decl::CLASS:
      BuildCodeForClass(decl->mutable_class_());
      break;
    case Decl::ENUM:
      BuildCodeForName(decl->mutable_enum_()->mutable_name());
      break;
    case Decl::VAR:
      BuildCodeForType(decl->mutable_var()->mutable_type(), true);
      // VAR decls can have getter/setter FUNC decls.
      if (decl->var().has_cpp_get()) {
        BuildCodeForFunc(decl->mutable_var()->mutable_cpp_get());
      }
      if (decl->var().has_cpp_set()) {
        BuildCodeForFunc(decl->mutable_var()->mutable_cpp_set());
      }
      break;
    case Decl::CONST:
      BuildCodeForType(decl->mutable_const_()->mutable_type(), true);
      break;
    case Decl::FUNC:
      BuildCodeForFunc(decl->mutable_func());
      break;
    case Decl::TYPE:
      BuildCodeForName(decl->mutable_fdecl()->mutable_name());
      break;
    case Decl::UNKNOWN:
      break;
  }
}

void CodeBuilder::BuildCodeForTopLevelDecls(DeclList* decls) {
  for (int i = 0; i < decls->size(); ++i) {
    Decl* decl = decls->Mutable(i);
    std::string full_namespace(decl->namespace_());
    const std::string clif_namespace = "clif";
    StrAppend(&full_namespace, "::", clif_namespace);
    NamespaceVector namespaces(full_namespace);
    for (const auto& namespace_name : namespaces) {
      StrAppend(&code_, "namespace ", namespace_name, " {\n");
      scoped_name_stack_.push_back(namespace_name.str());
    }
    BuildCodeForDecl(decl);
    current_line_.pop_back();
    while (!namespaces.empty()) {
      StrAppend(&code_, "} // ", scoped_name_stack_.back(), "\n");
      scoped_name_stack_.pop_back();
      namespaces.pop_back();
    }
  }
}

const std::string& CodeBuilder::BuildCode(
    AST* clif_ast, CLIFToClangTypeMap* clif_to_clang_type_map) {
  code_builder_clif_to_clang_type_map_ = clif_to_clang_type_map;
  for (const auto& file : clif_ast->usertype_includes()) {
    if (!file.empty()) {
      StrAppend(&code_, "#include \"", file, "\"\n");
    }
  }
  for (const auto& decl : clif_ast->decls()) {
    if (!decl.cpp_file().empty()) {
      StrAppend(&code_, "#include \"", decl.cpp_file(), "\"\n");
    }
  }
  if (!clif_ast->source().empty()) {
    current_line_.push_back(1);
    current_file_.push_back(clif_ast->source());
  }
  BuildCodeForTopLevelDecls(clif_ast->mutable_decls());
  if (!clif_ast->source().empty()) {
    current_line_.pop_back();
    current_file_.pop_back();
  }
  LLVM_DEBUG(llvm::dbgs() << clif_ast->DebugString());
  LLVM_DEBUG(llvm::dbgs() << code_);
  return code_;
}
}  // namespace clif
