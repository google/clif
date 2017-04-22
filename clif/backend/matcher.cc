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

// Takes clif protos and matches the functions referenced the
// appropriate C++ functions and types.

#include "clif/backend/matcher.h"

#include <algorithm>

#include "clif/backend/strutil.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/raw_ostream.h"
#include "clang/AST/Expr.h"
#include "clang/Sema/Initialization.h"
#include "clang/Sema/Sema.h"
#include "clang/Sema/SemaDiagnostic.h"
#include "clang/Tooling/Core/QualTypeNames.h"

// TODO: Switch to clang diagnostics mechanism for errors.

#define DEBUG_TYPE "clif_matcher"


namespace clif {

using clang::ClassTemplateSpecializationDecl;
using clang::CXXRecordDecl;
using clang::DeclarationName;
using clang::DeclContext;
using clang::EnumConstantDecl;
using clang::FunctionDecl;
using clang::FunctionTemplateDecl;
using clang::InitializedEntity;
using clang::NamedDecl;
using clang::NamespaceDecl;
using clang::QualType;
using clang::Sema;

const std::string GetDeclNativeName(const Decl& decl) {
  const char unknown_name[] = "(unknown)";
  switch (decl.decltype_()) {
    case Decl::CLASS:    return decl.class_().name().native();
    case Decl::ENUM:     return decl.enum_().name().native();
    case Decl::VAR:      return decl.var().name().native();
    case Decl::CONST:    return decl.const_().name().native();;
    case Decl::FUNC:     return decl.func().name().native();
    case Decl::TYPE:     return decl.fdecl().name().cpp_name();
    case Decl::UNKNOWN:  return unknown_name;
  }
}

std::string GetGloballyQualifiedName(const NamedDecl* decl) {
  std::string name("::");
  StrAppend(&name, decl->getQualifiedNameAsString());
  return name;
}

static const char kConstToken[] = "const ";  // Trailing space is important.
static const char kCppCharArray[] = "const char [";
static const char kClifCharArray[] = "::clif::char_ptr";

static std::string GetErrorCodeString(ClifErrorCode code) {
  switch (code) {
    case kOK:
      return "";
    case kNotFound:
      return "C++ symbol not found.";
    case kMultipleMatches:
      return ("Multiple C++ symbols with same name found. "
              "Possibilities include:");
    case kNotInImportFile:
      return "Declaration was found, but not inside the required file.";
    case kTypeMismatch:
      // TypeCheckLookupResult will fill in dynamic message.
      return "";
    case kReturnValueMismatch:
      return "C++ function return type didn't match.";
    case kParameterMismatch:
      return "Function parameter types didn't match.";
    case kConstVarError:
      return ("Symbol declared constant in Clif, but matched"
              " with non-constant C++ declaration.");
    case kMissingEnumerator:
      return "Clif enumerator not present in C++:";
    case kNonConstParameterType:
      return "A pointer or reference input parameter must be constant.";
    case kNonPointerReturnType:
      return "An output parameter must be either a pointer or a reference.";
    case kNonPointerType:
      return "Clif requires this parameter to be a pointer.";
    case kConstReturnType:
      return "Output parameter is constant.";
    case kConstVariable:
      return "Clif expects a variable, but C++ declares it constant.";
    case kIncompatibleTypes:
      return "Non-matching types.";
    case kParameterCountsDiffer:
      return "Parameter counts differ.";
    case kMultipleInheritance:
      return "Clif doesn't support classes with multiple inheritance.";
    case kNoDefinitionAvailable:
      return ("Clif requests matching class-members, but C++ didn't include "
              "the class definition.");
    case kNotCallable:
      return "Clif callables require a std::function.";
    case kUnspecializableTemplate:
      return "Function template can't be specialized with these arguments.";
    case kConstructorNotFound:
      return "Class constructor not found.";
    case kClassMethod:
      return ("Clif function with @classmember decorator matches a "
              "non-static C++ class member function.");
    case kCppStaticMethod:
      return ("Clif function without a @classmethod decorator matches a "
              "static C++ class member function.");
    case kNonStaticClassGlobalFunctionDecl:
      return ("Globally-declared function matches a non-static C++ class "
              "member function.");
  }
}

static void ReportMultimatchError(
    const ClifMatcher& matcher,
    const TranslationUnitAST* ast,
    const std::vector<std::pair<const FunctionDecl*, FuncDecl>> &matches,
    Decl* clif_decl) {
  ClifError multimatch_error(matcher, kMultipleMatches);
  for (auto decl_pair : matches) {
    multimatch_error.AddClangDeclAndLocation(ast, decl_pair.first);
  }
  multimatch_error.Report(clif_decl);
}

void ClifError::AddMessage(const std::string& message) {
  messages_.push_back(message);
}

const char kMessageIndent[] = "    ";

void ClifError::AddClangDeclAndLocation(const TranslationUnitAST* ast,
                                        const NamedDecl* decl) {
  // Weird spacing to make final message parsable to humans.
  std::string message;
  StrAppend(&message,
            "Rejected Candidate:\n  ",
            kMessageIndent, ast->GetClangDeclNameForError(*decl),
            " at ", ast->GetClangDeclLocForError(*decl));
  AddMessage(message);
}

std::string ClifError::Report(Decl* clif_decl) {
  std::string name = GetDeclNativeName(*clif_decl);
  if (name.empty()) {
    name = matcher_.GetDeclCppName(*clif_decl);
  }
  std::string error;
  StrAppend(&error, "No suitable matches found for ", name);
  if (name != matcher_.GetDeclCppName(*clif_decl)) {
    StrAppend(&error,
              " (with C++ name: ",
              matcher_.GetDeclCppName(*clif_decl), ")");
  }
  if (clif_decl->line_number() != 0) {
    StrAppend(&error, " on line ", clif_decl->line_number());
  }
  StrAppend(&error, ".\n");
  if (code_ != kOK &&
      code_ != kTypeMismatch &&
      code_ != kNotFound &&
      code_ != kConstructorNotFound) {
    StrAppend(&error, kMessageIndent, GetErrorCodeString(code_), "\n");
  } else {
    if (code_ == kNotFound) {
      // First message contains the lookup location.
      StrAppend(&error, kMessageIndent, "C++ symbol \"",
                matcher_.GetDeclCppName(*clif_decl),
                "\" not found in ", messages_.front(), ".\n");
      messages_.erase(messages_.begin());
    } else if (code_ == kConstructorNotFound) {
      // First message contains the lookup location.
      StrAppend(&error, kMessageIndent,
                "No viable constructor found in",
                messages_.front(), ".\n");
      messages_.erase(messages_.begin());
    }
  }

  for (const auto& message : messages_) {
    StrAppend(&error, kMessageIndent, message, "\n");
  }
  llvm::errs() << error;
  clif_decl->set_not_found(error);
  return error;
}

const std::string ClifMatcher::GetDeclCppName(const Decl& decl) const {
  const char unknown_name[] = "(unknown)";
  std::string cpp_name;
  switch (decl.decltype_()) {
    case Decl::CLASS:    cpp_name = decl.class_().name().cpp_name(); break;
    case Decl::ENUM:     cpp_name = decl.enum_().name().cpp_name(); break;
    case Decl::VAR:      return decl.var().name().cpp_name();
    case Decl::CONST:    return decl.const_().name().cpp_name();
    case Decl::FUNC:     return decl.func().name().cpp_name();
    case Decl::TYPE:     cpp_name = decl.fdecl().name().cpp_name(); break;
    case Decl::UNKNOWN:  return unknown_name;
  }

  const CodeBuilder::NameMap& name_map = builder_.OriginalNames();
  auto pair = name_map.find(cpp_name);
  assert(pair != name_map.end() &&
         "Original name of a class/enum/type not present.");
  return pair->second;
}

std::string ClifMatcher::GetParallelTypeNames() const {
  std::string message;
  for (auto types : type_mismatch_stack_) {
    StrAppend(&message,
              "\n Compare:\n",
              "    Clif Type: \"", types.second, "\" with \n",
              "     C++ Type: \"", types.first, "\"");
  }
  return message;
}

bool ClifTypeDerivedFromClangType(const QualType& clang_type,
                                  const QualType& clif_type) {
  CXXRecordDecl* clang_type_decl = clang_type->getAsCXXRecordDecl();
  if (clang_type_decl == nullptr) {
    return false;
  }

  CXXRecordDecl* clif_type_decl = clif_type->getAsCXXRecordDecl();
  if (clif_type_decl == nullptr) {
    return false;
  }

  if (clif_type_decl->isDerivedFrom(clang_type_decl)) {
    return true;
  }

  return false;
}

ClifErrorCode ClifMatcher::CheckForLookupError(
    const ClifLookupResult& decls) const {
  ClifError wrong_file(*this, kOK);
  ClifLookupResult valid_decls;
  for (auto decl : decls.GetResults()) {
    if (ImportedFromCorrectFile(*decl, &wrong_file)) {
      valid_decls.AddResult(decl);
    }
  }
  if (valid_decls.Size() == 0) {
    // Nothing found at all vs things found in wrong file.
    if (decls.Size() == 0) {
      ClifError error(*this, kNotFound, ast_->GetLookupScopeName());
      error.Report(CurrentDecl());
      return kNotFound;
    }
    wrong_file.Report(CurrentDecl());
    return kNotInImportFile;
  }
  if (valid_decls.Size() > 1) {
    ClifError error(*this, kMultipleMatches);
    for (auto decl : valid_decls.GetResults()) {
      error.AddClangDeclAndLocation(ast_.get(), decl);
    }
    error.Report(CurrentDecl());
    return kMultipleMatches;
  }
  return kOK;
}

bool ClifMatcher::CompileMatchAndSet(
    const std::vector<std::string>& compiler_args,
    const std::string& input_file_name,
    const AST& clif_ast,
    AST* modified_clif_ast) {
  DEBUG(llvm::dbgs() << clif_ast.DebugString());
  *modified_clif_ast = clif_ast;
  if (RunCompiler(builder_.BuildCode(modified_clif_ast),
                  compiler_args,
                  input_file_name) == false) {
    return false;
  }
  BuildTypeTable();
  modified_clif_ast->set_catch_exceptions(
      ast_->GetASTContext().getLangOpts().Exceptions);
  return MatchAndSetAST(modified_clif_ast);
}

bool ClifMatcher::RunCompiler(const std::string& code,
                              const std::vector<std::string>& args,
                              const std::string& input_file_name) {
  ast_.reset(new TranslationUnitAST);
  return ast_->Init(code, args, input_file_name);
}

bool ClifMatcher::CheckConstant(QualType type) const {
  if (!type.isConstQualified()) {
    ClifError error(*this, kConstVarError);
    error.Report(CurrentDecl());
    return false;
  }
  return true;
}

std::string ClifMatcher::GetQualTypeClifName(QualType qual_type) const {
  if (qual_type.getTypePtrOrNull() == nullptr) {
    return "";
  }
  std::string name = clang::TypeName::getFullyQualifiedName(
      qual_type, ast_->GetASTContext(), true /* Include "::" prefix */);

  // Clang desugars template parameters in unpredictable places, and
  // often in unpredictable ways. Strings are such a common case that
  // we special case them, which avoids that uglyness for the
  // users.
    if ((name == "::std::basic_string<char, char_traits<char>, allocator<char> >") ||  // NOLINT linelength
      (name == "::std::basic_string<char, ::std::char_traits<char>, ::std::allocator<char> >")) {  // NOLINT linelength
    name = "::std::string";
  }
  return name;
}

bool ClifMatcher::MatchAndSetAST(AST* clif_ast) {
  assert(ast_ != nullptr && "RunCompiler must be called prior to this.");
  int num_unmatched = MatchAndSetDecls(clif_ast->mutable_decls());
  DEBUG(llvm::dbgs() << "Matched proto:\n" << clif_ast->DebugString());
  return num_unmatched == 0;
}

int ClifMatcher::MatchAndSetDecls(DeclList* decls) {
  int num_unmatched = 0;
  for (auto& decl : *decls) {
    if (!MatchAndSetOneDecl(&decl)) {
      ++num_unmatched;
    }
  }
  return num_unmatched;
}

bool ClifMatcher::MatchAndSetOneDecl(Decl* clif_decl) {
  bool matched = false;
  decl_stack_.push_back(clif_decl);
  switch (clif_decl->decltype_()) {
    case Decl::CLASS:
      matched = MatchAndSetClass(clif_decl->mutable_class_());
      break;
    case Decl::ENUM:
      matched = MatchAndSetEnum(clif_decl->mutable_enum_());
      break;
    case Decl::VAR:
      matched = MatchAndSetVar(clif_decl->mutable_var());
      break;
    case Decl::CONST:
      matched = MatchAndSetConst(clif_decl->mutable_const_());
      break;
    case Decl::FUNC:
      matched = MatchAndSetFunc(clif_decl->mutable_func());
      break;
    case Decl::TYPE:
      matched = MatchAndSetClassName(clif_decl->mutable_fdecl());
      break;
    case Decl::UNKNOWN:
      matched = kTypeMismatch;
      break;
  }
  decl_stack_.pop_back();
  return matched;
}

bool ClifMatcher::ImportedFromCorrectFile(const NamedDecl& named_decl,
                                          ClifError* error) const {
  // TODO: Suffix checking is not a particularly robust
  // way of checking that we imported a declaration from a particular
  // file.  There could be many files with the given name. This is
  // less of an issue if the path in the proto is long, or even a full
  // path. We need to figure out some rules. GetSourceFile returns
  // strings of the form:
  //
  // /fully/qualified/path/to/clif/backend/test.h
  //
  // or a simlar form when not run under a test.
  const Decl& clif_decl = *CurrentDecl();
  std::string source_file = ast_->GetSourceFile(named_decl);
  if (clif_decl.has_cpp_file() &&
      clif_decl.cpp_file() != "" &&
      !llvm::StringRef(source_file).endswith(clif_decl.cpp_file().c_str())) {
    error->SetCode(kNotInImportFile);
    std::string message;
    StrAppend(&message,
              "Clif expects it in the file ",
              clif_decl.cpp_file(),
              " but found it at ",
              ast_->GetClangDeclLocForError(named_decl));
    error->AddMessage(message);
    return false;
  }
  return true;
}

template<class ClangDeclType>
ClangDeclType* ClifMatcher::TypecheckLookupResult(
    clang::NamedDecl* named_decl,
    const std::string& clif_identifier,
    const std::string& clif_type) const {
  ClangDeclType* decl = CheckDeclType<ClangDeclType>(named_decl);
  if (decl == nullptr) {
    ReportTypecheckError<ClangDeclType>(named_decl, clif_identifier, clif_type);
  }
  return decl;
}

template<class ClangDeclType>
ClangDeclType* ClifMatcher::CheckDeclType(clang::NamedDecl* named_decl) const {
  // Find the underlying type.
  if (clang::isa<clang::TypedefNameDecl>(named_decl)) {
    auto typedefname = static_cast<const clang::TypedefNameDecl*>(named_decl);
    QualType type = typedefname->getUnderlyingType();
    // We don't care if the type is incomplete, but this function also
    // finds the named decl which was typedeffed from, which we do
    // care about.
    type.getTypePtr()->isIncompleteType(&named_decl);
  }
  if (!clang::isa<ClangDeclType>(named_decl)) {
    return nullptr;
  }
  return static_cast<ClangDeclType*>(named_decl);
}

template<class ClangDeclType>
void ClifMatcher::ReportTypecheckError(
    clang::NamedDecl* named_decl,
    const std::string& clif_identifier,
    const std::string& clif_type) const {
  std::string message;
  StrAppend(&message,
            "Type mismatch: Clif declares ", clif_identifier,
            " as ", clif_type, " but its name matched \"",
            named_decl->getQualifiedNameAsString(),
            "\" which is a ", named_decl->getDeclKindName());
  ClifError error(*this, kTypeMismatch, message);
  error.AddClangDeclAndLocation(ast_.get(), named_decl);
  error.Report(CurrentDecl());
}

// Type-promotion often causes unexpected behavior on the
// source-language side, so clif forbid many kinds. Generally,
// promotion within a category is OK (short int to long int).  We
// don't want to use the Sema functions (isXXX[Promotion|Conversion])
// here because we are evaluating the promotions as if the from_type
// was a clif type, rather than an allowable C++ standard promotion.
bool ClifMatcher::IsValidClifTypePromotion(
    QualType from_type,
    QualType to_type) const {
  // Can't use "!to_type->isXXXXType()" here because record types such
  // as StatusOr may have appropriate conversions.

  // Forbid pointer type promotion. (With the caveat that arrays work
  // like pointers for the purposes of this calculation.)
  if (from_type->isPointerType() &&
      !to_type->isPointerType() && !to_type->isArrayType()) {
    return false;
  }
  if (from_type->isReferenceType()) {
     from_type = from_type.getNonReferenceType();
  }
  if (to_type->isReferenceType()) {
    to_type = to_type.getNonReferenceType();
  }

  // Forbid boolean conversions of any sort. Fun fact: C++ considers
  // bool an integer type.  Allow RecordTypes because implicit
  // conversions via constructors are OK, and a user can forbid such
  // conversions by using the "explicit" keyword, if one a conversion
  // causes them a problem.
  if ((from_type->isBooleanType() &&
       !to_type->isBooleanType() &&
       !to_type->isRecordType()) ||
      (to_type->isBooleanType() &&
       !from_type->isBooleanType() &&
       !from_type->isRecordType())) {
    return false;
  }

  // Char to integer is OK.

  // Forbid integer conversions.
  if ((from_type->isIntegerType() && (to_type->isFloatingType() ||
                                      to_type->isComplexType())) ||
      (to_type->isIntegerType() && (from_type->isFloatingType() ||
                                    from_type->isComplexType()))) {
    return false;
  }

  // Forbid float conversions.
  if ((from_type->isFloatingType() && to_type->isComplexType()) ||
      (to_type->isFloatingType() && from_type->isComplexType())) {
    return false;
  }

  // Everything else will be caught by AreAssignableTypes.
  return true;
}

bool ClifMatcher::AreAssignableTypes(const QualType from_type,
                                     const clang::SourceLocation& loc,
                                     const QualType to_type) const {
  assert((from_type.getTypePtrOrNull() != nullptr) && "Invalid type from Clif");
  assert((to_type.getTypePtrOrNull() != nullptr) && "Invalid type from C++");

  if (!IsValidClifTypePromotion(from_type, to_type)) {
    return false;
  }

  // An erroneous declaration can leave the Sema in an inconsistent
  // state, so push a context that says that no code will be generated
  // from this expression. This just makes it safer, not completely
  // safe. Also, carefully call functions that check if something is
  // possible, rather than actually generating the ast which does
  // it. These are typically the "CanXXXX" version of a function
  // instead of the "XXXX" version.

  // Object's destructor exits the context.
  clang::EnterExpressionEvaluationContext context(ast_->GetSema(),
      clang::Sema::ExpressionEvaluationContext::Unevaluated);

  InitializedEntity entity =
      InitializedEntity::InitializeResult(
          loc, to_type, false);  // NRVO is irrelevant.
  clang::OpaqueValueExpr init_expr(loc, from_type.getNonReferenceType(),
                                   clang::ExprValueKind::VK_LValue);
  return ast_->GetSema().CanPerformCopyInitialization(entity, &init_expr);
}

bool ClifMatcher::MatchAndSetClassName(ForwardDecl* forward_decl) const {
  auto clif_qual_type = clif_qual_types_.find(forward_decl->name().cpp_name());
  assert(clif_qual_type != clif_qual_types_.end());
  forward_decl->mutable_name()->set_cpp_name(
      clang::TypeName::getFullyQualifiedName(
          clif_qual_type->second.qual_type,
          ast_->GetASTContext(),
          true /* Include "::" prefix */));
  // We always set these to true for classes and capsules.
  ast_->AddPtrConversionType(clif_qual_type->second.qual_type);
  ast_->AddUniquePtrConversionType(clif_qual_type->second.qual_type);
  return true;
}

bool ClifMatcher::CalculateBaseClasses(const CXXRecordDecl* clang_decl,
                                       ClassDecl* clif_decl) const {
  if (clang_decl->hasDefinition()) {
    clang_decl = clang_decl->getDefinition();
  } else {
    if (llvm::isa<ClassTemplateSpecializationDecl>(clang_decl)) {
      return true;
    }
    ClifError error(*this, kNoDefinitionAvailable);
    error.Report(CurrentDecl());
    return false;
  }
  // This loop will eventually run out of base classes, or error.
  while (clang_decl->getNumBases() > 0) {
    // The proto fields "bases" and "cpp_bases" are separate for
    // historical reasons.
    for (auto base : clang_decl->bases()) {
      QualType base_type = base.getType();
      clif_decl->add_bases()->set_cpp_name(GetQualTypeClifName(base_type));
      ClassDecl::Base* cpp_base = clif_decl->add_cpp_bases();
      cpp_base->set_name(GetQualTypeClifName(base_type));
      clang_decl = base_type->getAsCXXRecordDecl();
      cpp_base->set_filename(ast_->GetSourceFile(*clang_decl));
      if (auto* context = clang_decl->getEnclosingNamespaceContext()) {
        if (auto* namespace_decl = llvm::dyn_cast<NamespaceDecl>(context)) {
          cpp_base->set_namespace_(namespace_decl->getNameAsString());
        }
      }
    }
  }
  return true;
}

bool ClifMatcher::MatchAndSetClass(ClassDecl* class_decl) {
  const ClifQualTypes::iterator clif_type =
      clif_qual_types_.find(class_decl->name().cpp_name());
  if (clif_type == clif_qual_types_.end()) {
    CheckForLookupError(ClifLookupResult());
    return false;
  }
  auto* record_decl = clif_type->second.qual_type->getAsCXXRecordDecl();
  std::string record_name = record_decl->getNameAsString();
  // We always set these to true for classes and capsules. Also, do
  // this before matching members, so that it is present as a
  // conversion type.
  ast_->AddPtrConversionType(clif_type->second.qual_type);
  ast_->AddUniquePtrConversionType(clif_type->second.qual_type);
  SetTypeProperties<ClassDecl>(clif_type->second.qual_type, class_decl);

  ast_->PushLookupContext(record_decl);
  int num_unmatched = 0;
  for (auto& decl : *class_decl->mutable_members()) {
    // Constructors are special-cased throughout clang, can't be
    // looked up normally, so handle them specially.
    if (decl.decltype_() == Decl::FUNC && decl.func().constructor()) {
      if (!MatchAndSetConstructor(record_decl,
                                  clif_type->second.loc,
                                  decl.mutable_func())) {
        num_unmatched++;
      }
    } else if (!MatchAndSetOneDecl(&decl)) {
      num_unmatched++;
    }
  }
  ast_->PopLookupContext();
  if (CalculateBaseClasses(record_decl, class_decl) != true) {
    return false;
  }

  // Use the qualtype to retrieve the name instead of the decl,
  // because that contains template parameters and fully qualified
  // subtypes.
  class_decl->mutable_name()->set_cpp_name(
      GetQualTypeClifName(
          clif_type->second.qual_type.getSingleStepDesugaredType(
              ast_->GetASTContext())));
  return num_unmatched == 0;
}

bool ClifMatcher::MatchAndSetEnum(EnumDecl* enum_decl) {
  auto clif_qual_type = clif_qual_types_.find(enum_decl->name().cpp_name());
  assert(clif_qual_type != clif_qual_types_.end());
  QualType clif_type = clif_qual_type->second.qual_type;
  auto clif_decl = clif_type->getAsTagDecl();
  if (clif_decl == nullptr) {
    return false;
  }
  auto clang_decl = TypecheckLookupResult<clang::EnumDecl>(
      clif_decl, enum_decl->name().native(), kEnumNameForError);
  if (clang_decl == nullptr) {
    return false;
  }
  enum_decl->mutable_name()->set_cpp_name(GetGloballyQualifiedName(clang_decl));
  enum_decl->set_enum_class(clang_decl->isScoped());

  std::unordered_map<std::string, protos::Name*> clif_enumerators;
  for (int i = 0; i < enum_decl->members().size(); ++i) {
    protos::Name* name = enum_decl->mutable_members(i);
    // The supplied cpp_name may or may not be qualified.
    // Canonicalize it to the unqualified name for comparisons.
    NamespaceVector components(name->cpp_name());
    if (!components.empty()) {
      const std::string& unqualified_enum_name = components.back().str();
      clif_enumerators[unqualified_enum_name] = name;
    }
  }
  std::unordered_map<std::string, NamedDecl*> clang_enumerators;
  for (const auto& clang_enumerator : clang_decl->enumerators()) {
    clang_enumerators[clang_enumerator->getNameAsString()] = clang_enumerator;
    DEBUG(llvm::dbgs()
          << "Clang enumerator : " << clang_enumerator->getNameAsString());
  }
  std::vector<std::string> extras;
  for (auto enumerator : clif_enumerators) {
    if (clang_enumerators.find(enumerator.first) == clang_enumerators.end()) {
      extras.emplace_back(enumerator.first);
    }
  }
  if (!extras.empty()) {
    std::string error;
    StrAppend(&error,
              "Extra enumerators in Clif enum declaration ",
              enum_decl->name().native(), ".  C++ Enumerator ",
              clang_decl->getQualifiedNameAsString(),
              " does not contain enumerator(s):");
    for (const std::string& extra : extras) {
      StrAppend(&error, " ", extra);
    }
    return false;
  }
  // Ensure that all the decls get fully qualified names. Extra C++
  // enumerators are just added to the proto.
  for (const auto& enumerator : clang_enumerators) {
    protos::Name* clif_name;
    auto clif_enumerator = clif_enumerators.find(enumerator.first);
    if (clif_enumerator != clif_enumerators.end()) {
      clif_name = clif_enumerator->second;
    } else {
      clif_name = enum_decl->add_members();
    }
    // The decl will be found, because we created the data structure
    // with this same method.
    auto result = ast_->LookupScopedSymbolInContext(clang_decl,
                                                    enumerator.first);
    clif_name->set_cpp_name(
        GetGloballyQualifiedName(result.GetFirst()));
    if (!clif_name->has_native()) {
      clif_name->set_native(result.GetFirst()->getNameAsString());
    }
  }
  DEBUG(llvm::dbgs() << enum_decl->DebugString());
  return true;
}


ClifErrorCode ClifMatcher::HandleEnumConstant(
    bool check_constant,
    EnumConstantDecl* enum_decl,
    protos::Name* name,
    protos::Type* type) {
  auto clif_qual_type = clif_qual_types_.find(type->cpp_type());
  assert(clif_qual_type != clif_qual_types_.end());
  name->set_cpp_name(GetGloballyQualifiedName(enum_decl));
  SetCppTypeName(clang::TypeName::getFullyQualifiedName(
      clif_qual_type->second.qual_type, ast_->GetASTContext(), true), type);
  return kOK;
}

ClifErrorCode ClifMatcher::MatchAndSetVarHelper(bool check_constant,
                                                protos::Name* name,
                                                protos::Type* type) {
  auto decls = ast_->ClifLookup(name->cpp_name());
  if (CheckForLookupError(decls) != kOK) {
    return kNotFound;
  }
  auto named_decl = decls.GetFirst();
  std::string error;
  // Enum literals require special handling because they don't
  // have an associated var decl.
  if (clang::isa<clang::EnumConstantDecl>(named_decl)) {
    return HandleEnumConstant(
        check_constant,
        static_cast<clang::EnumConstantDecl*>(named_decl),
        name, type);
  }
  // Is it a Class member field? Can't use TypecheckLookupResult here
  // because it could also be a VarDecl.
  QualType qual_type;
  if (clang::isa<clang::FieldDecl>(named_decl)) {
    qual_type = static_cast<clang::FieldDecl*>(named_decl)->getType();
  } else {
    // Didn't appear as a Class member field. It might be a non-class
    // member variable.
    auto clang_var_decl = TypecheckLookupResult<clang::VarDecl>(
        decls.GetFirst(), name->native(),
        check_constant ? kConstNameForError : kVariableNameForError);
    if (clang_var_decl == nullptr) {
      return kTypeMismatch;
    }
    qual_type = clang_var_decl->getType();
  }
  ClifErrorCode code = MatchAndSetTypeTop(qual_type, type);
  if (code != kOK) {
    ClifError error(*this, code);
    error.AddMessage(GetParallelTypeNames());
    error.Report(CurrentDecl());
    return code;
  }
  if (check_constant && !CheckConstant(qual_type)) {
    ClifError error(*this, kConstVarError);
    error.AddMessage(GetParallelTypeNames());
    error.Report(CurrentDecl());
    return kConstVarError;
  }
  if (check_constant) {
    name->set_cpp_name(GetGloballyQualifiedName(named_decl));
    std::string type_name = GetQualTypeClifName(qual_type);
    if (type_name.substr(0, sizeof(kCppCharArray) - 1) == kCppCharArray) {
      SetCppTypeName(kClifCharArray, type);
    } else {
      SetCppTypeName(GetQualTypeClifName(qual_type.getUnqualifiedType()), type);
    }
  } else {
    // Clif doesn't want fully qualified names for variables inside
    // classes, and doesn't allow variables outside of classes.
    name->set_cpp_name(named_decl->getNameAsString());
    SetCppTypeName(GetQualTypeClifName(qual_type.getUnqualifiedType()), type);
  }
  return kOK;
}

bool ClifMatcher::MatchAndSetVar(VarDecl* var_decl) {
  const bool has_cpp_get = !var_decl->cpp_get().name().cpp_name().empty();
  const bool has_cpp_set = !var_decl->cpp_set().name().cpp_name().empty();

  bool get_match;
  // VarDecls with getters and setters allow us to ignore cpp_name;
  // the "Var" is really a clif-level convenience.
  if (has_cpp_get) {
    get_match = MatchAndSetFunc(var_decl->mutable_cpp_get());
  } else {
    get_match = true;
  }
  bool set_match;
  if (has_cpp_set) {
    set_match = MatchAndSetFunc(var_decl->mutable_cpp_set());
  } else {
    set_match = true;
  }

  // But if it is missing both, then we need to ensure that it
  // actually exists.
  if (!has_cpp_get && !has_cpp_set) {
    ClifErrorCode code = MatchAndSetVarHelper(false,  // Don't check constant.
                                              var_decl->mutable_name(),
                                              var_decl->mutable_type());
    if (code != kOK) {
      // Error was reported by MatchAndSetVarHelper.
      return false;
    }
    return true;
  }
  if (get_match && set_match) {
    return true;
  }
  ClifError error(*this, kConstVarError);
  error.Report(CurrentDecl());
  return false;
}

bool ClifMatcher::MatchAndSetConst(ConstDecl* const_decl) {
  ClifErrorCode code = MatchAndSetVarHelper(true,  // Check if it is constant.
                                            const_decl->mutable_name(),
                                            const_decl->mutable_type());
  return code == kOK;
}

ClifErrorCode ClifMatcher::MatchAndSetCallable(const QualType& callable_type,
                                               FuncDecl* callable) {
  if (ast_->GetStdTemplateDecl("function") ==
      ast_->GetQualTypeTemplateDecl(callable_type)) {
    QualType func_type = ast_->GetTemplateArgType(callable_type);
    std::string message;
    // -1 means all args are non-default. TODO: add default
    // -args support.
    ClifErrorCode code = MatchAndSetSignatures(
        func_type->getAs<clang::FunctionProtoType>(), -1, callable, &message);
    if (code == kOK) {
      return kOK;
    }
    type_mismatch_stack_.emplace_back(
        std::make_pair(GetQualTypeClifName(callable_type), message));
    return code;
  }
  type_mismatch_stack_.emplace_back(
      std::make_pair(GetQualTypeClifName(callable_type),
                     GetErrorCodeString(kNotCallable)));
  return kNotCallable;
}

template<class T>
void ClifMatcher::SetTypeProperties(QualType clang_type,
                                    T* clif_decl) const {
  if (clang_type->isPointerType() || clang_type->isReferenceType()) {
    clang_type = clang_type->getPointeeType();
  }

  if (auto* clang_decl = clang_type->getAsCXXRecordDecl()) {
    if (clang_decl->hasDefinition()) {
      // Save some noise in the protobufs by leaving these empty when
      // we could set them to false. Makes the code here a little more
      // complicated, but the protobuf way easier to debug.  Also,
      // note the subtlety: This doesn't answer just if the class has
      // a default constructor, but also if it is public.

      if (!ast_->HasDefaultConstructor(clang_decl) ||
          !ast_->DestructorIsAccessible(clang_decl)) {
        // The real question we are answering here is, "Can we default
        // construct and destruct classes of this type?"
        clif_decl->set_cpp_has_def_ctor(false);
      }
      if (!ast_->DestructorIsAccessible(clang_decl)) {
        clif_decl->set_cpp_has_public_dtor(false);
      }
      if (!ast_->IsClifCopyable(clang_decl) ||
          !ast_->DestructorIsAccessible(clang_decl)) {
        clif_decl->set_cpp_copyable(false);
      }
      if (clang_decl->isAbstract()) {
        clif_decl->set_cpp_abstract(true);
      }
    } else {
      // From clif's perspective, if we have no definition for the
      // class (maybe it was forward declared), it may as well be
      // abstract.
      clif_decl->set_cpp_abstract(true);
    }
  }
}

ClifErrorCode ClifMatcher::MatchAndSetContainer(
    const QualType& clang_type,
    protos::Type* composed,
    unsigned int flags) {
  QualType reffed_type = clang_type;
  // The actual C++ type could be a pointer.
  bool original_is_ptr_type = false;
  if (reffed_type->isPointerType()) {
    original_is_ptr_type = true;
    reffed_type = reffed_type->getPointeeType().getUnqualifiedType();
  }
  const clang::TemplateArgument* clang_args;
  int num_clang_args;
  clang::Decl* canonical;
  if (const auto* record =
      reffed_type.getNonLValueExprType(
          ast_->GetASTContext())->getAs<clang::RecordType>()) {
    if (auto special =
        llvm::dyn_cast<const ClassTemplateSpecializationDecl>(
            record->getDecl())) {
      clang_args = special->getTemplateArgs().data();
      num_clang_args = special->getTemplateArgs().size();
      canonical = special->getSpecializedTemplate()->getCanonicalDecl();
    } else {
      RecordIncompatibleTypes(reffed_type, *composed);
      return kIncompatibleTypes;
    }
  } else {
    if (auto special =
        reffed_type->getAs<clang::TemplateSpecializationType>()) {
      clang_args = special->getArgs();
      num_clang_args = special->getNumArgs();
      canonical =
          special->getTemplateName().getAsTemplateDecl()->getCanonicalDecl();
    } else {
      RecordIncompatibleTypes(reffed_type, *composed);
      return kIncompatibleTypes;
    }
  }
  // If this isn't a template, then it can't match a composed type.
  if (clang_args == nullptr) {
    RecordIncompatibleTypes(reffed_type, *composed);
    return kIncompatibleTypes;
  }
  // Check that the container itself is compatible.
  auto clif_qual_type = clif_qual_types_.find(composed->cpp_type());
  assert(clif_qual_type != clif_qual_types_.end());
  auto clif_decl = clif_qual_type->second.qual_type->getAsCXXRecordDecl();
  if (clif_decl == nullptr) {
    return kIncompatibleTypes;
  }
  auto clang_decl = TypecheckLookupResult<ClassTemplateSpecializationDecl>(
      clif_decl, composed->lang_type(), kTemplateNameForError);
  if (clang_decl == nullptr ||
      clang_decl->getSpecializedTemplate()->getCanonicalDecl() != canonical) {
    RecordIncompatibleTypes(reffed_type, *composed);
    return kIncompatibleTypes;
  }

  int cur_arg = 0;
  int mismatches = 0;
  while (cur_arg < composed->params_size() && cur_arg < num_clang_args) {
    switch (clang_args[cur_arg].getKind()) {
      case clang::TemplateArgument::Type:
        if (MatchAndSetType(clang_args[cur_arg].getAsType(),
                            composed->mutable_params(cur_arg)) != kOK)  {
          ++mismatches;
        }
        ++cur_arg;
        break;
      case clang::TemplateArgument::Pack:
        {
          // If a template argument is of Pack kind, then the items in the
          // pack are guaranteed to be type arguments.
          num_clang_args += clang_args[cur_arg].pack_size() - 1;
          auto iter = clang_args[cur_arg].pack_begin();
          auto iter_end = clang_args[cur_arg].pack_end();
          for (;
               iter != iter_end && cur_arg < composed->params_size();
               ++iter) {
            if (MatchAndSetType(iter->getAsType(),
                                composed->mutable_params(cur_arg)) != kOK)  {
              ++mismatches;
            }
            ++cur_arg;
          }
        }
        break;
      default:
        RecordIncompatibleTypes(reffed_type, *composed);
        return kIncompatibleTypes;
    }
  }
  if (cur_arg != composed->params_size() ||
      mismatches != 0) {
    // If we exited the loop above because the clang-type doesn't have
    // enough elements, then that is an error.  TODO:
    // Handle templates with default arguments.  This would involve
    // clause like so:
    //
    // cur_arg < (num_clang_args - num_clang_default_args)
    //
    // Unfortunately, calculating the number of clang default template
    // arguments is not easy.
    RecordIncompatibleTypes(reffed_type, *composed);
    return kIncompatibleTypes;
  }
  // We stripped the pointer type from the actual C++ type if it was of a
  // pointer type. However, when reporting the type name, we need to report
  // the one of the actual C++ type.
  QualType type_to_report;
  if (original_is_ptr_type) {
    // We dropped qualifiers from |reffed_type| already if the original type
    // is a pointer type.
    if (flags & TMF_POINTEE_TYPE) {
      type_to_report = reffed_type;
    } else {
      type_to_report = ast_->GetASTContext().getPointerType(reffed_type);
    }
  } else {
    type_to_report = reffed_type.getNonReferenceType().getUnqualifiedType();
  }
  SetCppTypeName(GetQualTypeClifName(type_to_report), composed);
  return kOK;
}

ClifErrorCode ClifMatcher::MatchAndSetStdSmartPtr(
    const QualType& smart_ptr_type,
    protos::Type* clif_type,
    unsigned int flags) {
  QualType pointee_type = ast_->GetTemplateArgType(smart_ptr_type);
  std::string template_name = "";
  // If we have a smart pointer of the form std::smart_ptr<PointeeType>,
  // then we need to match PointeeType* with |clif_type|.
  // However, if PointeeType were a builtin type, we want to match it with
  // |clif_type|. This is because C++ builtin types have different flavors
  // for a single equivalent type of the wrapper language. For example,
  // it is a match if the Python type is int but the C++ type is any of {int,
  // long, short, unsigned, ...}.
  QualType type_to_match;
  if (pointee_type.getCanonicalType()->isBuiltinType()) {
    type_to_match = pointee_type;
    // The flags are effectively irrelevant for builtin types, but be explicit
    // to avoid confusion.
    flags = TMF_EXACT_TYPE;
  } else {
    auto record_decl = pointee_type->getAsCXXRecordDecl();
    if (record_decl != nullptr && (flags & TMF_DERIVED_CLASS_TYPE)) {
      if (pointee_type->isIncompleteType() || !record_decl->isDynamicClass()) {
        // We do not want to report the derived type if the actual C++ type
        // does not have a virtual destructor. This is because smart pointers
        // potentially call the object's destructor. So, if we report the
        // derived class, we want the derived class destructor to be called
        // and not the base class destructor.
        //
        // We do not also want to report the derived class type if the pointee
        // type is incomplete. This is because we cannot tell if the class is
        // dynamic or not if it is of an incomplete type. We could attempt to
        // complete the type, but such an attempt is not guaranteed to provide
        // enough information to help us determine if the type is dynamic.
        // Moreover, if such an attempt results in an error, it can
        // potentially leave the Sema in an invalid state.
        flags &= ~TMF_DERIVED_CLASS_TYPE;
      }
    }
    // We want the pointee type to be reported as we want to use its name
    // in constructing the smart pointer type name.
    flags |= TMF_POINTEE_TYPE;
    type_to_match = ast_->GetASTContext().getPointerType(pointee_type);
  }
  ClifErrorCode code = MatchAndSetType(type_to_match, clif_type, flags);
  if (code != kOK) {
    return code;
  }
  std::string type_name = GetGloballyQualifiedName(
      smart_ptr_type->getAsCXXRecordDecl());
  // |clif_type| holds the correct pointee type to report as it was
  // evaluated based on |flags|.
  StrAppend(&type_name, "<", clif_type->cpp_type(), ">");
  SetCppTypeName(type_name, clif_type);

  // Some of the fields on clif_type got set according to the
  // pointee type, but smart pointers are their own types with
  // their own properties. Fix those details up. std::unique_ptr
  // and std::shared_ptr are always copyable and constructible.
  // Only set it if necessary--this prevents protobuf noise.
  if (!clif_type->cpp_copyable()) {
    clif_type->set_cpp_copyable(true);
  }
  if (!clif_type->cpp_has_def_ctor()) {
    clif_type->set_cpp_has_def_ctor(true);
  }
  if (clif_type->cpp_raw_pointer()) {
    clif_type->set_cpp_raw_pointer(false);
  }
  if (clif_type->cpp_toptr_conversion()) {
    clif_type->set_cpp_toptr_conversion(false);
  }
  return kOK;
}

// Helper function that returns a type as described by
// flags. Sometimes this resultant type is based on the clang_type,
// sometimes on the clif_qual_type. This function only makes sense if
// clang_type and clif_qual_type are assignable.

QualType ClifMatcher::HandleTypeMatchFlags(
    const clang::QualType& clang_type,
    const clang::QualType& clif_qual_type,
    unsigned int flags) {
  // If the declared type is a base class of the clif type, then we should set
  // the cpp_type to the clif type.
  QualType clang_pointee_type = clang_type;
  QualType clif_pointee_type = clif_qual_type;
  if (clang_type->isPointerType()) {
    clang_pointee_type = clang_type->getPointeeType();
    clif_pointee_type = clif_qual_type->getPointeeType();
  }
  if (clang_type->isReferenceType()) {
    clang_pointee_type = clang_type->getPointeeType();
  }
  QualType type_to_report = flags & TMF_POINTEE_TYPE ?
      clang_pointee_type : clang_type;
  if (flags & TMF_DERIVED_CLASS_TYPE) {
    if (ClifTypeDerivedFromClangType(clang_pointee_type, clif_pointee_type)) {
      type_to_report = flags & TMF_POINTEE_TYPE ?
          clif_pointee_type : clif_qual_type;
    }
  }
  if (type_to_report->isReferenceType()) {
    type_to_report = flags & TMF_UNCONVERTED_REF_TYPE ?
        clif_qual_type : type_to_report->getPointeeType();
  }
  if (flags & TMF_REMOVE_CONST_POINTER_TYPE) {
    bool pointer_type = false;
    if (type_to_report->isPointerType()) {
      pointer_type = true;
      type_to_report = type_to_report->getPointeeType();
    }
    // Discard const, volatile, and restrict.
    type_to_report = type_to_report.getNonReferenceType().getUnqualifiedType();
    if (pointer_type) {
      type_to_report = ast_->GetASTContext().getPointerType(type_to_report);
    }
  }
  return type_to_report.getUnqualifiedType();
}

// Set up error handling and stack checking to match a type.
// MatchAndSetType calls itself recursively, but we want this setup to
// happen exactly once per type matching construct.  Also, we don't
// want to pop matching type-names off the stack until we are sure
// there are no errors. Otherwise, a mismatch like foo<string, string,
// string, int> vs map<string, string, int, string> will hide wich
// string.
ClifErrorCode ClifMatcher::MatchAndSetTypeTop(const QualType& clang_type,
                                              Type* clif_type,
                                              unsigned int flags) {
  type_mismatch_stack_.clear();
  return MatchAndSetType(clang_type, clif_type, flags);
}

// Summary of the rules for matching types. Match by the following
// rules:
//
// |-Case-|-----------Input--------------------|-Result-|
//         cpp_type cpp_raw_pointer header.h     Match?
//     1.  Foo      true            void f(Foo)  No
//     2.  Foo      true            void f(Foo*) Yes
//     3.  Foo*     true            void f(Foo*) Yes
//     4.  Foo*     true            void f(Foo)  No
//
//     5.  Foo      false           void f(Foo)  Yes
//     6.  Foo      false           void f(Foo*) Yes (+ set raw=true)
//     7.  Foo*     false           void f(Foo)  No
//     8.  Foo*     false           void f(Foo*) Yes (+ set raw=true)
//
//    Foo& works exactly like "Foo".
ClifErrorCode ClifMatcher::MatchAndSetType(const QualType& clang_type,
                                           Type* clif_type,
                                           unsigned int flags) {
  if (ast_->IsStdSmartPtr(clang_type)) {
    return MatchAndSetStdSmartPtr(clang_type, clif_type, flags);
  }
  if (clif_type->params_size() > 0) {
    return MatchAndSetContainer(clang_type, clif_type, flags);
  }
  if (clif_type->has_callable()) {
    return MatchAndSetCallable(clang_type, clif_type->mutable_callable());
  }
  if (clif_type->cpp_raw_pointer() && !clang_type->isPointerType()) {
    // Cases 1 and 4, but weak error message due to skipping any real
    // type matching. That is, even if they fix the pointer problem,
    // they may immediately run into another one of the error cases.
    RecordIncompatibleTypes(clang_type, *clif_type);
    return kNonPointerType;
  }
  assert((clif_qual_types_.find(clif_type->cpp_type()) !=
         clif_qual_types_.end()));
  const ClifQualTypeDecl& clif_cpp_decl = clif_qual_types_.find(
      clif_type->cpp_type())->second;

  // Desugar to use what the user wrote, rather than clif_type_0.
  QualType clif_qual_type =
      clif_cpp_decl.qual_type.getSingleStepDesugaredType(ast_->GetASTContext());
  std::string clif_type_name = GetQualTypeClifName(clif_qual_type);
  std::string clang_type_name = GetQualTypeClifName(clang_type);

  if (clif_type->cpp_raw_pointer() && !clif_qual_type->isPointerType()) {
    clif_qual_type = ast_->GetASTContext().getPointerType(clif_qual_type);
  }
  if (AreAssignableTypes(clif_qual_type,
                         clif_cpp_decl.loc, clang_type)) {
    // Cases 3, 5, and 8.
    SetUnqualifiedCppType(
        HandleTypeMatchFlags(clang_type, clif_qual_type, flags),
        clif_type);
    return kOK;
  }

  if (clang_type->isArrayType() &&
      AreAssignableTypes(clang_type, clif_cpp_decl.loc, clif_qual_type)) {
    // Arrays are tricky: In C++, when a variable or constant's type is
    // "array of type X" we need Clif to declare a pointer to type X,
    // not an array of type X. See below for why:
    //
    // Compilable, what most source code looks like.
    // const char array[] = "x";
    //
    // Invalid initializer, (must be literals)
    // const char invalid_init[2] = array;
    //
    // Compilable, but not what Clif needs in this case because the
    // type isn't an array type.
    // const char* pointer = "x";
    //
    // Compilable, what we need for Clif
    // const char* pointer = array;
    //
    // for this scenario, we simply swap the clif type with
    // the clang type and try again:
    //
    // Original:
    // clang_type = const char[];
    // clif_qual_type = cont char*;
    //
    // Invalid, but what clif normally checks:
    // clang_type = clif_type;
    //
    // Valid:
    // clif_qual_type = clang_type;
    SetUnqualifiedCppType(clang_type, clif_type);
    return kOK;
  }
  if (clang_type->isPointerType()) {
    // The compare of these two types failed, but try again with a
    // pointer to the clif type. (eg type "foo" can't be assigned to
    // "foo *", but "&foo" can. That is easy for the code generator to
    // do.
    QualType clif_ptr_type = ast_->GetSema().BuildPointerType(
        clif_qual_type, clif_cpp_decl.loc, DeclarationName());
    if (AreAssignableTypes(clif_ptr_type,
                           clif_cpp_decl.loc, clang_type)) {
      // Cases 2 and 6.
      SetUnqualifiedCppType(
          HandleTypeMatchFlags(clang_type, clif_ptr_type, flags),
          clif_type);
      return kOK;
    }
  }
  // Try again without const and ref.
  QualType retry_type
      = clif_qual_type.getNonReferenceType().getUnqualifiedType();
  if (retry_type != clif_qual_type) {
    if (AreAssignableTypes(retry_type,
                           clif_cpp_decl.loc, clang_type)) {
      SetUnqualifiedCppType(clang_type, clif_type);
      return kOK;
    }
  }
  // Case 7
  RecordIncompatibleTypes(clang_type, *clif_type);
  return kIncompatibleTypes;
}

ClifErrorCode ClifMatcher::RecordIncompatibleTypes(
    const QualType& clang_type,
    const Type& clif_type) {
  auto& original_names_map = builder_.OriginalNames();
  auto original_cpp_type = original_names_map.find(clif_type.cpp_type());
  assert(original_cpp_type != original_names_map.end());
  type_mismatch_stack_.emplace_back(
      std::make_pair(
          GetQualTypeClifName(clang_type), original_cpp_type->second));
  return kIncompatibleTypes;
}

// Is this parameter type suitable for an output parameter in Clif?
ClifErrorCode ClifMatcher::MatchAndSetOutputParamType(
    const QualType& clang_type,
    Type* clif_type) {
  if (!clang_type->isPointerType() && !clang_type->isReferenceType()) {
    // A type that doesn't point to anything can't have writes escape
    // back to the caller.
    return kNonPointerReturnType;
  }
  // getPointeeType works for both references and pointers.
  QualType reffed_type = clang_type->getPointeeType();
  // A const-qualified type can't be written to at all.
  if (reffed_type.isConstQualified()) {
    return kConstReturnType;
  }
  while (auto *td_type = reffed_type->getAs<clang::TypedefType>()) {
    reffed_type = td_type->desugar();
  }
  return MatchAndSetTypeTop(reffed_type, clif_type);
}

void ClifMatcher::SetUnqualifiedCppType(const QualType& clang_type,
                                        Type* clif_type) {
  SetTypeProperties<Type>(clang_type, clif_type);
  SetCppTypeName(GetQualTypeClifName(clang_type), clif_type);
  if (clang_type->isPointerType()) {
    clif_type->set_cpp_raw_pointer(true);
  }
  if (ast_->IsKnownPtrConversionType(clang_type)) {
    clif_type->set_cpp_toptr_conversion(true);
    DEBUG(llvm::dbgs()
          << "Used ptr conversion for " << clang_type.getAsString());
  }
  if (ast_->IsKnownUniquePtrConversionType(clang_type)) {
    clif_type->set_cpp_touniqptr_conversion(true);
    DEBUG(llvm::dbgs()
          << "Used unique_ptr conversion for " << clang_type.getAsString());
  }
}

// Is this type suitable for passing as a parameter to clif?
ClifErrorCode ClifMatcher::MatchAndSetInputParamType(QualType clang_type,
                                                     Type* clif_type) {
  return MatchAndSetTypeTop(clang_type,
                            clif_type,
                            TMF_DERIVED_CLASS_TYPE |
                            TMF_UNCONVERTED_REF_TYPE |
                            TMF_REMOVE_CONST_POINTER_TYPE);
}

// Return value expressions are special: Consider a movable but not
// copyable class:
//
// MNC x;
// MNC y = x; // Error--calls copy constructor
// MNC z = Factory(); // OK: Uses either the move or copy constructor.
//
// MatchAndSetType checks the y = x case, not the z = Factory case.
//
// Check that case now. We still need the call to MatchAndSetTypeTop
// because the move-constructor case doesn't deal with various
// not-exactly-equal-type cases.

ClifErrorCode ClifMatcher::MatchAndSetReturnType(const QualType& clang_ret,
                                                 Type* clif_type_proto) {
  if (MatchAndSetTypeTop(clang_ret, clif_type_proto) == kOK) {
    return kOK;
  }
  auto* ret_decl = clang_ret->getAsCXXRecordDecl();
  const ClifQualTypes::iterator clif_type =
      clif_qual_types_.find(clif_type_proto->cpp_type());
  // If all of the below are true, we can use move construction
  // for the return value:
  //
  // A) This type is a fully-defined, movable CXXRecord
  // B) The Clif type was found
  // C) The canonical unqualified types are identical.
  if (ret_decl && ret_decl->hasDefinition() && ast_->IsCppMovable(ret_decl) &&
      clif_type != clif_qual_types_.end()) {
    QualType clif_ret = clif_type->second.qual_type;
    if (clif_ret.getCanonicalType().getUnqualifiedType() ==
        clang_ret.getCanonicalType().getUnqualifiedType()) {
      return kOK;
    }
  }
  return kReturnValueMismatch;
}


ClifErrorCode ClifMatcher::MatchAndSetReturnValue(
    const clang::FunctionProtoType* clang_type,
    FuncDecl* func_decl,
    bool* consumed_return_value,
    std::string* message) {
  const QualType& clang_ret = clang_type->getReturnType();
  assert(!clang_ret->isDependentType());

  const bool cpp_returns_a_value = !clang_ret->isVoidType();
  if (!cpp_returns_a_value) {
    func_decl->set_cpp_void_return(true);
  }

  *consumed_return_value = false;
  if (cpp_returns_a_value) {
    protos::ParamDecl* return_param = nullptr;

    if (func_decl->returns().empty()) {
      // TODO: return error if C++ has MUST_USE_RESULT annotation.

      if (!func_decl->ignore_return_value()) {
        StrAppend(message, "C++ declares a return value but Clif does not.");
        return kReturnValueMismatch;
      }

      return_param = func_decl->add_returns();
      return_param->mutable_type()->set_lang_type("ignored");
      SetCppTypeName(GetQualTypeClifName(clang_ret),
                     return_param->mutable_type());
    } else {
      return_param = func_decl->mutable_returns(0);
      Type* ret_type = return_param->mutable_type();
      if (MatchAndSetReturnType(clang_ret, ret_type) != kOK) {
        StrAppend(message, "C++ Return value. ",
                  GetParallelTypeNames());
        return kReturnValueMismatch;
      }
    }

    *consumed_return_value = true;
    if (return_param != nullptr) {
      return_param->set_cpp_exact_type(clang::TypeName::getFullyQualifiedName(
          clang_ret, ast_->GetASTContext(), true /* Include "::" prefix */));
    }
  }

  return kOK;
}

ClifErrorCode ClifMatcher::MatchFunctionStatic(
    const clang::FunctionDecl* clang_decl,
    const FuncDecl& func_decl) {
  bool clif_static = func_decl.classmethod();
  auto method_decl = llvm::dyn_cast<clang::CXXMethodDecl>(clang_decl);
  bool clang_static = method_decl && method_decl->isStatic();
  // If the clif source declared this function outside of the class
  // then it must be C++ static, but shouldn't have the @class
  // decorator in the source.
  if (method_decl &&
      ast_->GetCurrentLookupScope() == ast_->GetTU() &&
      method_decl->getParent() != ast_->GetCurrentLookupScope()) {
    assert(!clif_static && "Invalid @class decorator not caught by parser.");
    if (!clang_static) {
      return kNonStaticClassGlobalFunctionDecl;
    }
    return kOK;
  }
  // But if the declaration is inside the class, the languages must agree.
  if (clif_static && !clang_static) {
    return kClassMethod;
  }
  if (!clif_static && clang_static) {
    return kCppStaticMethod;
  }
  return kOK;
}

// Clif can't use what would seem to be convenient Sema functions,
// such as Sema::BuildCallToMemberFunction and similar, because it is
// asking a fundamentally different question than what those answer.
// Those functions take C++ source code and determine if it is valid.
// Clif seeks to figure out a way to build valid C++ source code.
// So, for example, if C++ has:
//
// void Foo(int*x);
//
// And the user writes:
//
// int x = 3;
// Foo(x);
// Foo(&x);
//
// A C++ compiler will simply report an error on the first call, and
// not on the second. This is insufficient for Clif, which needs to
// figure out the correct version to write, rather than just reporting
// a failure on incorrect code. Additionally, Clif requires certain
// parameter orders, such as input parameters before output
// parameters, and output parameters always writable, so it would need
// additional checks anyway.
//
// Note on the function itself:
// Clif parlance is slightly different than C++ parlance.  In
// clif function "returns" any value that it might modify. So a
// function with the prototype:
//
// int Foo(int arg0, int arg1, int* arg2);
//
// returns two values--its C++ return value and arg2.  It takes two
// parameters: arg0 and arg1. Clif requires that all inputs come
// before all outputs, and prevents matches against functions that
// allow a param to be modified.  This has the interesting property of
// preventing matches against functions with default arguments,
// although the check for that is automatic via argument matching.

ClifErrorCode ClifMatcher::MatchAndSetSignatures(
    const clang::FunctionProtoType* clang_type,
    int min_req_args,
    FuncDecl* func_decl,
    std::string* message) {
  bool consumed_return_arg = false;
  ClifErrorCode code = MatchAndSetReturnValue(clang_type,
                                              func_decl,
                                              &consumed_return_arg,
                                              message);
  if (code != kOK) {
    return code;
  }
  // Number of non-optional CLIF input params.
  int clif_nonopt_params = 0;
  // Index into clang_type's list of C++ arguments.
  int cur_arg = 0;
  // Index to the last C++ input arg
  int last_in_arg = 0;
  // Index into params' list of clif parameters.
  int cur_param = 0;
  // Various "+ 1" in the error handling below to match clang
  // one-based numbering when reporting errors.
  int cur_return = consumed_return_arg ? 1 : 0;
  if (min_req_args < 0) min_req_args = clang_type->getNumParams();
  min_req_args += cur_return;

  // Check the input parameters.
  while (cur_arg < clang_type->getNumParams() &&
         cur_param < func_decl->params_size()) {
    const QualType arg_type = clang_type->getParamType(cur_arg);
    protos::ParamDecl* cur_param_decl = func_decl->mutable_params(cur_param);
    cur_param_decl->set_cpp_exact_type(clang::TypeName::getFullyQualifiedName(
        arg_type, ast_->GetASTContext(), true /* Include "::" prefix */));
    Type* param_type = cur_param_decl->mutable_type();
    ClifErrorCode code = MatchAndSetInputParamType(arg_type, param_type);
    if (code != kOK) {
      StrAppend(message, "Parameter ", cur_param + 1, ". ",
                GetParallelTypeNames());
      return kParameterMismatch;
    }
    if (func_decl->params(cur_param).default_value().empty()) {
      ++clif_nonopt_params;
    }
    ++cur_param;
    ++cur_arg;
  }

  last_in_arg = cur_arg;

  // Check the output parameters, aka, the clif "return" values.
  while (cur_arg < clang_type->getNumParams() &&
         cur_return < func_decl->returns_size()) {
    const QualType arg_type = clang_type->getParamType(cur_arg);
    protos::ParamDecl* cur_return_decl = func_decl->mutable_returns(cur_return);
    cur_return_decl->set_cpp_exact_type(clang::TypeName::getFullyQualifiedName(
        arg_type, ast_->GetASTContext(), true /* Include "::" prefix */));
    Type* param_type = cur_return_decl->mutable_type();
    ClifErrorCode code = MatchAndSetOutputParamType(arg_type, param_type);
    if (code != kOK) {
      StrAppend(message, "Parameter ", cur_param + 1, ". ",
                GetParallelTypeNames());
      return code;
    }
    ++cur_return;
    ++cur_arg;
  }
  // Did we use up all the clif-params?
  if (last_in_arg != func_decl->params_size()) {
    StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
    StrAppend(message, " Clif declares ", func_decl->params_size(),
              " input parameters. C++ declaration has ", last_in_arg);
    return kParameterCountsDiffer;
  }
  // Did we have enough returns?
  if (cur_return != func_decl->returns_size()) {
    StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
    StrAppend(message, " Clif declares ", func_decl->returns_size(),
              " output parameters. vs C++ declaration has ", cur_return,
              " (including C++ return value).");
    return kParameterCountsDiffer;
  }
  // Did we have enough non optional arguments to actually call the function?
  min_req_args -= cur_return;
  if (clif_nonopt_params != min_req_args) {
    StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
    StrAppend(message, " Clif declares ", clif_nonopt_params, " required "
              "parameters vs. C++ declaration has ", min_req_args);
    return kParameterCountsDiffer;
  }
  return kOK;
}

bool ClifMatcher::MatchAndSetFunc(FuncDecl* func_decl) {
  // Operator overloading in C++ doesn't map well to other
  // languages--handle it separately.
  if (ast_->IsOperatorFunction(func_decl->name().cpp_name())) {
    return MatchAndSetOperator(func_decl);
  }

  // Observe that C++ overloaded functions means we can't use
  // CheckForLookupError here.
  auto clang_decls = ast_->ClifLookup(func_decl->name().cpp_name());
  if (clang_decls.Size() == 0) {
    ClifError error(*this, kNotFound, ast_->GetLookupScopeName());
    error.Report(CurrentDecl());
    return false;
  }
  return MatchAndSetFuncFromCandidates(clang_decls, func_decl) != nullptr;
}

bool ClifMatcher::MatchAndSetOperatorInContext(
    DeclContext* context,
    FuncDecl* operator_decl) {
  auto overloads = ast_->LookupOperator(context,
                                        operator_decl->name().cpp_name());
  if (overloads.Size() > 0) {
    if (auto func_decl =
        MatchAndSetFuncFromCandidates(overloads, operator_decl)) {
      if (llvm::dyn_cast_or_null<clang::CXXMethodDecl>(func_decl) == nullptr) {
        operator_decl->set_cpp_opfunction(true);
      }
      return true;
    }
  }
  return false;
}

bool ClifMatcher::MatchAndSetOperator(FuncDecl* operator_decl) {
  // Fully qualified names get exact matching, even for operators.
  if (operator_decl->name().cpp_name().find(':') != std::string::npos) {
    ClifLookupResult candidates =
        ast_->LookupScopedSymbol(operator_decl->name().cpp_name());
    if (candidates.Size() == 0) {
      ClifError error(*this, kNotFound, ast_->GetLookupScopeName());
      error.Report(CurrentDecl());
      return false;
    }
    if (auto func_decl =
        MatchAndSetFuncFromCandidates(candidates, operator_decl)) {
      if (llvm::dyn_cast_or_null<clang::CXXMethodDecl>(func_decl) == nullptr) {
        operator_decl->set_cpp_opfunction(true);
      }
      return true;
    }
  }
  clang::Decl* lookup_scope = ast_->GetCurrentLookupScope();
  // If we are inside a class, try that first for an operator overload
  // that matches.
  auto class_decl = llvm::dyn_cast<clang::CXXRecordDecl>(lookup_scope);
  if (class_decl != nullptr) {
    // We only want the first parameter on the working copy of the
    // FunctionDecl, otherwise errors and such get confusing.
    FuncDecl cur_decl = *operator_decl;
    if (MatchAndSetOperatorInContext(class_decl, &cur_decl)) {
      *operator_decl = cur_decl;
      return true;
    }
    // From here, possible matching functions won't have the implicit
    // "this" pointer.  So add it as an explicit first parameter, but
    // only if the current context wasn't a class--if we weren't
    // inside a class, then the Clif-writer shouldn't have been
    // expecing an implicit "this" pointer.
    AdjustForNonClassMethods(&cur_decl);
    // Look inside the same declaration context as the class_decl.
    if (MatchAndSetOperatorInContext(class_decl->getParent(), &cur_decl)) {
      *operator_decl = cur_decl;
      return true;
    }
  }
  // We only want the first parameter on the working copy of the
  // FunctionDecl, otherwise errors and such get confusing.
  FuncDecl cur_decl = *operator_decl;
  AdjustForNonClassMethods(&cur_decl);
  // Look inside the TU declaration context.
  if (MatchAndSetOperatorInContext(ast_->GetTU(), &cur_decl)) {
    *operator_decl = cur_decl;
    return true;
  }
  ClifError error(*this, kNotFound, ast_->GetLookupScopeName());
  error.Report(CurrentDecl());
  return false;
}

bool ClifMatcher::MatchAndSetConstructor(
    CXXRecordDecl* class_decl,
    const clang::SourceLocation& loc,
    FuncDecl* func_decl) {
  // TODO: Figure out a way to suppress this diagnostic if
  // the complete type can't be instantiatiated.
  if (ast_->GetSema().RequireCompleteType(
          loc,
          QualType(class_decl->getTypeForDecl(), 0),
          clang::diag::err_template_spec_redecl_global_scope)) {
    ClifError error(*this, kConstructorNotFound, ast_->GetLookupScopeName());
    error.Report(CurrentDecl());
    return false;
  }

  ClifLookupResult constructors(ast_->GetSema().LookupConstructors(class_decl));
  if (constructors.Size() == 0) {
    ClifError error(*this, kConstructorNotFound, ast_->GetLookupScopeName());
    error.Report(CurrentDecl());
    return false;
  }
  return MatchAndSetFuncFromCandidates(constructors, func_decl) != nullptr;
}

const FunctionDecl* ClifMatcher::MatchAndSetFuncFromCandidates(
    const ClifLookupResult& candidates,
    FuncDecl* func_decl) {
  // Work on a copy of the FuncDecl for each possible match, then copy
  // the correct FuncDecl to the original when it is time. Otherwise,
  // the original clif FuncDecl may have some parameters filled out,
  // and some not and that confuses the matcher on subsequent calls.
  typedef std::pair<const FunctionDecl*, FuncDecl> MatchedDecls;
  typedef std::vector<MatchedDecls> MatchedDeclVector;
  MatchedDeclVector match_decls;
  // Doing this in a loop allows us to report errors for every failed
  // decl. We don't want to early terminate the loop unless we
  // couldn't cast to a function decl (as C++ doesn't allow
  // overloading non-function types).

  ClifError mismatch_error(*this, kOK);
  for (auto decl : candidates.GetResults()) {
    FuncDecl cur_func_decl = *func_decl;
    const FunctionDecl* clang_decl = nullptr;
    auto* template_decl = CheckDeclType<FunctionTemplateDecl>(decl);
    if (template_decl != nullptr) {
      // Some templates won't specialize properly without the class
      // parameter.
      clang_decl = SpecializeFunctionTemplate(template_decl, &cur_func_decl);
      if (!clang_decl) {
        mismatch_error.SetCode(kUnspecializableTemplate);
        continue;
      }
    } else {
      clang_decl = CheckDeclType<FunctionDecl>(decl);
      if (clang_decl == nullptr) {
        // Methods and constructors can be inherited via using decls which
        // occur in the clang AST as clang::UsingDecl instances. The actual
        // decls imported in this fashion occur as clang::UsingShadowDecl
        // within the using decl.
        //
        // When Sema looks up the desired decls by name, UsingShadowDecl
        // instances are returned as matches. However, when sema looks up
        // constructors, it returns the UsingDecl instances also as a match.
        // Hence, we ignore the UsingDecl instances.
        auto using_decl = llvm::dyn_cast<clang::UsingDecl>(decl);
        if (using_decl != nullptr) {
          continue;
        }
        auto using_shadow_decl = llvm::dyn_cast<clang::UsingShadowDecl>(decl);
        if (using_shadow_decl != nullptr) {
          clang::NamedDecl* target_decl = using_shadow_decl->getTargetDecl();
          clang_decl = llvm::dyn_cast<FunctionDecl>(target_decl);
        }
      }
      if (clang_decl == nullptr) {
        ReportTypecheckError<FunctionDecl>(
            decl, func_decl->name().native(), kFunctionNameForError);
        return nullptr;
      }
      // Some FunctionDecl's are children of FunctionTemplateDecls
      // with the same name. These get examined in
      // SpecializeFunctionTemplate, so avoid further handling below.
      if (clang_decl->getDescribedFunctionTemplate() != nullptr &&
          !clang_decl->isFunctionTemplateSpecialization()) {
        continue;
      }
    }
    if (!ImportedFromCorrectFile(*decl, &mismatch_error)) {
      // Ignore certain errors for now. If we don't find any match,
      // these will be listed as failed candidates.
      continue;
    }
    std::string message;
    ClifErrorCode code = MatchAndSetSignatures(
        clang_decl->getType()->getAs<clang::FunctionProtoType>(),
        clang_decl->getMinRequiredArguments(),
        &cur_func_decl, &message);
    if (code == kOK) {
      code = MatchFunctionStatic(clang_decl, cur_func_decl);
    }
    if (code == kOK) {
      match_decls.emplace_back(std::make_pair(clang_decl, cur_func_decl));
    } else {
      mismatch_error.SetCode(code);
      mismatch_error.AddClangDeclAndLocation(ast_.get(), clang_decl);
      mismatch_error.AddMessage(message);
      if (code == kParameterMismatch) {
        mismatch_error.AddMessage(
            "Do all output parameters follow all input parameters?");
      }
    }
  }

  // We prune deprecated functions from among the matches iff there were more
  // than one match.
  MatchedDeclVector pruned_decls;
  if (match_decls.size() == 1) {
    pruned_decls.emplace_back(match_decls.front());
  } else {
    for (auto decl_pair : match_decls) {
      const clang::FunctionDecl *decl = decl_pair.first;
      if (!decl->isDeprecated()) {
        pruned_decls.emplace_back(decl_pair);
      }
    }
  }

  // If multiple decls differ only in the number of const parameters,
  // take the one with the most consts.
  if (pruned_decls.size() > 1) {
    typedef std::pair<int, MatchedDecls> ConstCount;
    std::vector<ConstCount> const_count_sorter;
    for (auto decl_pair : pruned_decls) {
      const_count_sorter.emplace_back(std::make_pair(0, decl_pair));
      auto* prototype =
          decl_pair.first->getType()->getAs<clang::FunctionProtoType>();
      if (auto* method =
          llvm::dyn_cast_or_null<clang::CXXMethodDecl>(decl_pair.first)) {
        if (method->isConst()) {
          ++const_count_sorter.back().first;
        }
      }
      for (int cur_arg = 0; cur_arg < prototype->getNumParams(); cur_arg++) {
        // Top-level consts don't change the signature, so we only care
        // about pointers or references to const.
        QualType qual_type = prototype->getParamType(cur_arg);
        if ((qual_type->isPointerType() || qual_type->isReferenceType()) &&
            qual_type->getPointeeType().isConstQualified()) {
          ++const_count_sorter.back().first;
        }
      }
    }
    std::sort(const_count_sorter.begin(), const_count_sorter.end(),
              [](const ConstCount& a, const ConstCount& b) -> bool {
                return a.first > b.first;
              });
    if (const_count_sorter.begin()->first >
        std::next(const_count_sorter.begin())->first) {
      pruned_decls.clear();
      pruned_decls.push_back(const_count_sorter.front().second);
    }
  }
  // If we found one match, it doesn't matter that any others had an
  // error.
  if (pruned_decls.size() == 1) {
    *func_decl = pruned_decls.front().second;
    const clang::FunctionDecl* clang_decl = pruned_decls.front().first;
    func_decl->mutable_name()->set_cpp_name(
        GetGloballyQualifiedName(clang_decl));

    auto prototype = clang_decl->getType()->getAs<clang::FunctionProtoType>();
    func_decl->set_cpp_noexcept(prototype->hasNoexceptExceptionSpec());

    if (auto method_decl = llvm::dyn_cast<clang::CXXMethodDecl>(clang_decl)) {
      func_decl->set_cpp_const_method(method_decl->isConst());
    }

    for (int i = 0; i < func_decl->params_size(); ++i) {
      if (!func_decl->params(i).has_default_value()) {
        continue;
      }

      const clang::ParmVarDecl* clang_param_decl = clang_decl->getParamDecl(i);
      // We should never hit a case of an unparsed default arg as we always
      // run the matcher at the end of a TU.
      assert(!clang_param_decl->hasUnparsedDefaultArg());
      // However, an uninstantiated default arg can occur if, for example the
      // function to be matched were a template function.
      if (clang_param_decl->hasUninstantiatedDefaultArg()) {
        continue;
      }
      const clang::Expr* def_arg_expr = clang_param_decl->getDefaultArg();
      if (def_arg_expr == nullptr) {
        continue;
      }

      clang::Expr::EvalResult result;
      if (!def_arg_expr->EvaluateAsRValue(result, ast_->GetASTContext())) {
        continue;
      }
      if (result.hasSideEffects()) {
        // Even though the expression could be evaluated as an r-value,
        // there could be side effects which were ignored. For example:
        //   SomeFunc() || true
        // The above expression would always evaluate to true, but SomeFunc
        // will also be called. If we consider only the result in such
        // cases, we will be changing the runtime behavior of the default
        // value expr.
        continue;
      }
      // We want to restrict this to integral, floating point or pointer value
      // (to handle nullptr default value) results. Boolean and enum values are
      // treated by the Clang API to be of integral types.
      // See http://b/29280060 for more info.
      //
      // To check whether the result of evaluating the default value expression
      // is of integral or floating point type, we focus on the result of
      // evaluation and not on the type of the param. This is because there
      // could be case like this:
      //
      // class A {
      //  public:
      //   int a;
      //   operator int() {
      //     return a;
      //   }
      // };
      // int Func(int a = (A){100});
      if (result.Val.isInt() || result.Val.isFloat() ||
          clang_param_decl->getType()->isPointerType()) {
        protos::ParamDecl* param_decl = func_decl->mutable_params(i);
        param_decl->set_default_value(result.Val.getAsString(
            ast_->GetASTContext(), clang_param_decl->getType()));
      }
    }

    return clang_decl;
  } else if (pruned_decls.size() > 1) {
    ReportMultimatchError(*this, ast_.get(), pruned_decls, CurrentDecl());
    // Don't return here. There may be a mismatch error too.
  } else if (match_decls.size() > 1) {
    // All the matched decls are deprecated!
    ReportMultimatchError(*this, ast_.get(), match_decls, CurrentDecl());
  }

  if (mismatch_error.GetCode() != kOK) {
    // Decls with the name were found, but none of the signatures
    // matched.  The decls and locations were added earlier.
    mismatch_error.Report(CurrentDecl());
  }
  return nullptr;
}

// Both Clif and Clang typically treat the "this" pointer in a class
// method call as implicit.  However, sometimes (for example, when
// looking for non-class operator overloads) Clif needs it to be
// explicit.
void ClifMatcher::AdjustForNonClassMethods(FuncDecl* clif_decl) const {
  const ClassDecl* enclosing_class = EnclosingClifClass();
  // If there is no enclosing class, nothing to do. Further matching
  // will fail via the normal mechanism.
  if (enclosing_class == nullptr) {
    return;
  }
  auto params = clif_decl->mutable_params();
  params->Add();
  for (int i = params->size() - 1; i > 0; --i) {
    params->SwapElements(i - 1, i);
  }
  protos::ParamDecl* p = params->Mutable(0);
  *p->mutable_name() = enclosing_class->name();
  p->mutable_type()->set_lang_type(enclosing_class->name().native());
  p->mutable_type()->set_cpp_type(enclosing_class->name().cpp_name());
}

const clang::FunctionDecl* ClifMatcher::SpecializeFunctionTemplate(
    clang::FunctionTemplateDecl* template_decl,
    FuncDecl* clif_func_decl) const {
  clang::FunctionDecl* templated_decl = template_decl->getTemplatedDecl();
  int params_size = clif_func_decl->params().size();
  int arg_count = params_size;
  int ret_val_offset = 0;
  // Adjust for output arguments wrapped as return values.
  if (templated_decl->getReturnType()->isVoidType()) {
    arg_count += clif_func_decl->returns().size();
  } else {
    arg_count += clif_func_decl->returns().size() - 1;
    // If the C++ function has return values, then the output arguments begin
    // from index 1 of clif_func_decl.returns().
    ret_val_offset = 1;
  }
  if (arg_count > templated_decl->getNumParams()) {
    return nullptr;
  }
  clang::sema::TemplateDeductionInfo info((clang::SourceLocation()));
  clang::FunctionDecl* specialized_decl = nullptr;
  llvm::SmallVector<clang::Expr, 4> args;
  llvm::SmallVector<clang::Expr *, 4> arg_ptrs;


  for (int i = 0; i < arg_count; ++i) {
    std::string clif_cpp_type;
    if (i < params_size) {
      clif_cpp_type = clif_func_decl->params(i).type().cpp_type();
    } else {
      clif_cpp_type = clif_func_decl->returns(
          i - params_size + ret_val_offset).type().cpp_type();
    }
    auto clif_qual_type_iter = clif_qual_types_.find(clif_cpp_type);
    assert(clif_qual_type_iter != clif_qual_types_.end());
    // Be a little smart about pointer types in template deduction. If
    // the template takes a T* as a parameter, rather than just a T,
    // Make that work at the deduction point.
    QualType clif_qual_type = clif_qual_type_iter->second.qual_type;
    QualType clang_qual_type = templated_decl->getParamDecl(i)->getType();
    if (clang_qual_type->isPointerType() && !clif_qual_type->isPointerType()) {
      clif_qual_type = ast_->GetASTContext().getPointerType(clif_qual_type);
    } else {
      std::string template_name;
      QualType template_arg_type;
      if (ast_->IsStdSmartPtr(clang_qual_type)) {
        clif_qual_type =
            ast_->BuildTemplateType(
                ast_->GetQualTypeTemplateDecl(clang_qual_type),
                clif_qual_type);
      }
    }
    args.push_back(clang::OpaqueValueExpr(clif_qual_type_iter->second.loc,
                                          clif_qual_type,
                                          clang::ExprValueKind::VK_LValue));
    arg_ptrs.push_back(&args.back());
  }

  ast_->GetSema().DeduceTemplateArguments(
      template_decl,
      nullptr,  // No explicitly listed template arguments.
      arg_ptrs,
      specialized_decl,
      info,
      false,  // No partial overloading
      [&](clang::ArrayRef<QualType> param_types) {
        // For template parameters that aren't instantiation
        // dependent, should we check for valid conversions prior to
        // general template deduction? In real C++ code this prevents
        // overload resolution from picking an invalid overload and
        // thereby instantiating an invalid template. But since Clif
        // does it's own overload resolution, Clif doesn't need it,
        // and Clif avoids some complexity by bypassing this check
        // altogether, which is designed to remedy a defect in the
        // standard (DR1391).
        return false;
      });
  return specialized_decl;
}

void ClifMatcher::BuildTypeTable() {
  // Create a map betwen the unique key for every type in the input proto
  // to its qual type. The key for a type is the typedef name which is
  // CodeBuilder uses for its type index.
  for (auto& clif_to_cpp : builder_.FullyQualifiedTypedefs()) {
    ClifLookupResult result = ast_->LookupScopedSymbol(clif_to_cpp.second);
    assert(result.Size() == 1);
    // Every type declared by the CodeBuilder is typedef.
    auto td_decl = llvm::dyn_cast<clang::TypedefNameDecl>(result.GetFirst());
    assert(td_decl != nullptr);
    clif_qual_types_[clif_to_cpp.first] = {
      td_decl->getCanonicalDecl()->getUnderlyingType().getCanonicalType(),
      td_decl->getLocation()
    };
  }
}


}  // namespace clif

