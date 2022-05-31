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

#include <string>

#include "gtest/gtest.h"

namespace clif {

using clif::TranslationUnitAST;

class TranslationUnitASTTest : public testing::Test {
 protected:
  void SetUp() override {
    // CLIF_BACKEND_SOURCE_DIR is a preprocessor macro set in CMakeLists.txt.
    std::string test_src = CLIF_BACKEND_SOURCE_DIR;

    std::string code = "#include \"" + test_src + "/test.h\"\n";
    ast_.reset(new TranslationUnitAST());
    bool succeeded = ast_->Init(code,
                                TranslationUnitAST::CompilerArgs(),
                                "clif_temp.cc");
    EXPECT_TRUE(succeeded);
  }
  std::unique_ptr<TranslationUnitAST> ast_;
};

TEST_F(TranslationUnitASTTest, ASTSanityCheck) {
  // Simply dumping the AST is a good sanity check--ask me how I know.
  ast_->Dump();
}

TEST_F(TranslationUnitASTTest, LookupScopedSymbolSimple) {
  EXPECT_EQ(ast_->LookupScopedSymbol("NotFound").Size(), 0);
  EXPECT_EQ(ast_->LookupScopedSymbol("simple").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("Func").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("PolymorphicFunc").Size(), 2);
  EXPECT_EQ(ast_->LookupScopedSymbol("Class").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("Namespace").Size(), 1);
}

TEST_F(TranslationUnitASTTest, LookupScopedSymbolQualified) {
  // Make sure we can find qualified names, and that we only
  // find the copies that we want.
  EXPECT_EQ(ast_->LookupScopedSymbol("Class::Func").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("Class::NotFound").Size(), 0);
  EXPECT_EQ(ast_->LookupScopedSymbol("Namespace::simple").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("Namespace::NotFound").Size(), 0);
  EXPECT_EQ(ast_->LookupScopedSymbol("Namespace::Func").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol("Namespace::Class").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "Namespace::Class::NotFound").Size(), 0);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "Namespace::Class::Func").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "Namespace::Class::PolymorphicFunc").Size(), 2);
  EXPECT_EQ(ast_->LookupScopedSymbol("TypedeffedClass::x").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "ComposedType::FunctionWithTemplatedReturnType").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "TypedeffedTemplate::FunctionWithTemplatedReturnType").Size(), 1);
  EXPECT_EQ(ast_->LookupScopedSymbol(
      "TypedeffedTemplate::FunctionWithTemplatedParameter").Size(), 1);
}

// This should find more instances than above, because some functions
// have the same name, but are declared in multiple namespaces.  This
// should not find class members though.  Also, this test exercises
// the entire DeclClassification mechanism.
TEST_F(TranslationUnitASTTest, LookupUnQualifiedFunction) {
  auto decls = ast_->ClifLookup("NotFound");
  EXPECT_EQ(decls.Size(), 0);
  decls = ast_->ClifLookup("Func");
  EXPECT_EQ(decls.Size(), 2);
  decls = ast_->ClifLookup("::Func");
  EXPECT_EQ(decls.Size(), 1);
  decls = ast_->ClifLookup("PolymorphicFunc");
  EXPECT_EQ(decls.Size(), 2);
  decls = ast_->ClifLookup("::PolymorphicFunc");
  EXPECT_EQ(decls.Size(), 2);
  decls = ast_->ClifLookup("int_id");
  EXPECT_EQ(decls.Size(), 1);
  decls = ast_->ClifLookup("some::int_id");
  EXPECT_EQ(decls.Size(), 1);
}

TEST_F(TranslationUnitASTTest, FindConversionFunctions) {
  EXPECT_EQ(ast_->ptr_conversions_.size(), 4);
  clang::QualType int_type = ast_->FindBuiltinType("int");
  EXPECT_TRUE(ast_->IsKnownPtrConversionType(
      ast_->GetASTContext().getPointerType(int_type)));
  EXPECT_TRUE(ast_->IsKnownUniquePtrConversionType(int_type));
  clang::QualType bool_type = ast_->FindBuiltinType("bool");
  EXPECT_TRUE(ast_->IsKnownPtrConversionType(
      ast_->GetASTContext().getPointerType(bool_type)));
  EXPECT_FALSE(ast_->IsKnownUniquePtrConversionType(
      ast_->GetASTContext().getPointerType(bool_type)));
  clang::QualType float_type = ast_->FindBuiltinType("float");
  EXPECT_FALSE(ast_->IsKnownPtrConversionType(
      ast_->GetASTContext().getPointerType(float_type)));
  EXPECT_FALSE(ast_->IsKnownUniquePtrConversionType(
      ast_->GetASTContext().getPointerType(float_type)));
}

TEST_F(TranslationUnitASTTest, IsStdSmartPtr) {
  clang::QualType int_type = ast_->FindBuiltinType("int");
  EXPECT_FALSE(ast_->IsStdSmartPtr(int_type));

  const auto aliased_template_decls = ast_->LookupScopedSymbol("template_func");
  EXPECT_EQ(aliased_template_decls.Size(), 2);
  {
    const auto f_decl = static_cast<clang::FunctionTemplateDecl*>(
                            aliased_template_decls.GetFirst())
                            ->getTemplatedDecl();
    const auto aliased_template_type = f_decl->getParamDecl(0)->getType();
    EXPECT_FALSE(ast_->IsStdSmartPtr(aliased_template_type));
  }
  {
    const auto f_decl = static_cast<clang::FunctionTemplateDecl*>(
                            aliased_template_decls.GetResults()[1])
                            ->getTemplatedDecl();
    const auto aliased_template_type = f_decl->getParamDecl(0)->getType();
    EXPECT_TRUE(ast_->IsStdSmartPtr(aliased_template_type));
  }
}

}  // namespace clif
