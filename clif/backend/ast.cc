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

#include "clif/backend/ast.h"

#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "clif/backend/strutil.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/Frontend/ASTUnit.h"
#include "clang/Sema/Initialization.h"
#include "clang/Sema/Lookup.h"
#include "clang/Sema/Sema.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/Debug.h"

#define DEBUG_TYPE "clif_ast"

llvm::cl::opt<std::string> FLAGS_install_location(
    "install_location",
    llvm::cl::desc("Act as if the matcher were installed at this location."),
    llvm::cl::Hidden);

static std::unique_ptr<clang::ASTUnit> BuildClangASTFromCode(
    const std::vector<std::string>& command_line, const std::string& file_name,
    const std::string& file_contents, const std::string& program_name) {
  const std::vector<std::string>& clang_command = command_line;
  // |clang_command| includes argv[0], but buildASTFromCodeWithArgs expects
  // argv[0] to have been removed.
  std::vector<std::string> adjusted_clang_command(clang_command.begin() + 1,
                                                  clang_command.end());
  // Disable all warnings. We can't call AdjustClangArgsForSyntaxOnly,
  // which removes some options we need, such as -MM. The user will
  // see any warnings for the wrapped C++ code when it is built to
  // generate an object file. So these would be redundant anyway.
  adjusted_clang_command.push_back("-fsyntax-only");
  adjusted_clang_command.push_back("-w");
  return clang::tooling::buildASTFromCodeWithArgs(
      file_contents.c_str(), adjusted_clang_command, file_name.c_str(),
      clang_command[0].c_str(),
      std::make_shared<clang::PCHContainerOperations>(),
      clang::tooling::getClangSyntaxOnlyAdjuster());
}

namespace clif {

using clang::ClassTemplateDecl;
using clang::CXXRecordDecl;
using clang::DeclarationName;
using clang::DeclarationNameInfo;
using clang::DeclContext;
using clang::DeclContextLookupResult;
using clang::ast_matchers::MatchFinder;
// Both clang and clif have an "EnumDecl", so a using statement makes
// for ambiguity.
// using clang::EnumDecl;
using clang::FunctionDecl;
using clang::IdentifierInfo;
using clang::NamedDecl;
using clang::OverloadedOperatorKind;
using clang::QualType;
using clang::Sema;
using clang::SourceLocation;

template <class T>
bool IsForwardDeclarationOf(NamedDecl* decl) {
  auto t_decl = llvm::dyn_cast<T>(decl);
  return (t_decl && t_decl->getDefinition() != t_decl);
}

bool IsForwardDeclaration(NamedDecl* decl) {
  // Many decl types inherit from TagDecl, so no need for a complete
  // list here.
  return (IsForwardDeclarationOf<clang::TagDecl>(decl) ||
          IsForwardDeclarationOf<clang::VarDecl>(decl));
}

// TODO: Most of the DeclClassification logic is obsolete,
// delete it. The conversion function finder is one part that isn't
// obsolete.

void DeclClassification::Add(TranslationUnitAST* ast_, clang::NamedDecl* decl) {
  // Ignore forward declarations.
  if (IsForwardDeclaration(decl)) {
    LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString()
                            << " not classified (forward declaration)");
    return;
  }
  // Only classify function decls if they are:
  //
  // A) the canonical decl OR
  // B) A prototype decl in a different file than the canonical decl.
  //
  // This is because the same function prototype can be declared many
  // times, and the behavior is different than a true forward
  // declaration.
  //
  // CheckForLookup error will find if there was a declaration in the
  // correct file.
  auto* canonical =
      llvm::dyn_cast<clang::FunctionDecl>(decl->getCanonicalDecl());
  if (canonical && decl != canonical &&
      ast_->GetSourceFile(*decl) == ast_->GetSourceFile(*canonical)) {
    LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString() << " at "
                            << ast_->GetClangDeclLocForError(*decl)
                            << " not classified (second declaration)");
    return;
  }

  // Parameters and variables inside methods aren't referenceable.
  if (decl->getParentFunctionOrMethod() != nullptr ||
      clang::isa<clang::ParmVarDecl>(decl) ||
      clang::isa<clang::TemplateTypeParmDecl>(decl)) {
    LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString()
                            << " not classified (unreferenceable by Clif)");
    return;
  }
  if (clang::isa<clang::UsingDecl>(decl)) {
    LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString()
                            << " not classified (using decl)");
    return;
  }

  // CXXRecordDecls that are the children of a ClassTemplateDecl don't
  // need to be classified. They have the same name, and CLifLookup
  // will find the parent and the caller can extract the child if
  // necessary.
  auto* record_decl = llvm::dyn_cast<clang::CXXRecordDecl>(decl);
  if (record_decl != nullptr &&
      record_decl->getDescribedClassTemplate() != nullptr) {
    LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString()
                            << " not classified (using decl)");
    return;
  }
  // We don't classify class members because clif has different
  // rules for disambiguating them that we handle other places.  We
  // don't classify decls in anonymous namespaces because they
  // aren't usable in clif.
  if (!decl->isUnconditionallyVisible() || decl->isCXXClassMember() ||
      decl->isCXXInstanceMember() || decl->isInAnonymousNamespace()) {
    LLVM_DEBUG(llvm::dbgs()
               << decl->getQualifiedNameAsString()
               << " not classified (class or anonymous namespace member)");
    return;
  }
  // No need to classify things without names--these are anonymous
  // namespaces, structs and unions. We do classify the _members_ of
  // anonymous structs and unions when we encounter them, just not
  // the entities themselves.
  if (decl->getNameAsString().length() == 0) {
    LLVM_DEBUG(llvm::dbgs() << "not classified (no name)");
    return;
  }
  LLVM_DEBUG(llvm::dbgs() << decl->getQualifiedNameAsString() << " "
                          << ast_->GetClangDeclLocForError(*decl)
                          << " classified under " << decl->getNameAsString());
  map_.insert(std::make_pair(decl->getNameAsString(), decl));
  if (decl->getQualifiedNameAsString() != decl->getNameAsString()) {
    map_.insert(std::make_pair(decl->getQualifiedNameAsString(), decl));
  }
}

class TranslationUnitAST::ClassifyDeclsVisitor
    : public clang::RecursiveASTVisitor<ClassifyDeclsVisitor> {
 public:
  explicit ClassifyDeclsVisitor(TranslationUnitAST* ast) : ast_(ast) {}
  bool VisitNamedDecl(clang::NamedDecl* decl) {
    ast_->top_level_decls_.Add(ast_, decl);
    return true;
  }

 private:
  TranslationUnitAST* ast_;
};

// Find all functions of the form:
//
// void clif::PyObjAs(PyObject*, Foo**)
//   or
// void any::namespace::Clif_PyObjAs(PyObject*, Bar**)
//
// and keep track of the types of the second parameter (Foo and Bar in the
// example above).
static const size_t kConversionFunctionCount = 2;
static const char* kConversionFunctionNames[kConversionFunctionCount] = {
    "clif::PyObjAs", "Clif_PyObjAs"};

class TranslationUnitAST::ConversionFunctionFinder
    : public MatchFinder::MatchCallback {
 public:
  explicit ConversionFunctionFinder(TranslationUnitAST* ast) : ast_(ast) {}

  void run(const MatchFinder::MatchResult& match) override {
    const clang::FunctionProtoType* prototype = nullptr;
    for (size_t i = 0; i < kConversionFunctionCount; ++i) {
      const clang::FunctionDecl* func_decl;
      func_decl = match.Nodes.getNodeAs<clang::FunctionDecl>(
          llvm::StringRef(kConversionFunctionNames[i]));

      if (func_decl != nullptr) {
        prototype = func_decl->getType()->getAs<clang::FunctionProtoType>();
        break;
      }
    }
    assert(prototype != nullptr);

    QualType arg_type = prototype->getParamType(1);
    if (arg_type->isPointerType()) {
      QualType pointee_type = arg_type->getPointeeType();
      // Pointer to pointer: "SomeType**".
      if (pointee_type->isPointerType()) {
        pointee_type = pointee_type->getPointeeType();
        ast_->ptr_conversions_.insert(pointee_type.getCanonicalType());
        LLVM_DEBUG(llvm::dbgs() << "Ptr conversion found for type "
                                << pointee_type.getAsString());
      } else {
        // Pointer to unique_ptr: "std::unique_ptr<SomeType>*"
        if (ast_->GetStdTemplateDecl(kUniquePtrName) ==
            ast_->GetQualTypeTemplateDecl(pointee_type)) {
          QualType template_param_type =
              ast_->GetTemplateArgType(pointee_type).getCanonicalType();
          ast_->unique_ptr_conversions_.insert(template_param_type);
          LLVM_DEBUG(llvm::dbgs() << "Unique_ptr conversion found for type "
                                  << template_param_type.getAsString());
        }
      }
    }
  }

  void FindConversionFunctions() {
    clang::ast_matchers::MatchFinder finder;
    for (size_t i = 0; i < kConversionFunctionCount; ++i) {
      finder.addMatcher(
          clang::ast_matchers::functionDecl(
              clang::ast_matchers::hasName(kConversionFunctionNames[i]),
              clang::ast_matchers::parameterCountIs(2))
              .bind(llvm::StringRef(kConversionFunctionNames[i])),
          this);
    }
    finder.matchAST(ast_->GetASTContext());
  }

 private:
  TranslationUnitAST* ast_;
};

bool TranslationUnitAST::IsStdSmartPtr(const QualType& template_type) {
  ClassTemplateDecl* template_decl = GetQualTypeTemplateDecl(template_type);
  if (template_decl == nullptr) {
    return false;
  }
  return ((GetStdTemplateDecl(kUniquePtrName) == template_decl) ||
          (GetStdTemplateDecl(kSharedPtrName) == template_decl));
}

clang::ClassTemplateDecl* TranslationUnitAST::GetStdTemplateDecl(
    const std::string& template_name) {
  clang::Sema& sema = GetSema();
  if (sema.getStdNamespace() == nullptr) {
    return nullptr;
  }
  ClifLookupResult result =
      LookupScopedSymbolInContext(sema.getStdNamespace(), template_name);
  if (result.Size() != 1) {
    return nullptr;
  }
  auto* std_templ = llvm::dyn_cast<clang::ClassTemplateDecl>(result.GetFirst());
  if (std_templ == nullptr) {
    return nullptr;
  }
  // The declaration originally found by lookup could be a forward
  // declaration or some other noncanonical declaration.
  return std_templ->getCanonicalDecl();
}

clang::ClassTemplateDecl* TranslationUnitAST::GetQualTypeTemplateDecl(
    const QualType& qual_type, const clang::TemplateArgument** args) {
  clang::ClassTemplateDecl* templ = nullptr;
  auto* record = qual_type->getAs<clang::RecordType>();
  if (record != nullptr) {
    auto* special = llvm::dyn_cast<clang::ClassTemplateSpecializationDecl>(
        record->getDecl());
    if (!special) {
      return nullptr;
    }
    templ = special->getSpecializedTemplate();
    if (args) {
      *args = special->getTemplateArgs().data();
    }
  } else {
    auto* special = qual_type->getAs<clang::TemplateSpecializationType>();
    if (!special) {
      return nullptr;
    }
    if (special->isTypeAlias()) {
      return GetQualTypeTemplateDecl(special->getAliasedType(), args);
    }
    templ = llvm::dyn_cast<clang::ClassTemplateDecl>(
        special->getTemplateName().getAsTemplateDecl());
    if (args) {
      *args = special->getArgs();
    }
  }
  return templ->getCanonicalDecl();
}

// Return the type of the first template argument.
QualType TranslationUnitAST::GetTemplateArgType(const QualType& type) {
  const clang::TemplateArgument* args;
  GetQualTypeTemplateDecl(type, &args);
  assert(clang::isa<clang::TemplateTypeParmDecl>(
             GetQualTypeTemplateDecl(type, &args)
                 ->getTemplateParameters()
                 ->getParam(0)) &&
         "Non templateargument to template.");
  return args[0].getAsType();
}

QualType TranslationUnitAST::BuildTemplateType(
    clang::ClassTemplateDecl* template_decl, QualType arg_qual_type) {
  clang::TemplateName template_name(template_decl);
  clang::TemplateArgumentListInfo args;
  clang::TemplateArgument template_arg(arg_qual_type);
  args.addArgument(GetSema().getTrivialTemplateArgumentLoc(
      template_arg, arg_qual_type, SourceLocation()));
  return GetSema().CheckTemplateIdType(template_name, SourceLocation(), args);
}

bool TranslationUnitAST::Init(const std::string& code,
                              const std::vector<std::string>& args,
                              const std::string& input_file_name) {
  std::vector<std::string> modified_args = args;
  std::string original_arg_0 = args[0];
  if (!FLAGS_install_location.empty()) {
    modified_args[0] = FLAGS_install_location;
    LLVM_DEBUG(llvm::dbgs()
               << "Using " << modified_args[0] << " for install_location");
  }
  ast_ = ::BuildClangASTFromCode(modified_args, input_file_name, code,
                                 original_arg_0);
  if (ast_ == nullptr || ast_->getDiagnostics().hasErrorOccurred() ||
      ast_->getDiagnostics().hasFatalErrorOccurred() ||
      ast_->getDiagnostics().hasUncompilableErrorOccurred()) {
    return false;
  }
  ClassifyDeclsVisitor classifier(this);
  classifier.TraverseDecl(GetTU());
  ConversionFunctionFinder conversion_finder(this);
  conversion_finder.FindConversionFunctions();
  HandleBuiltinTypes();
  return true;
}

bool TranslationUnitAST::HasDefaultConstructor(
    clang::CXXRecordDecl* class_decl) const {
  return ConstructorIsAccessible(
      ast_->getSema().LookupDefaultConstructor(class_decl));
}

// For copyable types, CLIF's generated code invokes both of the copy
// constructor and the copy assignment operator in the backend. Thus, both of
// the copy constructors and copy assignment operators are required.
bool TranslationUnitAST::IsClifCopyable(
    clang::CXXRecordDecl* class_decl) const {
  const int kNoQualifiers = 0;
  Sema& sema = ast_->getSema();
  bool copy_constructor = ConstructorIsAccessible(
      sema.LookupCopyingConstructor(class_decl, kNoQualifiers));
  bool copy_assignment =
      MethodIsAccessible(sema.LookupCopyingAssignment(class_decl, kNoQualifiers,
                                                      false,  // non-rvalue
                                                      kNoQualifiers));
  return copy_constructor && copy_assignment;
}

// For movable return values, CLIF sets its `cpp_movable` as true
// in .opb. Then, CLIF's generated code invokes the move constructor to hold
// the object in the target language.
bool TranslationUnitAST::IsClifMovable(clang::CXXRecordDecl* class_decl) const {
  const int kNoQualifiers = 0;
  Sema& sema = ast_->getSema();
  bool move_constructor = ConstructorIsAccessible(
      sema.LookupMovingConstructor(class_decl, kNoQualifiers));
  bool move_assignment =
      MethodIsAccessible(sema.LookupMovingAssignment(class_decl, kNoQualifiers,
                                                     false,  // non-rvalue
                                                     kNoQualifiers));
  return move_constructor && move_assignment;
}

bool TranslationUnitAST::MethodIsAccessible(
    const clang::CXXMethodDecl* method) const {
  return (method && !method->isDeleted() &&
          method->getAccess() == clang::AccessSpecifier::AS_public);
}

bool TranslationUnitAST::ConstructorIsAccessible(
    clang::CXXConstructorDecl* ctor) const {
  if (ctor == nullptr) {
    return false;
  }
  auto entity = clang::InitializedEntity::InitializeResult(
      SourceLocation(),
      ast_->getASTContext().getQualifiedType(
          ctor->getParent()->getTypeForDecl(), clang::Qualifiers())
#if LLVM_VERSION_MAJOR < 14
      , false
#endif
  );
  Sema& sema = ast_->getSema();
  auto access = sema.CheckConstructorAccess(
      SourceLocation(), ctor,
      clang::DeclAccessPair::make(ctor, ctor->getAccess()), entity,
      clang::PartialDiagnostic(0,  // Don't print anything on error.
                               ast_->getASTContext().getDiagAllocator()));
  return (!ctor->isDeleted() && access == Sema::AccessResult::AR_accessible);
}

bool TranslationUnitAST::DestructorIsAccessible(
    clang::CXXRecordDecl* class_decl) const {
  clang::CXXDestructorDecl* dtor = class_decl->getDestructor();
  if (dtor == nullptr) {
    return true;  // No access violation possible.
  }
  Sema& sema = ast_->getSema();
  auto access = sema.CheckDestructorAccess(
      SourceLocation(), dtor,
      clang::PartialDiagnostic(0,  // Don't print anything on error.
                               ast_->getASTContext().getDiagAllocator()));
  return (dtor->isDeleted() || access == Sema::AccessResult::AR_accessible);
}

void TranslationUnitAST::HandleBuiltinTypes() {
  for (const auto& type : ast_->getASTContext().getTypes()) {
    if (type->getTypeClass() == clang::Type::Builtin) {
      const clang::BuiltinType* builtin =
          static_cast<clang::BuiltinType*>(type);
      const char* name =
          builtin->getNameAsCString(ast_->getASTContext().getPrintingPolicy());
      builtin_types_[name] = type;
    }
  }
}

QualType TranslationUnitAST::FindBuiltinType(
    const std::string& type_name) const {
  auto atype = builtin_types_.find(type_name);
  return (atype == builtin_types_.end() ? QualType()
                                        : QualType(atype->second, 0));
}

ClifLookupResult TranslationUnitAST::LookupOperatorOrConversionFunction(
    clang::DeclContext* context, const std::string& name) {
  const std::string operator_keyword = "operator";
  auto& ast = GetASTContext();
  const std::string& token =
      name.substr(operator_keyword.length(), name.length());
  // check if it's an overloaded operator or implicit type conversion function.
  bool is_conversion = true;
  // Sema::LookupOverloadedOperatorName is only valid during
  // parsing, so find the clang operator name in the raw clang style.
  DeclarationNameInfo operator_name;
#define OVERLOADED_OPERATOR(Name, Spelling, Token, Unary, Binary, MemberOnly) \
  if (token == (Spelling)) {                                                  \
    is_conversion = false;                                                    \
    operator_name = DeclarationNameInfo(                                      \
        ast.DeclarationNames.getCXXOperatorName(clang::OO_##Name),            \
        SourceLocation());                                                    \
  }
#define OVERLOADED_OPERATOR_MULTI(Name, Spelling, Unary, Binary, MemberOnly) \
  if (token == (Spelling)) {                                                 \
    is_conversion = false;                                                   \
    operator_name = DeclarationNameInfo(                                     \
        ast.DeclarationNames.getCXXOperatorName(clang::OO_##Name),           \
        SourceLocation());                                                   \
  }
#include "clang/Basic/OperatorKinds.def"  // NO_LINT
  // Clang handles member operator overloading separate from normal
  // operator lookup
  auto class_decl = llvm::dyn_cast<CXXRecordDecl>(context);
  if (class_decl != nullptr && is_conversion) {
    auto conversion_decls = class_decl->getVisibleConversionFunctions();
    ClifLookupResult result(conversion_decls);
    return result;
  }

  Sema::LookupNameKind lookup_kind =
      (class_decl != nullptr ? Sema::LookupNameKind::LookupMemberName
                             : Sema::LookupNameKind::LookupOperatorName);
  clang::LookupResult results(GetSema(), operator_name, lookup_kind);
  results.suppressDiagnostics();
  GetSema().LookupQualifiedName(results, context, false);
  return ClifLookupResult(results);
}

ClifLookupResult TranslationUnitAST::LookupClassMember(
    const std::string& name) {
  assert(!contexts_.empty());
  CXXRecordDecl* class_decl = contexts_.top();
  LLVM_DEBUG(llvm::dbgs() << "Looking up class member " << name
                          << " in context "
                          << class_decl->getQualifiedNameAsString());

  auto& ast = GetASTContext();
  DeclarationNameInfo decl_name = DeclarationNameInfo(
      ast.DeclarationNames.getIdentifier(&ast.Idents.get(name.c_str())),
      SourceLocation());
  clang::LookupResult result(GetSema(), decl_name,
                             Sema::LookupNameKind::LookupMemberName);
  result.suppressDiagnostics();
  GetSema().LookupQualifiedName(result, class_decl, false);
  return ClifLookupResult(result);
}

clang::DeclContext* TranslationUnitAST::GetDeclContextFromDecl(
    clang::Decl* decl) {
  // Remove any typedefs and other sugar.
  if (auto typedef_decl = llvm::dyn_cast<clang::TypedefNameDecl>(decl)) {
    decl = typedef_decl->getUnderlyingType()
               .getSingleStepDesugaredType(GetASTContext())
               ->getAsCXXRecordDecl();
  }
  // Dig into any template specialization.
  if (auto special_decl =
          llvm::dyn_cast_or_null<clang::ClassTemplateSpecializationDecl>(
              decl)) {
    decl = special_decl->getSpecializedTemplate();
  }
  if (auto templ_decl =
          llvm::dyn_cast_or_null<clang::ClassTemplateDecl>(decl)) {
    return templ_decl->getTemplatedDecl();
  } else {
    return llvm::dyn_cast_or_null<DeclContext>(decl);
  }
}

ClifLookupResult TranslationUnitAST::LookupScopedSymbolInContext(
    clang::Decl* decl, const std::string& qualified_name) {
  NamespaceVector namespace_components(qualified_name);
  DeclContextLookupResult lookup_result;
  DeclContext* decl_context = GetDeclContextFromDecl(decl);
  for (const auto& name_component : namespace_components) {
    if (IsOperatorOrConversionFunction(name_component.str())) {
      return LookupOperatorOrConversionFunction(decl_context,
                                                name_component.str());
    }
    IdentifierInfo& name_ident = GetASTContext().Idents.get(name_component);
    DeclarationName decl_name =
        GetASTContext().DeclarationNames.getIdentifier(&name_ident);
    lookup_result = decl_context->lookup(decl_name);

    if (lookup_result.empty() || lookup_result.front()->isInvalidDecl()) {
      return ClifLookupResult(lookup_result);
    }
    decl_context = GetDeclContextFromDecl(lookup_result.front());
    assert((name_component == namespace_components.back() ||
            decl_context != nullptr) &&
           "Valid decl without a DeclContext in a fully-qualified name.");
  }
  return ClifLookupResult(lookup_result);
}

ClifLookupResult TranslationUnitAST::LookupScopedSymbol(
    const std::string& qualified_name) {
  // If the name begins with "::" then use a TU-level lookup.
  // Likewise if we haven't pushed any scopes.
  if (qualified_name.substr(0, 2) != "::" && !contexts_.empty()) {
    CXXRecordDecl* class_decl = contexts_.top();
    ClifLookupResult result =
        LookupScopedSymbolInContext(class_decl, qualified_name);
    if (result.Size() != 0) {
      return result;
    }
  }
  return LookupScopedSymbolInContext(GetTU(), qualified_name);
}

}  // namespace clif
