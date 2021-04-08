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
#include <deque>
#include <memory>

#include "absl/container/btree_map.h"
#include "clif/backend/strutil.h"
#include "clang/AST/Expr.h"
#include "clang/AST/Mangle.h"
#include "clang/AST/QualTypeNames.h"
#include "clang/Sema/Initialization.h"
#include "clang/Sema/Sema.h"
#include "clang/Sema/SemaDiagnostic.h"
#include "clang/Sema/Template.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/raw_ostream.h"

// TODO: Switch to clang diagnostics mechanism for errors.

#define DEBUG_TYPE "clif_matcher"

namespace clif {

// Currently only UNIX-like pathnames are supported.
// For Windows this would be '\\'.
static const char kFilesystemPathSep = '/';

// Support for auxiliary header files with C++ customizations specifically
// for CLIF.
// TODO: Point to new documentation under go/pyclif once it is available.
static const char kClifAux[] = "_clif_aux";
static constexpr std::size_t kClifAuxLen = sizeof(kClifAux) - 1;

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
    case kUncopyableUnmovableReturnType:
      return ("Clif expects output parameters or return types to be copyable "
              "or movable.");
    case kIncompatibleTypes:
      return "Non-matching types.";
    case kParameterCountsDiffer:
      return "Parameter counts differ.";
    case kUnexpectedDefaultSpecifier:
      return "Clif contains unexpected default specifiers.";
    case kWrongOrderDefault:
      return ("Clif expects all required parameters to be placed before "
          "default arguments.");
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
    case kNonVirtualDiamondInheritance:
      return ("Non-virtual diamond inheritance.");
    case kMustUseResultIgnored:
      return ("Clif can not ignore ABSL_MUST_USE_RESULT return values.");
  }
}

static void ReportMultimatchError(
    const ClifMatcher& matcher, const TranslationUnitAST* ast,
    const std::vector<std::pair<const FunctionDecl*, FuncDecl>>& matches,
    Decl* clif_decl, const std::string& message = "") {
  ClifError multimatch_error(matcher, kMultipleMatches);
  for (const auto& decl_pair : matches) {
    multimatch_error.AddClangDeclAndLocation(ast, decl_pair.first);
  }
  multimatch_error.AddMessage(message);
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
  // For a single clif decl, more than one error might be reported. The
  // not_found field should record all of the error messages.
  std::string error_message;
  StrAppend(&error_message, clif_decl->not_found(), error);
  clif_decl->set_not_found(error_message);
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
  for (const auto& types : type_mismatch_stack_) {
    StrAppend(&message,
              "\n Compare:\n",
              "    Clif Type: \"", types.second, "\" with \n",
              "     C++ Type: \"", types.first, "\"");
  }
  return message;
}

std::string ClifMatcher::GetErrorMessageForNonTargetDecl(
    const clang::NamedDecl& clang_decl) const {
  std::string message;
  StrAppend(&message,
            "Clif Error: UsingShadowDecl does not have the target decl\n",
            "Rejected Candidate:\n  ", kMessageIndent,
            ast_->GetClangDeclNameForError(clang_decl), " at ",
            ast_->GetClangDeclLocForError(clang_decl));
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
  LLVM_DEBUG(llvm::dbgs() << clif_ast.DebugString());
  *modified_clif_ast = clif_ast;
  BuildClifToClangTypeMap(clif_ast);
  if (RunCompiler(
          builder_.BuildCode(modified_clif_ast, &clif_to_clang_type_map_),
          compiler_args, input_file_name) == false) {
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
      qual_type, ast_->GetASTContext(),
      ast_->GetASTContext().getPrintingPolicy(),
      true /* Include "::" prefix */);

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
  LLVM_DEBUG(llvm::dbgs() << "Matched proto:\n" << clif_ast->DebugString());
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
  if (!clif_decl.has_cpp_file()) {
    return true;
  }
  std::string clif_cpp_file = clif_decl.cpp_file();
  if (clif_cpp_file.empty()) {
    return true;
  }
  std::string source_file = ast_->GetSourceFile(named_decl);

  // Examples: .../name.h, .../python/name.h, .../python/name_clif_aux.h
  if (llvm::StringRef(source_file).endswith(clif_cpp_file.c_str())) {
    return true;
  }
  std::string decl_expected_in = clif_cpp_file;

  // Testing for kClifAux
  std::size_t dot_pos = clif_cpp_file.rfind('.');
  if (dot_pos != std::string::npos &&
      dot_pos > kClifAuxLen  // Intentionally NOT >= (implies len(name) > 0)
      && llvm::StringRef(clif_cpp_file.c_str() + (dot_pos - kClifAuxLen))
             .startswith(kClifAux)) {
    // Example: .../python/name.h
    std::string clif_cpp_file_no_aux =
        clif_cpp_file.substr(0, dot_pos - kClifAuxLen) +
        clif_cpp_file.substr(dot_pos, std::string::npos);
    if (llvm::StringRef(source_file).endswith(clif_cpp_file_no_aux.c_str())) {
      return true;
    }
    decl_expected_in += ", " + clif_cpp_file_no_aux;

    // Example: .../name.h (one directory level up)
    // The name of the subdirectory is intentionally NOT checked HERE.
    std::size_t sep_pos_r1 = clif_cpp_file_no_aux.rfind(kFilesystemPathSep);
    if (sep_pos_r1 != std::string::npos && sep_pos_r1 > 0) {
      std::size_t sep_pos_r2 = clif_cpp_file_no_aux.rfind(
          kFilesystemPathSep, sep_pos_r1 - 1);
      if (sep_pos_r2 != std::string::npos) {
        std::string clif_cpp_file_no_aux_level_up =
            clif_cpp_file_no_aux.substr(0, sep_pos_r2) +
            clif_cpp_file_no_aux.substr(sep_pos_r1, std::string::npos);
        if (llvm::StringRef(source_file).endswith(
                clif_cpp_file_no_aux_level_up.c_str())) {
          return true;
        }
        decl_expected_in += ", " + clif_cpp_file_no_aux_level_up;
      }
    }
    decl_expected_in = "one of the files {" + decl_expected_in + "}";
  } else {  // not clif_aux
    decl_expected_in = "the file " + decl_expected_in;
  }

  error->SetCode(kNotInImportFile);
  std::string message;
  StrAppend(&message,
            "Clif expects it in ",
            decl_expected_in,
            " but found it at ",
            ast_->GetClangDeclLocForError(named_decl));
  error->AddMessage(message);
  return false;
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

std::string ClifMatcher::ClifDeclName(
    const clang::NamedDecl* named_decl) const {
  if (clang::isa<clang::CXXRecordDecl>(named_decl)) {
    return "C++ class";
  }
  if (clang::isa<clang::CXXConstructorDecl>(named_decl)) {
    return "C++ constructor";
  }
  if (clang::isa<clang::CXXDestructorDecl>(named_decl)) {
    return "C++ destructor";
  }
  if (clang::isa<clang::CXXConversionDecl>(named_decl)) {
    return "C++ conversion function";
  }
  if (clang::isa<clang::CXXMethodDecl>(named_decl)) {
    return "C++ method";
  }
  if (clang::isa<clang::FunctionDecl>(named_decl)) {
    return "C++ function";
  }
  if (clang::isa<clang::FunctionTemplateDecl>(named_decl)) {
    return "C++ template function";
  }
  if (clang::isa<clang::ClassTemplateDecl>(named_decl)) {
    return "C++ template class";
  }
  if (clang::isa<clang::ConstructorUsingShadowDecl>(named_decl)) {
    return "C++ constructor imported by \"using\" declaration";
  }
  if (clang::isa<clang::UsingShadowDecl>(named_decl)) {
    return "\"using\" declaration";
  }
  if (clang::isa<clang::EnumDecl>(named_decl)) {
    return "C++ enum";
  }
  if (clang::isa<clang::FieldDecl>(named_decl)) {
    return "C++ field";
  }
  if (clang::isa<clang::VarDecl>(named_decl)) {
    return "C++ varaible";
  }
  return named_decl->getDeclKindName();
}

template<class ClangDeclType>
void ClifMatcher::ReportTypecheckError(
    clang::NamedDecl* named_decl,
    const std::string& clif_identifier,
    const std::string& clif_type) const {
  std::string message;
  StrAppend(&message, "Type mismatch: Clif declares ", clif_identifier, " as ",
            clif_type, " but its name matched \"",
            named_decl->getQualifiedNameAsString(), "\" which is a ",
            ClifDeclName(named_decl), ".");
  ClifError error(*this, kTypeMismatch, message);
  error.AddClangDeclAndLocation(ast_.get(), named_decl);
  error.Report(CurrentDecl());
}

namespace detail {

// Practical approch to enforcing matching CLIF types for widely used
// optional-like C++ types with implicit conversion to the held type(s).
// Example:
//   C++   std::optional<int> ReturnOptionalInt();
//   CLIF  def ReturnOptionalInt() -> NoneOr<int>  # OK
//   CLIF  def ReturnOptionalInt() -> int  # No match b/o logic here.
bool CheckOptionalLikeTypes(
    std::string from_clif_name,
    std::string to_clif_name) {
  const std::array<const std::string, 6> covered_types({
      "::absl::optional<",
      "::absl::StatusOr<",
      "::absl::variant<",
      "::std::optional<",
      "::std::variant<",
  });
  for (const auto& covered_type : covered_types) {
    if (from_clif_name.find(covered_type, 0) == 0) { //  NOLINT abseil-string-find-startswith
      continue;  // Optional-like in .clif file.
      // NOT checking here: Optional-like in .clif but not in C++.
      // It fails elsewhere.
    }
    if (to_clif_name.find(covered_type, 0) != 0) { //  NOLINT abseil-string-find-startswith
      continue;  // Optional-like not in .clif and not in C++.
    }
    // Optional-like not in .clif but in C++.
    return false;
  }
  return true;
}

}  // namespace detail

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

  if (!detail::CheckOptionalLikeTypes(GetQualTypeClifName(from_type),
                                      GetQualTypeClifName(to_type))) {
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

  // The clif type may be assignable to the C++ type via a converting
  // constructor.  If that converting constructor is part of a template,
  // AreAssignableTypes may need to instantiate it. But by the time matching
  // takes place, Sema has deleted the Parser and the associated scopes. It is
  // something of a wart in clang that instantiating some template declarations
  // in this situation need Scopes instead of DeclContexts. Fake a scope for
  // those that need it.
  //
  // Usually this template instantiation happens via a similar construct
  // somewhere else in the original source, but if one doesn't exist, there may
  // have been no need to instantiate the template before this.
  //
  // Logically, matching takes place just before the end of the TU, so the TU
  // should never have been closed, but buildASTFromCodeWithArgs doesn't allow
  // that level of control. It would be more correct to switch to a hand-built
  // CompilerInstance which doesn't tear down the parser until after
  // matching--the lldb expression parser does this.
  ast_->PushFakeTUScope();
  // Object's destructor exits the context.
  clang::EnterExpressionEvaluationContext context(ast_->GetSema(),
      clang::Sema::ExpressionEvaluationContext::Unevaluated);

  InitializedEntity entity =
      InitializedEntity::InitializeResult(
          loc, to_type, false);  // NRVO is irrelevant.
  clang::OpaqueValueExpr init_expr(loc, from_type.getNonReferenceType(),
                                   clang::ExprValueKind::VK_LValue);
  bool assignable = ast_->GetSema().CanPerformCopyInitialization(
      entity, &init_expr);
  // Sema is very sensitive, so don't leave this fake scope in place any longer
  // than is absolutely necessary.
  ast_->PopFakeTUScope();
  return assignable;
}

bool ClifMatcher::AreEqualTypes(QualType from_type, QualType to_type) const {
  auto from_canonical_type = from_type.getCanonicalType().getTypePtr();
  auto to_canonical_type = to_type.getCanonicalType().getTypePtr();
  return (from_canonical_type == to_canonical_type);
}

bool ClifMatcher::SelectTypeWithTypeSelector(
    clang::QualType clang_type, ClifRetryType try_type, Type* clif_type,
    clang::QualType* type_selected) const {
  QualType possible_clif_type;
  auto type_map = clif_to_clang_type_map_.find(clif_type->lang_type());
  if (type_map == clif_to_clang_type_map_.end()) {
    return false;
  }
  std::vector<std::string> possible_clif_type_names = type_map->second;
  QualType first_assignable_clif_type;
  int assignable_clif_type_count = 0;
  QualType equal_clif_type;
  int equal_clif_type_count = 0;

  // Iterates through all of the possible CLIF cpp types. Finds the equal type
  // to clang type if exists. Otherwise, CLIF chooses the first assignable CLIF
  // cpp type to clang type.
  for (const std::string& clif_type_name : possible_clif_type_names) {
    auto clif_type_iter = clif_qual_types_.find(clif_type_name);
    assert(clif_type_iter != clif_qual_types_.end());
    possible_clif_type = clif_type_iter->second.qual_type;

    if (clif_type->cpp_raw_pointer() && !possible_clif_type->isPointerType()) {
      possible_clif_type =
          ast_->GetASTContext().getPointerType(possible_clif_type);
    }

    switch (try_type) {
      // Tries the pointer version of the possible CLIF cpp types.
      case ClifRetryType::kPointer: {
        possible_clif_type = ast_->GetSema().BuildPointerType(
            possible_clif_type, clif_type_iter->second.loc, DeclarationName());
        break;
      }
      // Tries the nonconst and nonref version of the possible CLIF cpp types.
      case ClifRetryType::kNonconstNonref: {
        possible_clif_type =
            possible_clif_type.getNonReferenceType().getUnqualifiedType();
        break;
      }
      default:
        break;
    }

    if (AreEqualTypes(possible_clif_type, clang_type)) {
      if (equal_clif_type_count == 0) {
        equal_clif_type = possible_clif_type;
      }
      equal_clif_type_count++;
    } else if ((try_type != ClifRetryType::kArray &&
                AreAssignableTypes(possible_clif_type,
                                   clif_type_iter->second.loc, clang_type)) ||
               (try_type == ClifRetryType::kArray &&
                AreAssignableTypes(clang_type, clif_type_iter->second.loc,
                                   possible_clif_type))) {
      if (assignable_clif_type_count == 0) {
        first_assignable_clif_type = possible_clif_type;
      }
      assignable_clif_type_count++;
    }
  }

  // Chooses the equal candidate type to clang type if there exists.
  if (equal_clif_type_count != 0) {
    *type_selected = equal_clif_type;
    return true;
  }
  // Otherwise, chooses the first assignable candidate type.
  if (assignable_clif_type_count != 0) {
    *type_selected = first_assignable_clif_type;
    return true;
  }
  // Otherwise, there is no available clif cpp type.
  return false;
}

// Selects the appropriate CLIF cpp type either with/without type selector.
bool ClifMatcher::SelectType(const clang::QualType& clang_type,
                             ClifRetryType try_type, bool enable_type_selector,
                             const ClifQualTypeDecl* clif_cpp_decl,
                             Type* clif_type,
                             clang::QualType* type_selected) const {
  if (enable_type_selector) {
    return SelectTypeWithTypeSelector(clang_type, try_type, clif_type,
                                      type_selected);
  }
  // When users specify the cpp_type on purpose, CLIF will disable the type
  // selector and use the user specified CLIF cpp type.

  // Desugars to use what the user wrote, rather than clif_type_0.
  *type_selected = clif_cpp_decl->qual_type.getSingleStepDesugaredType(
      ast_->GetASTContext());

  if (clif_type->cpp_raw_pointer() && !(*type_selected)->isPointerType()) {
    *type_selected = ast_->GetASTContext().getPointerType(*type_selected);
  }
  switch (try_type) {
    case ClifRetryType::kPointer: {
      *type_selected = ast_->GetSema().BuildPointerType(
          *type_selected, clif_cpp_decl->loc, DeclarationName());
      break;
    }
    case ClifRetryType::kArray: {
      return AreAssignableTypes(clang_type, clif_cpp_decl->loc, *type_selected);
    }
    case ClifRetryType::kNonconstNonref: {
      *type_selected =
          type_selected->getNonReferenceType().getUnqualifiedType();
      break;
    }
    default:
      break;
  }
  return AreAssignableTypes(*type_selected, clif_cpp_decl->loc, clang_type);
}

bool ClifMatcher::MatchAndSetClassName(ForwardDecl* forward_decl) const {
  auto clif_qual_type = clif_qual_types_.find(forward_decl->name().cpp_name());
  assert(clif_qual_type != clif_qual_types_.end());
  forward_decl->mutable_name()->set_cpp_name(
      clang::TypeName::getFullyQualifiedName(
          clif_qual_type->second.qual_type, ast_->GetASTContext(),
          ast_->GetASTContext().getPrintingPolicy(),
          true /* Include "::" prefix */));
  // We always set these to true for classes and capsules.
  ast_->AddPtrConversionType(clif_qual_type->second.qual_type);
  ast_->AddUniquePtrConversionType(clif_qual_type->second.qual_type);
  return true;
}

// Calculate if a base type should be added to the clif declaration. Return
// false if non-virtual diamond inheritance happens.
bool ClifMatcher::CalculateBaseClassesHelper(
    ClassDecl* clif_decl, BaseSpecifierQueue* base_queue,
    QualTypeMap* public_bases,
    ClassTempSpecializedDeclMap* public_template_specialized_bases) const {
  auto base = base_queue->front();
  base_queue->pop();
  // Bypass private and protected base classes.
  if (base.getAccessSpecifier() == clang::AS_public) {
    bool is_virtual = base.isVirtual();
    QualType base_type = base.getType();
    CXXRecordDecl* base_clang_decl = base_type->getAsCXXRecordDecl();
    if (public_bases->find(base_type) == public_bases->end()) {
      // Template specialized base classes are differently represented from
      // regular base classes. Consider the following diamond inheritance
      // example:
      // template <class T>
      // class base {};
      //
      // template <class T>
      // class derive1: virtual public base<T> {};
      //
      // template <class T>
      // class derive2: virtual public base<T> {};
      //
      // template <class T>
      // class derive3: virtual public derive1<T>, virtual public derive2<T> {};
      //
      // While processing derive3's base classes, we will encounter "base<int>"
      // twice, one(named "b1") is the base of "derive1" and another(names "b2")
      // is the base of "derive2". "b1" and "b2" have different QualTypes
      // because class "base" is specialized separately for them, but the same
      // ClassTemplateSpecializationDecl. To avoid the duplication of
      // recording base classes in diamond inheritance, we also need to keep a
      // set of ClassTemplateSpecializationDecl for specialized template base
      // classes.
      auto template_specialized_decl =
          llvm::dyn_cast<ClassTemplateSpecializationDecl>(base_clang_decl);
      if (template_specialized_decl) {
        auto decl_iter =
            public_template_specialized_bases->find(template_specialized_decl);
        if (decl_iter != public_template_specialized_bases->end()) {
          // Non-virtual diamond inheritance for template classes.
          if (decl_iter->second != true || !is_virtual) {
            return false;
          }
          return true;
        }
        public_template_specialized_bases->insert(
            {template_specialized_decl, is_virtual});
      }
      const std::string base_type_name = GetQualTypeClifName(base_type);
      // The proto fields "bases" and "cpp_bases" are separate for
      // historical reasons.
      clif_decl->add_bases()->set_cpp_name(base_type_name);
      ClassDecl::Base* cpp_base = clif_decl->add_cpp_bases();
      cpp_base->set_name(base_type_name);
      cpp_base->set_filename(ast_->GetSourceFile(*base_clang_decl));
      if (auto* context = base_clang_decl->getEnclosingNamespaceContext()) {
        if (auto* namespace_decl = llvm::dyn_cast<NamespaceDecl>(context)) {
          cpp_base->set_namespace_(namespace_decl->getNameAsString());
        }
      }
      for (auto child_base : base_clang_decl->bases()) {
        base_queue->push(child_base);
      }
      public_bases->insert({base_type, is_virtual});
    } else if ((*public_bases)[base_type] != true || !is_virtual) {
      // Non-virtual diamond inheritance for regular classes.
      return false;
    }
  }
  return true;
}

// Collect public base classes of |clang_decl| and save them in |clif_decl|.
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

  // Traverse all of the base classes of the current ClassDecl and update
  // clif_decl. Base classes for private/protected inheritances are skipped.
  // "base_queue" stores the base classes waiting to be processed.
  BaseSpecifierQueue base_queue;
  // public_bases keeps already processed bases to avoid duplicate reporting.
  QualTypeMap public_bases;
  // public_template_specialized_bases keeps processed template specialized
  // bases.
  ClassTempSpecializedDeclMap public_template_specialized_bases;

  for (auto base : clang_decl->bases()) {
    base_queue.push(base);
  }
  while (!base_queue.empty()) {
    const std::string base_type_name =
        base_queue.front().getType()->getAsCXXRecordDecl()->getNameAsString();
    if (!CalculateBaseClassesHelper(clif_decl, &base_queue, &public_bases,
                                    &public_template_specialized_bases)) {
      ClifError error(*this, kNonVirtualDiamondInheritance);
      std::string message;
      StrAppend(
          &message, "C++ class \"", clang_decl->getNameAsString(),
          "\" contains non-virtual diamond inheritance of the base class \"",
          base_type_name, "\".");
      error.AddMessage(message);
      error.AddClangDeclAndLocation(ast_.get(), clang_decl);
      error.Report(CurrentDecl());
      return false;
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

  // Check if the class is an instantiation of a template. If so, we can allow
  // the class declaration located at a separate file.
  clang::ClassTemplateDecl* template_decl =
      ast_->GetQualTypeTemplateDecl(clif_type->second.qual_type);
  if (template_decl == nullptr) {
    ClifError mismatch_error(*this, kOK);
    ImportedFromCorrectFile(*record_decl, &mismatch_error);
    // If the class is not an instantiation of a template, but declared in
    // a separate file, report error(kNotInImportFile).
    if (mismatch_error.GetCode() != kOK) {
      mismatch_error.Report(CurrentDecl());
      ast_->PopLookupContext();
      return false;
    }
  }

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
  class_decl->set_is_cpp_polymorphic(record_decl->isPolymorphic());
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

  // Need sorted container for output stability.
  absl::btree_map<std::string, protos::Name*> clif_enumerators;
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
  // Need sorted container for output stability.
  absl::btree_map<std::string, NamedDecl*> clang_enumerators;
  for (const auto& clang_enumerator : clang_decl->enumerators()) {
    clang_enumerators[clang_enumerator->getNameAsString()] = clang_enumerator;
    LLVM_DEBUG(llvm::dbgs()
          << "Clang enumerator : " << clang_enumerator->getNameAsString());
  }
  std::vector<std::string> extras;
  for (const auto& enumerator : clif_enumerators) {
    if (clang_enumerators.find(enumerator.first) == clang_enumerators.end()) {
      extras.emplace_back(enumerator.first);
    }
  }
  if (!extras.empty()) {
    std::string error;
    StrAppend(&error,
              "Extra enumerators in Clif enum declaration ",
              enum_decl->name().native(), ".  C++ enum ",
              clang_decl->getQualifiedNameAsString(),
              " does not contain enumerator(s):");
    for (const std::string& extra : extras) {
      StrAppend(&error, " ", extra);
    }
    StrAppend(&error, ".\n");
    llvm::errs() << error;
    CurrentDecl()->set_not_found(error);
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
  LLVM_DEBUG(llvm::dbgs() << enum_decl->DebugString());
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
                     clif_qual_type->second.qual_type, ast_->GetASTContext(),
                     ast_->GetASTContext().getPrintingPolicy(), true),
                 type);
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

ClifErrorCode ClifMatcher::MatchAndSetCallable(QualType callable_type,
                                               FuncDecl* callable) {
  // Check if callable_type is const &, if so, remove both const and &, so that
  // callable_type matches with "std::function"
  if (callable_type->isReferenceType()) {
    callable_type = callable_type.getNonReferenceType();
    callable_type.removeLocalConst();
  }
  if (ast_->GetStdTemplateDecl("function") ==
      ast_->GetQualTypeTemplateDecl(callable_type)) {
    QualType func_type = ast_->GetTemplateArgType(callable_type);
    std::string message;
    // nullptr means all args are non-default (eg.in std::function).
    auto* clang_prototype = func_type->getAs<clang::FunctionProtoType>();
    ClifErrorCode code =
        MatchAndSetSignatures(nullptr, clang_prototype, callable, &message);
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
    if (ast_->GetSema().isCompleteType(clang_decl->getLocation(),
                                        clang_type)) {
      SetTypePropertiesHelper(clang_decl, clif_decl);
    } else {
      // From clif's perspective, if we have no definition for the
      // class (maybe it was forward declared), it may as well be
      // abstract.
      clif_decl->set_cpp_abstract(true);
    }
  }
}

template <class T>
void ClifMatcher::SetTypePropertiesHelper(clang::CXXRecordDecl* clang_decl,
                                          T* clif_decl) const {
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
  if (!ast_->IsClifMovable(clang_decl) ||
      !ast_->DestructorIsAccessible(clang_decl)) {
    clif_decl->set_cpp_movable(false);
  }
  if (clang_decl->isAbstract()) {
    clif_decl->set_cpp_abstract(true);
  }
  SetUniqueClassProperties(clang_decl, clif_decl);
}

template<> void SetUniqueClassProperties(const clang::CXXRecordDecl* clang_decl,
                                         clif::ClassDecl* clif_decl) {
  if (clang_decl->hasTrivialDefaultConstructor()) {
    clif_decl->set_cpp_has_trivial_defctor(true);
  }
  if (clang_decl->hasTrivialDestructor()) {
    clif_decl->set_cpp_has_trivial_dtor(true);
  }
}

// template_required indicates if we are expecting both clif_type and clang_type
// to be template types. When MatcheAndSetContainerHelper is invoked by
// MatchAndSetContainer, template_required is set to true because clif_type and
// clang_type should be containers.
ClifErrorCode ClifMatcher::MatchAndSetContainerHelper(
    const QualType& clang_type, const QualType& clif_type,
    const clang::SourceLocation& loc, bool template_required) {
  QualType clang_qual_type = clang_type.getCanonicalType();
  QualType clif_qual_type = clif_type;
  // Remove clang_qual_type's pointer if there exist.
  bool is_clang_type_a_ptr = false;
  if (clang_qual_type->isPointerType()) {
    is_clang_type_a_ptr = true;
    clang_qual_type = clang_qual_type->getPointeeType().getUnqualifiedType();
  }
  // Process clang_qual_type if it is a smart pointer. If clang_qual_type is
  // std::smart_ptr<PointeeType>, then we remove the outer smart pointer
  // template and get the PointeeType for matching and setting in later section.
  bool is_smart_ptr = false;
  if (ast_->IsStdSmartPtr(clang_qual_type)) {
    clang_qual_type = ast_->GetTemplateArgType(clang_qual_type);
    is_smart_ptr = true;
  }

  // Parse the clang_decl and clang_args from clang_qual_type.
  const clang::TemplateArgument* clang_args = nullptr;
  int num_clang_args = 0;
  clang::Decl* clang_template_decl = nullptr;
  if (const auto* record =
          clang_qual_type.getNonLValueExprType(ast_->GetASTContext())
              ->getAs<clang::RecordType>()) {
    if (auto clang_decl = llvm::dyn_cast<const ClassTemplateSpecializationDecl>(
            record->getDecl())) {
      clang_args = clang_decl->getTemplateArgs().data();
      num_clang_args = clang_decl->getTemplateArgs().size();
      clang_template_decl =
          clang_decl->getSpecializedTemplate()->getCanonicalDecl();
    }
  } else if (auto clang_decl =
                 clang_qual_type->getAs<clang::TemplateSpecializationType>()) {
    clang_args = clang_decl->getArgs();
    num_clang_args = clang_decl->getNumArgs();
    clang_template_decl =
        clang_decl->getTemplateName().getAsTemplateDecl()->getCanonicalDecl();
  }

  // Parse the clif_decl and clif_args from clif_qual_type.
  auto clif_record_decl = clif_qual_type.getNonReferenceType()
                              .getCanonicalType()
                              ->getAsCXXRecordDecl();
  clang::Decl* clif_template_decl = nullptr;
  const clang::TemplateArgument* clif_args = nullptr;
  const ClassTemplateSpecializationDecl* clif_decl = nullptr;
  int num_clif_args = 0;
  bool is_basic_string = false;
  if (clif_record_decl != nullptr) {
    clif_decl =
        CheckDeclType<ClassTemplateSpecializationDecl>(clif_record_decl);
    if (clif_decl) {
      num_clif_args = clif_decl->getTemplateArgs().size();
      clif_args = clif_decl->getTemplateArgs().data();
      clif_template_decl =
          clif_decl->getSpecializedTemplate()->getCanonicalDecl();
      // If the type we are matching is "::std::basic_string" or
      // "::basic_string", we can not match clif and clang template type by
      // comparing whether clif_template_decl and clang_template_decl are equal.
      // "basic_string" is a versioned symbol in google3 and might appear as
      // "::std::basic_string" or "::basic_string". We match by checking whether
      // clif_qual_type and clang_qual_type are assignable for "basic_string".
      auto *context = clif_decl->getDeclContext()->getRedeclContext();
      if ((context->isStdNamespace() || context->isTranslationUnit()) &&
          clif_decl->getIdentifier()->isStr("basic_string")) {
        is_basic_string = true;
      }
    }
  }

  // If both clang_type and clif_type are templates, they can only be matched if
  // all of the following rules are satisfied("basic_string" is an exception):
  // 1. clang_type and clif_type's canonical template decls are the same.
  // 2. clang_type and clif_type's number of template arguments are the same.
  // 3. Each clang_type and clif_type's template arguments are matched.
  if (clang_template_decl && clif_template_decl) {
    if (clang_template_decl == clif_template_decl) {
      if (num_clang_args != num_clif_args) {
        return kIncompatibleTypes;
      }
      // TODO: Add more information about the container's template
      // arguments' type mismatch error message.
      //
      // Recursively call MatchAndSetContainerHelper to check if each of the
      // clang_type and clif_type's template arguments are matched.
      for (int arg_count = 0; arg_count < num_clang_args; arg_count++) {
        auto clang_arg_type = clang_args[arg_count].getKind();
        auto clif_arg_type = clif_args[arg_count].getKind();
        if (clang_arg_type != clif_arg_type) {
          return kIncompatibleTypes;
        }
        switch (clang_arg_type) {
          case clang::TemplateArgument::Type: {
            if (MatchAndSetContainerHelper(clang_args[arg_count].getAsType(),
                                           clif_args[arg_count].getAsType(),
                                           loc, false) != kOK) {
              return kIncompatibleTypes;
            }
            break;
          }
          case clang::TemplateArgument::Pack: {
            // If a template argument is of Pack kind, then the items in the
            // pack are guaranteed to be type arguments.
            if (clang_args[arg_count].pack_size() !=
                clif_args[arg_count].pack_size()) {
              return kIncompatibleTypes;
            }
            auto clang_iter = clang_args[arg_count].pack_begin();
            auto clif_iter = clif_args[arg_count].pack_begin();
            auto clang_iter_end = clang_args[arg_count].pack_end();
            while (clang_iter != clang_iter_end) {
              if (MatchAndSetContainerHelper(clang_iter->getAsType(),
                                             clif_iter->getAsType(), loc,
                                             false) != kOK) {
                return kIncompatibleTypes;
              }
              ++clang_iter;
              ++clif_iter;
            }
            break;
          }
          case clang::TemplateArgument::Integral: {
            auto clang_arg_integral_type =
                clang_args[arg_count].getIntegralType();
            auto clif_arg_integral_type =
                clif_args[arg_count].getIntegralType();
            if (clang_arg_integral_type != clif_arg_integral_type) {
              return kIncompatibleTypes;
            }
            auto clang_arg_integral = clang_args[arg_count].getAsIntegral();
            auto clif_arg_integral = clif_args[arg_count].getAsIntegral();
            if (clang_arg_integral != clif_arg_integral) {
              return kIncompatibleTypes;
            }
            break;
          }
          default: {
            return kIncompatibleTypes;
            break;
          }
        }
      }
      return kOK;
    } else if (!is_basic_string) {
      return kIncompatibleTypes;
    }
  } else if (template_required) {
    // If MatchAndSetContainerHelper is invoked by MatchAndSetContainer
    // directly, we expect both clang_type and clif_type to be templates.
    return kIncompatibleTypes;
  }
  if ((!clang_template_decl && !clif_template_decl) || is_basic_string) {
    // If none of clang_type and clif_type is a template or if they are
    // "basic_string", check if they are assignable to each other.
    if (is_smart_ptr || is_clang_type_a_ptr) {
      clang_qual_type = ast_->GetASTContext().getPointerType(clang_qual_type);
      // Clif template type's default template argument might already contain
      // *.
      if (!clif_qual_type->isPointerType()) {
        clif_qual_type = ast_->GetASTContext().getPointerType(clif_qual_type);
      }
    }
    if (AreAssignableTypes(clif_qual_type, loc, clang_qual_type)) {
      return kOK;
    }
    // Clif_qual_type and clang_qual_type might be uncopyable. If their
    // pointer type are assignable, it's still a match.
    if (!clang_qual_type->isPointerType() && !clif_qual_type->isPointerType()) {
      if (AreAssignableTypes(
              ast_->GetASTContext().getPointerType(clif_qual_type), loc,
              ast_->GetASTContext().getPointerType(clang_qual_type))) {
        return kOK;
      }
    }
    type_mismatch_stack_.emplace_back(
        std::make_pair(GetQualTypeClifName(clang_qual_type),
                       GetQualTypeClifName(clif_qual_type)));
    return kIncompatibleTypes;
  }
  return kIncompatibleTypes;
}

ClifErrorCode ClifMatcher::MatchAndSetContainer(const QualType& clang_type,
                                                protos::Type* composed,
                                                unsigned int flags) {
  QualType reffed_type = clang_type;
  // The actual C++ type could be a pointer.
  bool original_is_ptr_type = false;
  if (reffed_type->isPointerType()) {
    original_is_ptr_type = true;
    reffed_type = reffed_type->getPointeeType().getUnqualifiedType();
  }

  auto clif_qual_decl = clif_qual_types_.find(composed->cpp_type());
  assert(clif_qual_decl != clif_qual_types_.end());
  auto clif_qual_type = clif_qual_decl->second.qual_type;

  // Here we matched and set the container by matching clang_qual_type and
  // clif_qual_type. We can not match the clang qual type with parameters
  // listed in clif .ipb directly because clif .ipb might not show the correct
  // information about the underlying template arguments types when the c++
  // template uses template alias.
  if (MatchAndSetContainerHelper(reffed_type, clif_qual_type,
                                 clif_qual_decl->second.loc, true) != kOK) {
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
    // When the current type smart_ptr<builtintype> is the return type, we keep
    // the flag TMF_RETURN_TYPE so that qualifiers of builtintype are kept.
    flags = TMF_EXACT_TYPE | (flags & TMF_RETURN_TYPE);
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
  // type_to_match is the nested type of a smart pointer, so we update flags.
  flags |= TMF_FROM_SMART_PTR;
  ClifErrorCode code = MatchAndSetType(type_to_match, clif_type, flags);
  if (code != kOK) {
    return code;
  }

  // Hard code smart_ptr template's name to be
  // "::std::unique_ptr"/"::std::shared_ptr" In case that smart_ptrs are defined
  // in different versions.
  clang::ClassTemplateDecl* template_decl =
      ast_->GetQualTypeTemplateDecl(smart_ptr_type);
  std::string type_name;
  if (template_decl == ast_->GetStdTemplateDecl(kUniquePtrName)) {
    type_name = "::std::unique_ptr";
  } else {
    type_name = "::std::shared_ptr";
  }
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
  QualType reference_type = type_to_report;
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
  // Record the canonical type, so that the generated code is not influenced by
  // the sugar of the clang type.
  type_to_report = type_to_report.getCanonicalType();
  // For the function's return type, if the c++ type is the nested type of a
  // smart pointer, we keep the qualifiers of the type.
  if ((flags & TMF_RETURN_TYPE) && (flags & TMF_FROM_SMART_PTR)) {
    return type_to_report;
  } else {
    // If the function's return value is uncopyable, we would keep the const
    // qualifier and reference if the original clang type has them.
    // Example:
    // If we have a C++ function: const T& FactoryConstRef();
    // When T is uncopyable but movable, CLIF wants to have "const T& ret0 =
    // FactoryConstRef();" in the generated code. Dropping the const qualifier
    // and & would lead to a compilation error. We keep the const qualifier and
    // & here as long as T is uncopyable. The compiler will produce an error if
    // T is both uncopyable and unmovable.
    // When T is copyable, it's clean and safe to keep the original clif
    // matcher's implemetation, which generates "T ret0 = FactoryConstRef();"

    type_to_report = type_to_report.getUnqualifiedType();
    // TODO: check if matcher could restore const and & on all return
    // values.
    auto type_to_report_decl = type_to_report->getAsTagDecl();
    if ((flags & TMF_RETURN_TYPE) &&
        !AreAssignableTypes(type_to_report,
                            type_to_report_decl != nullptr
                                ? type_to_report_decl->getLocation()
                                : clang::SourceLocation(),
                            type_to_report)) {
      // Add reference back to the type.
      if (clang_type->isReferenceType()) {
        type_to_report = reference_type.getUnqualifiedType().getCanonicalType();
      }
      // Add const back to the type.
      if (clang_type.isConstQualified() && !type_to_report.isConstQualified()) {
        type_to_report.addConst();
      }
    }
    return type_to_report;
  }
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

  // If users do not specify the clif_type's cpp_type on purpose, the automatic
  // type selector is enabled.
  const bool enable_type_selector = clif_type->cpp_type().empty();
  QualType type_selected;
  ClifQualTypeDecl clif_cpp_decl;

  if (!enable_type_selector) {
    assert((clif_qual_types_.find(clif_type->cpp_type()) !=
            clif_qual_types_.end()));
    clif_cpp_decl = clif_qual_types_.find(clif_type->cpp_type())->second;
  }

  if (SelectType(clang_type, ClifRetryType::kPlain, enable_type_selector,
                 &clif_cpp_decl, clif_type, &type_selected)) {
    // In this condition, HandleTypeMatchFlags will get clif_qual_type and
    // clang_type's pointee types if clang_type is a pointer.

    // Check if clang_type and clif_qual_type are both pointer or non-pointer
    // types. In regular cases, the condition is satisfied except for one case:
    // clang_type is a pointer but clif_qual_type not.

    // Matcher will crash when clang_type is a pointer but clif_qual_type not,
    // because HandleTypeMatchFlags is getting the pointee type of a non-pointer
    // type(clif_qual_type).

    if (!(clang_type->isPointerType() ^ type_selected->isPointerType())) {
      // Cases 3, 5, and 8.
      SetUnqualifiedCppType(
          HandleTypeMatchFlags(clang_type, type_selected, flags), clif_type);
      return kOK;
    }
    // For input parameters, allow implicit conversion between clang_type and
    // clif_type when clang_type is a pointer but clif_qual_type not.
    //
    // Example:
    // C++:
    // struct A {};
    //
    // class B {
    //  public:
    //   operator A*();
    // };
    //
    // void FuncImplicitConversion(A* a);
    //
    // CLIF: def FuncImplicitConversion(b: B)
    //
    // Use clif_qual_type's name("::B") for cpp_type in .opb because CLIF does
    // not have the conversion function Clif_PyObjAs(A**, ...).
    if (!type_selected->isPointerType() && clang_type->isPointerType() &&
        (flags & TMF_DERIVED_CLASS_TYPE) &&
        (flags & TMF_UNCONVERTED_REF_TYPE) &&
        (flags & TMF_REMOVE_CONST_POINTER_TYPE)) {
      SetUnqualifiedCppType(type_selected, clif_type);
      clif_type->set_implicitly_converted(true);
      return kOK;
    }
  }

  if (clang_type->isArrayType() &&
      SelectType(clang_type, ClifRetryType::kArray, enable_type_selector,
                 &clif_cpp_decl, clif_type, &type_selected)) {
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
    if (SelectType(clang_type, ClifRetryType::kPointer, enable_type_selector,
                   &clif_cpp_decl, clif_type, &type_selected)) {
      // Cases 2 and 6.
      SetUnqualifiedCppType(
          HandleTypeMatchFlags(clang_type, type_selected, flags), clif_type);
      return kOK;
    }
  }
  // Try again without const and ref.
  if (SelectType(clang_type, ClifRetryType::kNonconstNonref,
                 enable_type_selector, &clif_cpp_decl, clif_type,
                 &type_selected)) {
    SetUnqualifiedCppType(type_selected, clif_type);
    return kOK;
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
  auto clang_record_decl = reffed_type->getAsCXXRecordDecl();
  // When the output parameter's type is a class type, CLIF checks if the type
  // (reffed_type) is copyable.
  if ((!clang_record_decl) ||
      AreAssignableTypes(reffed_type, clang_record_decl->getLocation(),
                         reffed_type)) {
    return MatchAndSetTypeTop(reffed_type, clif_type);
  }
  // Checks if the output parameter's type(reffed_type) is movable.
  if (clang_record_decl && clang_record_decl->hasDefinition() &&
      ast_->IsClifMovable(clang_record_decl)) {
    if (MatchAndSetMovableType(reffed_type, clif_type) == kOK) return kOK;
    return kParameterMismatch;
  }
  // Output parameters must be either copyable or movable.
  return kUncopyableUnmovableReturnType;
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
    LLVM_DEBUG(llvm::dbgs()
          << "Used ptr conversion for " << clang_type.getAsString());
  }
  if (ast_->IsKnownUniquePtrConversionType(clang_type)) {
    clif_type->set_cpp_touniqptr_conversion(true);
    LLVM_DEBUG(llvm::dbgs()
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

ClifErrorCode ClifMatcher::MatchAndSetMovableType(const QualType& clang_type,
                                                  Type* clif_type) {
  QualType clif_qual_type;
  if (!clif_type->cpp_type().empty()) {
    // Selects the user-specified CLIF cpp type.
    const ClifQualTypes::iterator clif_iter =
        clif_qual_types_.find(clif_type->cpp_type());
    if (clif_iter == clif_qual_types_.end()) {
      return kTypeMismatch;
    }
    clif_qual_type = clif_iter->second.qual_type;

  } else {
    // Selectes the most appropriate CLIF cpp type provided by the automatic
    // type selector.
    if (!SelectTypeWithTypeSelector(clang_type, ClifRetryType::kNonconstNonref,
                                    clif_type, &clif_qual_type)) {
      return kTypeMismatch;
    }
  }
  auto* clang_decl = clang_type->getAsCXXRecordDecl();
  // If all of the below are true, we can use move construction
  // for the return value or output parameters:
  //
  // A) This type is a fully-defined, movable CXXRecord
  // B) The Clif type was found
  // C) The canonical unqualified types are identical.
  if (clang_decl && clang_decl->hasDefinition()) {
    if (!ast_->IsClifMovable(clang_decl)) {
      return kUncopyableUnmovableReturnType;
    }
    if (clif_qual_type.getCanonicalType().getUnqualifiedType() ==
        clang_type.getCanonicalType().getUnqualifiedType()) {
      // Set the return value or output parameter's cpp_type in .opb.
      SetUnqualifiedCppType(clang_type.getUnqualifiedType(), clif_type);
      return kOK;
    }
  }
  return kTypeMismatch;
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
  if (MatchAndSetTypeTop(clang_ret, clif_type_proto, TMF_RETURN_TYPE) == kOK) {
    return kOK;
  }

  auto code = MatchAndSetMovableType(clang_ret, clif_type_proto);
  if (code == kOK || code == kUncopyableUnmovableReturnType) {
    return code;
  }
  return kReturnValueMismatch;
}

// If must_use_reult is true, it means the C++ candidate explicitly declares
// that the return value must be kept.
ClifErrorCode ClifMatcher::MatchAndSetReturnValue(
    const clang::FunctionProtoType* clang_type, FuncDecl* func_decl,
    bool* consumed_return_value, std::string* message, bool must_use_result) {
  const QualType& clang_ret = clang_type->getReturnType();
  assert(!clang_ret->isDependentType());

  *consumed_return_value = false;
  const bool cpp_returns_a_value = !clang_ret->isVoidType();
  if (!cpp_returns_a_value) {
    func_decl->set_cpp_void_return(true);
  } else {
    if (!func_decl->returns().empty()) {
      protos::ParamDecl* return_param = func_decl->mutable_returns(0);
      Type* ret_type = return_param->mutable_type();
      auto code = MatchAndSetReturnType(clang_ret, ret_type);
      if (code != kOK) {
        if (code == kReturnValueMismatch) {
          StrAppend(message, "C++ Return value. ",
                    GetParallelTypeNames());
        }
        return code;
      }
      *consumed_return_value = true;
      return_param->set_cpp_exact_type(clang::TypeName::getFullyQualifiedName(
          clang_ret, ast_->GetASTContext(),
          ast_->GetASTContext().getPrintingPolicy(),
          true /* Include "::" prefix */));
    } else if (must_use_result) {
      // Clif allows users to drop return values if the return value is not
      // required and no output parameters are wrapped.
      return kMustUseResultIgnored;
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
//
// clang_type is a parameter of MatchAndSetSignatures() because when we call
// MatchAndSetCallable(), there is no valid clang_decl, only clang_type
// makes sense. Also callable(eg. std::function) does not have default args, so
// clang_decl is passed in as nullptr in this case.

ClifErrorCode ClifMatcher::MatchAndSetSignatures(
    const clang::FunctionDecl* clang_decl,
    const clang::FunctionProtoType* clang_type, FuncDecl* func_decl,
    std::string* message) {
  bool consumed_return_arg = false;
  bool must_use_result = false;
  if (clang_decl) {
    must_use_result =
        clang_decl->getAttr<clang::WarnUnusedResultAttr>() != nullptr;
  }
  ClifErrorCode code = MatchAndSetReturnValue(
      clang_type, func_decl, &consumed_return_arg, message, must_use_result);
  if (code != kOK) {
    return code;
  }
  // Index into clang_type's list of C++ arguments.
  int cur_arg = 0;
  // Index to the last C++ input arg
  int last_in_arg = 0;
  // Index into params' list of clif parameters.
  int cur_param = 0;
  // Various "+ 1" in the error handling below to match clang
  // one-based numbering when reporting errors.
  int cur_return = consumed_return_arg ? 1 : 0;
  // Record if any default specifier has appeared so far. All required clif
  // parameters must be placed before default arguments.
  bool default_exist = false;

  // Check the input parameters.
  while (cur_arg < clang_type->getNumParams() &&
         cur_param < func_decl->params_size()) {
    const QualType arg_type = clang_type->getParamType(cur_arg);
    protos::ParamDecl* cur_param_decl = func_decl->mutable_params(cur_param);
    cur_param_decl->set_cpp_exact_type(clang::TypeName::getFullyQualifiedName(
        arg_type, ast_->GetASTContext(),
        ast_->GetASTContext().getPrintingPolicy(),
        true /* Include "::" prefix */));
    Type* param_type = cur_param_decl->mutable_type();
    ClifErrorCode code = MatchAndSetInputParamType(arg_type, param_type);
    if (code != kOK) {
      StrAppend(message, "Parameter ", cur_param + 1, ". ",
                GetParallelTypeNames());
      return kParameterMismatch;
    }
    // If clif does not have "default" specifier for this parameter but clang
    // does, we skip clang's default specifier. If clif has "default" specifier
    // for this parameter but clang does not, we report the error
    // kUnexpectedDefaultSpecifier.
    if (!func_decl->params(cur_param).default_value().empty()) {
      if (!clang_decl || !clang_decl->getParamDecl(cur_arg)->hasDefaultArg()) {
        StrAppend(message, GetErrorCodeString(kUnexpectedDefaultSpecifier));
        StrAppend(message, " Clif's param ", cur_param, " \"",
                  param_type->lang_type(), "\"",
                  " contains a default specifier while C++'s param ", cur_arg,
                  " \"", GetQualTypeClifName(arg_type), "\"", " does not.");
        return kUnexpectedDefaultSpecifier;
      } else {
        default_exist = true;
      }
    } else if (default_exist) {
      // Clif does not allow non-default parameters being placed before default
      // arguments.
      StrAppend(message, GetErrorCodeString(kWrongOrderDefault));
      StrAppend(message, " Clif's param ", cur_param, " \"",
                param_type->lang_type(), "\"",
                " does not contain a default specifier while previous params "
                "contain default specifiers.");
      return kWrongOrderDefault;
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
        arg_type, ast_->GetASTContext(),
        ast_->GetASTContext().getPrintingPolicy(),
        true /* Include "::" prefix */));
    Type* param_type = cur_return_decl->mutable_type();
    ClifErrorCode code = MatchAndSetOutputParamType(arg_type, param_type);
    if (code != kOK) {
      StrAppend(message, "Parameter ", cur_param + 1, ". ",
                GetParallelTypeNames());
      if (code == kUncopyableUnmovableReturnType) {
        StrAppend(message, "    Output Parameter Type: \"",
                  GetQualTypeClifName(arg_type), "\" \n");
      }
      return code;
    }
    ++cur_return;
    ++cur_arg;
  }
  // Do we have clif input parameters left unmatched?
  if (last_in_arg != func_decl->params_size()) {
    StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
    StrAppend(message, " Clif declares ", func_decl->params_size(),
              " input parameters. C++ declaration has ", last_in_arg);
    return kParameterCountsDiffer;
  }
  // Do we have clif output parameters left unmatched?
  if (cur_return != func_decl->returns_size()) {
    StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
    StrAppend(message, " Clif declares ", func_decl->returns_size(),
              " output parameters. vs C++ declaration has ", cur_return,
              " (including C++ return value).");
    return kParameterCountsDiffer;
  }
  // Do we have c++ parameter's left unmatched?
  while (cur_arg < clang_type->getNumParams()) {
    // If C++'s current parameter has the default specifier, clif is allowed to
    // skip the current parameter.
    if (clang_decl && clang_decl->getParamDecl(cur_arg)->hasDefaultArg()) {
      cur_arg++;
    } else {
      StrAppend(message, GetErrorCodeString(kParameterCountsDiffer));
      StrAppend(message, " Clif declares ",
                func_decl->params_size() + func_decl->returns_size() -
                    consumed_return_arg,
                " input or output parameters while the C++ declaration has ",
                clang_type->getNumParams(), " parameters.");
      return kParameterCountsDiffer;
    }
  }
  return kOK;
}

bool ClifMatcher::MatchAndSetFunc(FuncDecl* func_decl) {
  // Operator overloading in C++ doesn't map well to other
  // languages--handle it separately.
  if (ast_->IsOperatorOrConversionFunction(func_decl->name().cpp_name())) {
    return MatchAndSetOperatorOrConversion(func_decl);
  }

  // Observe that C++ overloaded functions means we can't use
  // CheckForLookupError here.
  auto clang_decls = ast_->ClifLookup(func_decl->name().cpp_name());
  if (clang_decls.Size() == 0) {
    ClifError error(*this, kNotFound, ast_->GetLookupScopeName());
    error.Report(CurrentDecl());
    return false;
  }
  func_decl->set_is_overloaded(clang_decls.Size() > 1);
  return MatchAndSetFuncFromCandidates(clang_decls, func_decl) != nullptr;
}

bool ClifMatcher::MatchAndSetOperatorOrConversionInContext(
    DeclContext* context, FuncDecl* operator_decl) {
  auto overloads = ast_->LookupOperatorOrConversionFunction(
      context, operator_decl->name().cpp_name());
  if (overloads.Size() > 0) {
    if (auto func_decl =
        MatchAndSetFuncFromCandidates(overloads, operator_decl)) {
      if (llvm::dyn_cast_or_null<clang::CXXMethodDecl>(func_decl) == nullptr) {
        operator_decl->set_cpp_opfunction(true);
      }
      operator_decl->set_is_overloaded(overloads.Size() > 1);
      return true;
    }
  }
  return false;
}

bool ClifMatcher::MatchAndSetOperatorOrConversion(FuncDecl* operator_decl) {
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
    if (MatchAndSetOperatorOrConversionInContext(class_decl, &cur_decl)) {
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
    if (MatchAndSetOperatorOrConversionInContext(class_decl->getParent(),
                                                 &cur_decl)) {
      *operator_decl = cur_decl;
      return true;
    }
  }
  // We only want the first parameter on the working copy of the
  // FunctionDecl, otherwise errors and such get confusing.
  FuncDecl cur_decl = *operator_decl;
  AdjustForNonClassMethods(&cur_decl);
  // Look inside the TU declaration context.
  if (MatchAndSetOperatorOrConversionInContext(ast_->GetTU(), &cur_decl)) {
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
  func_decl->set_is_overloaded(constructors.Size() > 1);
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

  // TODO: ClifError can only store one mismatch error and override
  // the previous error code. We should record all of the mismatch errors and
  // report them together.
  ClifError mismatch_error(*this, kOK);
  for (auto decl : candidates.GetResults()) {
    FuncDecl cur_func_decl = *func_decl;
    const FunctionDecl* clang_decl = nullptr;
    auto* template_decl = CheckDeclType<FunctionTemplateDecl>(decl);
    if (template_decl != nullptr) {
      // Some templates won't specialize properly without the class
      // parameter.
      std::string message;
      clang_decl =
          SpecializeFunctionTemplate(template_decl, &cur_func_decl, &message);
      if (!clang_decl) {
        mismatch_error.SetCode(kUnspecializableTemplate);
        mismatch_error.AddClangDeclAndLocation(ast_.get(), template_decl);
        mismatch_error.AddMessage(message);
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
          // UsingShadowDecl's target decl is the processed candidate we want to
          // match and set. Here target_decl could be any type like FuctionDecl,
          // FunctionTemplateDecl, CXXRecord...
          // We select the FunctionDecl, specialize the FunctionTemplateDecl, or
          // report an error for other types.

          // If UsingShadowDecl does not have a target decl, a clif error is
          // reported.
          if (target_decl == nullptr) {
            llvm::errs() << GetErrorMessageForNonTargetDecl(*using_shadow_decl);
            return nullptr;
          }

          if (llvm::isa<FunctionDecl>(target_decl)) {
            clang_decl = llvm::dyn_cast<FunctionDecl>(target_decl);
          } else if (llvm::isa<FunctionTemplateDecl>(target_decl)) {
            auto* template_decl =
                llvm::dyn_cast<FunctionTemplateDecl>(target_decl);
            std::string message;
            clang_decl = SpecializeFunctionTemplate(template_decl,
                                                    &cur_func_decl, &message);
            if (!clang_decl) {
              mismatch_error.SetCode(kUnspecializableTemplate);
              mismatch_error.AddClangDeclAndLocation(ast_.get(), template_decl);
              mismatch_error.AddMessage(message);
              continue;
            }
          } else {
            // Use the underlying target_decl without using-declaration rather
            // than the initial decl for error reporting.
            decl = target_decl;
          }
        }
        // Report an error if the type of the candidate is not a (template)
        // function. For example, we report an error when the candidate decl is
        // a CXXRecord.
        if (clang_decl == nullptr) {
          ReportTypecheckError<FunctionDecl>(
              decl, func_decl->name().native(), kFunctionNameForError);
          return nullptr;
        }
      }
      // Some FunctionDecl's are children of FunctionTemplateDecls
      // with the same name. These get examined in
      // SpecializeFunctionTemplate, so avoid further handling below.
      if (clang_decl->getDescribedFunctionTemplate() != nullptr &&
          !clang_decl->isFunctionTemplateSpecialization()) {
        continue;
      }
    }

    // Check if the current decl is a member function. If it's not a class
    // member function, the candidates found in separate header files are not
    // valid.

    // We already filter out non-template classes with declarations in different
    // header files in MatchAndSetClass(). So here we only care about non-member
    // functions and member functions of template classes.
    clang::Decl* lookup_scope = ast_->GetCurrentLookupScope();
    if (!clang::isa<clang::CXXRecordDecl>(lookup_scope) &&
        !ImportedFromCorrectFile(*decl, &mismatch_error)) {
      // Ignore certain errors for now. If we don't find any match,
      // these will be listed as failed candidates.
      continue;
    }

    // If the current decl is deleted, skip matching it.
    if (clang_decl->isDeleted()) {
      continue;
    }

    std::string message;
    ClifErrorCode code = MatchAndSetSignatures(
        clang_decl, clang_decl->getType()->getAs<clang::FunctionProtoType>(),
        &cur_func_decl, &message);
    if (code == kOK) {
      // Skipping static function check if the function is an extended
      // classmethod. We define extended classmethods outside of classes,
      // so they are considered non-static by llvm.
      if (!(cur_func_decl.classmethod() && cur_func_decl.is_extend_method())) {
        code = MatchFunctionStatic(clang_decl, cur_func_decl);
      }
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
  } else if (match_decls.size() > 1) {
    for (const auto& decl_pair : match_decls) {
      const clang::FunctionDecl *decl = decl_pair.first;
      if (!decl->isDeprecated()) {
        pruned_decls.emplace_back(decl_pair);
      }
    }
  } else if (mismatch_error.GetCode() == kOK) {
    // Match_decls is empty and there is no mismatch error, indicating that none
    // valid FunctionDecl candidate is passed into MatchAndSetSignatures to
    // match against clang_decl.
    mismatch_error.SetCode(kNotFound);
    mismatch_error.AddMessage(ast_->GetLookupScopeName());
    mismatch_error.AddMessage("Are you wrapping a deleted method?");
  }

  // If multiple decls differ only in the number of consts,
  // take the non-const candidate with the most const parameters.
  if (pruned_decls.size() > 1) {
    typedef std::pair<int, MatchedDecls> ConstCount;
    std::vector<ConstCount> const_count_sorter;
    for (const auto& decl_pair : pruned_decls) {
      const_count_sorter.emplace_back(std::make_pair(0, decl_pair));
      auto* prototype =
          decl_pair.first->getType()->getAs<clang::FunctionProtoType>();
      if (auto* method =
          llvm::dyn_cast_or_null<clang::CXXMethodDecl>(decl_pair.first)) {
        if (!method->isConst()) {
          // In the generated code, we use a pointer to the non-const class
          // object to invoke the candidate method, which invokes the non-const
          // method when there are both const/non-const overloading methods.
          // To make the clif-matcher's behavior aligns with the generated
          // code's, we give higher priority to non-const candiates.
          const_count_sorter.back().first += 100;
        }
      }
      // Non-const methods usually have non-const return values. Add one more
      // check, if the candidate methods are all const/non-const, the ones with
      // const return pointer/reference types are deprecated.
      QualType ret_type = prototype->getReturnType();
      if ((ret_type->isPointerType() || ret_type->isReferenceType()) &&
          ret_type->getPointeeType().isConstQualified()) {
        const_count_sorter.back().first -= 10;
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
      func_decl->set_is_pure_virtual(method_decl->isPure());
    }

    if (auto named_decl = llvm::dyn_cast<clang::NamedDecl>(clang_decl)) {
      std::string mangle_name = GetMangledName(named_decl);
      func_decl->set_mangled_name(mangle_name);
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
      bool is_ptr = clang_param_decl->getType()->isPointerType();
      if (result.Val.isInt() || result.Val.isFloat() || is_ptr) {
        protos::ParamDecl* param_decl = func_decl->mutable_params(i);
        std::string default_value = result.Val.getAsString(
            ast_->GetASTContext(), clang_param_decl->getType());
        // nullptr default value is evaluated as "0" here. We want to represent
        // nullptr default value as "nullptr" in .opb.
        if (is_ptr && default_value == "0") {
          default_value = "nullptr";
        }
        param_decl->set_default_value(default_value);
      }
    }

    return clang_decl;
  } else if (pruned_decls.size() > 1) {
    std::string message;
    // If a constructor matches multiple candidates, users may have forgotten to
    // add the keyword "explicit" for the C++ construtors, which enables
    // unexpected implicit type conversion.
    if (pruned_decls.front().second.constructor()) {
      message =
          "Is the keyword \"explicit\" missed in C++'s definition of "
          "constructors?";
    }
    ReportMultimatchError(*this, ast_.get(), pruned_decls, CurrentDecl(),
                          message);
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

std::string ClifMatcher::GetMangledName(const clang::NamedDecl* clang_decl) {
  std::unique_ptr<clang::MangleContext> mangler(
      clang_decl->getASTContext().createMangleContext());
  if (!mangler->shouldMangleDeclName(clang_decl)) {
    return "";
  }
  std::string buffer;
  llvm::raw_string_ostream buf_stream(buffer);
  if (clang::isa<clang::CXXConstructorDecl>(clang_decl)) {
    auto ctorDecl = llvm::dyn_cast<clang::CXXConstructorDecl>(clang_decl);
    clang::GlobalDecl gd = clang::GlobalDecl(ctorDecl,
                                             clang::Ctor_Complete);
    mangler->mangleName(gd, buf_stream);
  } else if (clang::isa<clang::CXXDestructorDecl>(clang_decl)) {
    auto dtorDecl = llvm::dyn_cast<clang::CXXDestructorDecl>(clang_decl);
    clang::GlobalDecl gd = clang::GlobalDecl(dtorDecl,
                                             clang::Dtor_Complete);
    mangler->mangleName(gd, buf_stream);
  } else {
    mangler->mangleName(clang_decl, buf_stream);
  }
  return buf_stream.str();
}

// Both Clif and Clang typically treat the "this" pointer in a class
// method call as implicit.  However, sometimes (for example, when
// looking for non-class operator overloads) Clif needs it to be
// explicit.
void ClifMatcher::AdjustForNonClassMethods(FuncDecl* clif_decl) const {
  if (clif_decl->cpp_opfunction()) return;  // Already adjusted.
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
    clang::FunctionTemplateDecl* template_decl, FuncDecl* clif_func_decl,
    std::string* message) const {
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

  if (arg_count != templated_decl->getNumParams()) {
    if (arg_count > templated_decl->getNumParams()) {
      StrAppend(message, "Too many CLIF arguments:\n");
    } else {
      StrAppend(message, "Too few CLIF arguments:\n");
    }
    StrAppend(message, kMessageIndent, "  CLIF declares ", arg_count,
              " input or output parameters while C++ declares ",
              templated_decl->getNumParams(), " parameters.\n");
    return nullptr;
  }

  clang::sema::TemplateDeductionInfo info(template_decl->getLocation());
  clang::FunctionDecl* specialized_decl = nullptr;
  // clang::OpaqueValueExpr is not copyable.
  std::deque<clang::OpaqueValueExpr> args;
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
      if (ast_->IsStdSmartPtr(clang_qual_type)) {
        clif_qual_type =
            ast_->BuildTemplateType(
                ast_->GetQualTypeTemplateDecl(clang_qual_type),
                clif_qual_type);
      }
    }
    args.emplace_back(clif_qual_type_iter->second.loc, clif_qual_type,
                      clang::ExprValueKind::VK_LValue);
    arg_ptrs.push_back(&args.back());
  }

  auto specialized_result = ast_->GetSema().DeduceTemplateArguments(
      template_decl,
      nullptr,  // No explicitly listed template arguments.
      arg_ptrs, specialized_decl, info,
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
  StrAppend(message, TemplateDeductionResult(specialized_result), "\n");
  return specialized_decl;
}

std::string ClifMatcher::TemplateDeductionResult(
    Sema::TemplateDeductionResult specialized_result) const {
  switch (specialized_result) {
    case Sema::TDK_Invalid:
      return "The template function declaration was invalid.";
    case Sema::TDK_InstantiationDepth:
      return "Template argument deduction exceeded the maximum template "
             "instantiation depth.";
    case Sema::TDK_Incomplete:
      return "Template argument deduction did not deduce a value for every "
             "template parameter.";
    case Sema::TDK_Inconsistent:
      return "Template argument deduction produced inconsistent deduced "
             "values.";
    case Sema::TDK_Underqualified:
      return "Template argument deduction failed due to inconsistent "
             "cv-qualifiers.";
    default:
      return "";
  }
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

// The return value is a reference to CLIF matcher's clif_to_clang_type_map_,
// which could be passed to the code builder and modify the typemaps.
ClifMatcher::CLIFToClangTypeMap& ClifMatcher::BuildClifToClangTypeMap(
    const AST& clif_ast) {
  for (int typemap_index = 0; typemap_index < clif_ast.typemaps_size();
       typemap_index++) {
    const auto& current_typemap = clif_ast.typemaps(typemap_index);
    if (current_typemap.has_lang_type()) {
      std::vector<std::string> cpp_type_vec;
      cpp_type_vec.reserve(current_typemap.cpp_type_size());
      for (int cpp_type_index = 0;
           cpp_type_index < current_typemap.cpp_type_size(); cpp_type_index++) {
        cpp_type_vec.push_back(current_typemap.cpp_type(cpp_type_index));
      }
      clif_to_clang_type_map_[current_typemap.lang_type()] = cpp_type_vec;
    }
  }
  return clif_to_clang_type_map_;
}

}  // namespace clif
