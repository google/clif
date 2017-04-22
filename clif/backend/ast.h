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
#ifndef CLIF_BACKEND_AST_H_
#define CLIF_BACKEND_AST_H_

// Wrapper for the CLIF backend to retrieve Clang ASTs and TUs.
// Example use:
//
//   std::unique_ptr<TranslationUnitAST> ast(new TranslationUnitAST());
//   ast->init("input.cpp", ASTTranslationUnit::CompilerArgs()));
//   ast->Dump();

#include <memory>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "gtest/gtest.h"  // Defines FRIEND_TEST.
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/raw_ostream.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/CXXInheritance.h"
#include "clang/AST/Decl.h"
#include "clang/AST/PrettyPrinter.h"
#include "clang/Frontend/ASTUnit.h"
#include "clang/Sema/Lookup.h"

extern llvm::cl::opt<std::string> install_location;


namespace clif {

static const char kSharedPtrName[] = "shared_ptr";
static const char kUniquePtrName[] = "unique_ptr";

class TranslationUnitASTTest;

// In clang, decl subtypes inherit from NamedDecl.  Dynamically cast
// the contained value to the appropriate kind.
typedef std::unordered_multimap<std::string,
                                clang::NamedDecl*> DeclMap;
typedef std::pair<DeclMap::iterator, DeclMap::iterator> DeclRange;

struct HashQualType {
  size_t operator()(const clang::QualType& qual_type) const {
    size_t hash_value;
    static_assert(sizeof(size_t) <= sizeof(clang::QualType),
                  "size_t is bigger than a QualType.");
    memcpy(&hash_value, &qual_type, sizeof(hash_value));
    return hash_value;
  }
};

typedef std::unordered_set<clang::QualType, HashQualType>
KnownToPointerConversionTypes;

// Utility class to abstract away the differences between lookups done
// via clif namespace rules (see below) and normal C++ lookups in
// classes.
class ClifLookupResult {
 public:
  typedef std::vector<clang::NamedDecl*> ResultVector;
  ClifLookupResult() { }
  explicit ClifLookupResult(const DeclRange& decls) {
    for (auto decl = decls.first; decl != decls.second; decl++) {
      results_.push_back(decl->second);
    }
  }
  explicit ClifLookupResult(const clang::LookupResult& results) {
    for (auto decl : results) {
      results_.push_back(decl);
    }
  }
  explicit ClifLookupResult(const clang::DeclContextLookupResult& decls) {
    for (auto& decl : decls) {
      results_.push_back(decl);
    }
  }
  explicit ClifLookupResult(const clang::CXXRecordDecl::ctor_range& decls) {
    for (const auto& decl : decls) {
      results_.push_back(decl);
    }
  }

  void AddResult(clang::NamedDecl* decl) {
    results_.push_back(decl);
  }

  void AddResults(const ClifLookupResult& more) {
    results_.insert(results_.end(), more.results_.begin(), more.results_.end());
  }

  clang::NamedDecl* GetFirst() const { return results_.front(); }
  std::vector<clang::NamedDecl*>& GetResults() { return results_; }
  const std::vector<clang::NamedDecl*>& GetResults() const { return results_; }
  unsigned Size() const { return results_.size(); }
  // For debugging only.
  void Dump();

 private:
  ResultVector results_;
};

class TranslationUnitAST;

// Utility class for tracking different declarations that exist
// outside of classes.
class DeclClassification {
 public:
  ClifLookupResult Lookup(const std::string& name) {
    return ClifLookupResult(map_.equal_range(name));
  }

  void Add(TranslationUnitAST* ast_, clang::NamedDecl* decl);

 private:
  DeclMap map_;
};

class TranslationUnitAST {
 public:
  TranslationUnitAST() { }
  virtual ~TranslationUnitAST() {
    assert(contexts_.empty() && "Context stack not exhausted.");
  }

  bool Init(const std::string& code,
            const std::vector<std::string>& args,
            const std::string& input_file_name);

  void HandleBuiltinTypes();

  void Dump() const {
    GetTU()->dump();
  }

  // The most commonly used args to clang.  Useful mostly for
  // testing. Real clients should use the arguments they would use to
  // compile the headers included in the clif proto.  Passed as an
  // argument to the constructor in case a client wants to override or
  // add.  Returned by a function to allow defining in the header.
  static std::vector<std::string> CompilerArgs() {
    static const char* c_args[] = {
      "clifbackend",
      "-x", "c++",
      "-std=gnu++11",
      "-DCOMPILER_GCC3",
      "-c", "-I.",
      nullptr
    };
    // Every function down the chain wants a vector of C++ strings,
    // but the style guide forbids static vectors, as well as static
    // strings, so convert every time. This code is not performance
    // critical.
    std::vector<std::string> args;
    for (const char** iter = c_args; *iter != nullptr; iter++) {
      args.emplace_back(*iter);
    }
    return args;
  }

  // Builtin types don't have decls, and thus aren't found by scoped
  // lookup. So handle them separately here. Clang doesn't provide a
  // quick lookup mechanism, so use our own.  Fortunately, a
  // builtin-type is always fully qualified, so if "type_name" is a
  // built-in type, it is also the fully qualified name. If the
  // given type isn't found, getTypePtrOrNull() on the returned
  // value will be null.
  clang::QualType FindBuiltinType(const std::string& type_name) const;

  // Lookup a name that includes in the current context. If a symbol
  // is not found the current context, look for it starting at the TU
  // context.
  ClifLookupResult LookupScopedSymbol(const std::string& qualified_name);
  // Lookup a qualified name in the given context.
  ClifLookupResult LookupScopedSymbolInContext(
      clang::Decl* decl, const std::string& qualified_name);

  clang::DeclContext* GetDeclContextFromDecl(clang::Decl* decl);

  // Lookup C++ declarations according clif rules, which don't follow
  // C++ scoping rules.
  ClifLookupResult ClifLookup(const std::string& name) {
    if (name.find(':') != std::string::npos) {
      return LookupScopedSymbol(name);
    }
    if (contexts_.empty()) {
      return top_level_decls_.Lookup(name);
    }
    return LookupClassMember(name);
  }

  // Lookup an operator in the given context.
  ClifLookupResult LookupOperator(clang::DeclContext* context,
                                  const std::string& token);

  // A name used by clif may or may not be defined within a class. So
  // for type names only, we want to do a normal cliff lookup and
  // then, if it isn't found, do a top-level lookup. Normal class
  // members should always be found within the class.
  ClifLookupResult ClifLookupType(const std::string& name) {
    ClifLookupResult result = ClifLookup(name);
    if (result.Size() != 0) {
      return result;
    }
    return top_level_decls_.Lookup(name);
  }

  // Clif lookup collapses C++ namespaces into a single view, but
  // treats classes (including inner-classes) as normal naming scopes.
  // This approach does not map well to C++ lookup.  If we are inside
  // the TU's context, then lookup should examine all non-class
  // members in all namespaces (which we got via the decl-classifier).
  // If we are inside a class's context, we should examine just the
  // declarations inside that class.  We need a stack to handle
  // inner-classes at arbitrary depth, because CXXRecord lookup does
  // not search in nested classes.
  void PushLookupContext(clang::CXXRecordDecl* context) {
    contexts_.push(context);
  }

  void PopLookupContext() {
    contexts_.pop();
  }

  clang::Decl* GetCurrentLookupScope() {
    if (contexts_.empty()) {
      return GetTU();
    }
    return contexts_.top();
  }

  std::string GetLookupScopeName() {
    if (contexts_.empty()) {
      return "<top-level>";
    } else {
      return GetClangDeclNameForError(
          *(llvm::dyn_cast<clang::NamedDecl>(contexts_.top())));
    }
  }

  clang::ASTContext& GetASTContext() const {
    return ast_->getASTContext();
  }

  clang::Sema& GetSema() const {
    return ast_->getSema();
  }

  // The AST retains ownership of the returned pointer.
  clang::TranslationUnitDecl* GetTU() const {
    return GetASTContext().getTranslationUnitDecl();
  }

  std::string GetClangDeclNameForError(
      const clang::NamedDecl& clang_decl) const {
    std::string name;
    llvm::raw_string_ostream stream(name);
    clang_decl.getNameForDiagnostic(stream,
                                    ast_->getASTContext().getPrintingPolicy(),
                                    true);
    return stream.str();
  }

  std::string GetClangDeclLocForError(
      const clang::NamedDecl& clang_decl) const {
    return clang_decl.getLocStart().printToString(
        ast_->getASTContext().getSourceManager());
  }

  std::string GetSourceFile(const clang::NamedDecl& clang_decl) const {
    clang::PresumedLoc start =
        ast_->getASTContext().getSourceManager().getPresumedLoc(
            clang_decl.getLocStart());
    // Certain built-ins don't have valid start locations, and clang
    // returns the empty string during normal builds, but asserts in
    // debug builds. Match that behavior for all builds. From Clif's
    // perspective, an empty string is equivalent to "not in the
    // imported file."
    if (start.isValid()) {
      return start.getFilename();
    } else {
      return "";
    }
  }

  bool IsKnownPtrConversionType(const clang::QualType clang_type) {
    return IsKnownConversionType(clang_type, ptr_conversions_);
  }

  bool IsKnownUniquePtrConversionType(const clang::QualType clang_type) {
    return IsKnownConversionType(clang_type, unique_ptr_conversions_);
  }

  void AddPtrConversionType(const clang::QualType qual_type) {
    ptr_conversions_.insert(qual_type.getCanonicalType());
  }

  void AddUniquePtrConversionType(const clang::QualType qual_type) {
    unique_ptr_conversions_.insert(qual_type.getCanonicalType());
  }

  bool HasDefaultConstructor(clang::CXXRecordDecl* class_decl) const;

  bool IsClifCopyable(clang::CXXRecordDecl* class_decl) const;

  bool IsCppMovable(clang::CXXRecordDecl* class_decl) const;

  bool ConstructorIsAccessible(clang::CXXConstructorDecl* ctor) const;

  bool MethodIsAccessible(const clang::CXXMethodDecl* method) const;

  bool DestructorIsAccessible(clang::CXXRecordDecl* class_decl) const;

  bool IsOperatorFunction(const std::string& name) const {
    const std::string operator_keyword = "operator";
    size_t last_component = name.rfind("::");
    if (last_component == std::string::npos) {
      return operator_keyword == name.substr(0, operator_keyword.length());
    }
    return (operator_keyword ==
            name.substr(last_component + 2, operator_keyword.length()));
  }

  // Determine if this type is a template of the form std::unique_ptr<A>
  // or std::shared_ptr<B>.
  bool IsStdSmartPtr(const clang::QualType& template_type);

  // Retrieve the template declaration of the template
  // "std::<template_name>" or nullptr if no such template exists.
  clang::ClassTemplateDecl* GetStdTemplateDecl(
      const std::string& template_name);

  // Given a QualType, return the associated ClassTemplateDecl for any
  // template it may describe. If one is found, and args is not
  // nullptr, set *args to a list of template argument types.
  clang::ClassTemplateDecl* GetQualTypeTemplateDecl(
      const clang::QualType& qual_type,
      const clang::TemplateArgument** args = nullptr);

  // Given a template qualtype A<B, ...>, return B's QualType.
  clang::QualType GetTemplateArgType(const clang::QualType& template_type);

  // Given TemplateDecl A and QualType B, return the QualType
  // corresponding to A<B>.
  clang::QualType BuildTemplateType(clang::ClassTemplateDecl* template_decl,
                                    clang::QualType arg_qual_type);

 private:
  clang::DeclarationNameInfo GetDeclarationName(const std::string& name);

  ClifLookupResult LookupClassMember(const std::string& name);

  bool IsKnownConversionType(const clang::QualType& qual_type,
                             const KnownToPointerConversionTypes& conversions) {
    clang::QualType working_type = qual_type.getCanonicalType();
    if (working_type->isPointerType() || working_type->isReferenceType()) {
      working_type = working_type->getPointeeType();
    }
    return (conversions.find(working_type.getCanonicalType()) !=
            conversions.end());
  }

  clang::CompilerInvocation* invocation_;
  std::unique_ptr<clang::ASTUnit> ast_;

  class ClassifyDeclsVisitor;
  class ConversionFunctionFinder;
  std::stack<clang::CXXRecordDecl*> contexts_;
  std::unordered_map<std::string, const clang::Type*> builtin_types_;
  DeclClassification top_level_decls_;
  KnownToPointerConversionTypes ptr_conversions_;
  KnownToPointerConversionTypes unique_ptr_conversions_;

  FRIEND_TEST(TranslationUnitASTTest, FindConversionFunctions);
};

}  // namespace clif

#endif  // CLIF_BACKEND_AST_H_
