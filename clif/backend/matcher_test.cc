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

#include "clif/backend/matcher.h"
#include "clif/backend/ast.h"
#include "clif/backend/code_builder.h"
#include "clif/backend/strutil.h"
#include "clif/protos/ast.pb.h"
#include "google/protobuf/text_format.h"
#include "gtest/gtest.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/raw_ostream.h"

#define PROTOBUF_NS google::protobuf


namespace clif {

using clif::TranslationUnitAST;

class ClifMatcherTest : public testing::Test {
 protected:
  void SetUp() override {
    // CLIF_BACKEND_SOURCE_DIR is a preprocessor macro set in CMakeLists.txt.
    test_src_dir_ = CLIF_BACKEND_SOURCE_DIR;
  }

  // We do not do matcher preparation in the SetUp method because:
  // 1. We want to pass an argument to this function.
  // 2. Each run of TestMatch and TestNoMatch should get their own
  //    fresh matcher suitable for the proto they want to match. Hence,
  //    this method will be called repeatedly by a single test (unlike
  //    SetUp which is only called once per test).
  // 3. We want this function to return a DeclList corresponding to the
  //    protos in |proto_list|. The code builder will have made a pass
  //    over the protos in this DeclList. Hence, the C++ type names in the
  //    Decl proto messages of this DeclList will actually be keys to the
  //    corresponding qual types in the matcher's type table.
  DeclList PrepareMatcher(const std::vector<std::string>& proto_list) {
    // We add a dummy decl which only has the cpp_file field set.
    // This cpp_file is the test header file which contains the C++
    // constructs to match.
    std::string clif_ast_proto_text;
    StrAppend(&clif_ast_proto_text,
              "decls: { decltype: UNKNOWN cpp_file: ",
              "'", test_src_dir_, "/test.h'"
              "} ");
    for (const std::string& proto_str : proto_list) {
        StrAppend(&clif_ast_proto_text, "decls: { ", proto_str, " } ");
    }
    EXPECT_TRUE(PROTOBUF_NS::TextFormat::ParseFromString(
        clif_ast_proto_text, &clif_ast_));
    matcher_.reset(new ClifMatcher);
    std::string code = matcher_->builder_.BuildCode(&clif_ast_);
    matcher_->RunCompiler(code,
                          TranslationUnitAST::CompilerArgs(),
                          "clif_temp.cc");
    matcher_->BuildTypeTable();
    DeclList decl_list = clif_ast_.decls();
    // We take out the first decl as it was added only to specify the test
    // header file and does not correspond to the protos in |proto_list|.
    decl_list.erase(decl_list.begin());
    return decl_list;
  }

  void TestMatch(const std::string& proto);
  void TestMatch(const std::string& proto, protos::Decl* decl);
  void TestMatch(const std::vector<std::string>& proto_list, DeclList* decl);
  void TestNoMatch(const std::string& proto);
  void TestNoMatch(const std::string& proto, protos::Decl* decl);

  std::unique_ptr<ClifMatcher> matcher_;
  protos::AST clif_ast_;
  std::string test_src_dir_;
};

TEST_F(ClifMatcherTest, BuildCode) {
  // Be sure we find all the files, and that we don't crash on empty
  // or missing fields.
  std::string proto_string =
      "usertype_includes: 'foo.h'"
      "usertype_includes: 'bar.h' "
      "decls: { decltype: UNKNOWN cpp_file: 'test.h'} "
      "decls: { decltype: CONST cpp_file: '' } "
      "decls: { decltype: VAR } ";
  protos::AST ast_proto;
  EXPECT_TRUE(PROTOBUF_NS::TextFormat::ParseFromString(
      proto_string, &ast_proto));
  matcher_.reset(new ClifMatcher);
  std::string code = matcher_->builder_.BuildCode(&ast_proto);
  EXPECT_TRUE(llvm::StringRef(code).contains("#include \"foo.h\""));
  EXPECT_TRUE(llvm::StringRef(code).contains("#include \"bar.h\""));
  EXPECT_TRUE(llvm::StringRef(code).contains("#include \"test.h\""));
}

void ClifMatcherTest::TestMatch(const std::string& proto) {
  protos::Decl decl;
  TestMatch(proto, &decl);
}

void ClifMatcherTest::TestNoMatch(const std::string& proto) {
  protos::Decl decl;
  TestNoMatch(proto, &decl);
}

void ClifMatcherTest::TestMatch(const std::string& proto, protos::Decl* decl) {
  std::vector<std::string> proto_list(1, proto);
  DeclList decl_list = PrepareMatcher(proto_list);
  SCOPED_TRACE(proto);
  *decl = decl_list.Get(0);
  EXPECT_TRUE(matcher_->MatchAndSetOneDecl(decl));
}

void ClifMatcherTest::TestMatch(const std::vector<std::string>& proto_list,
                                DeclList* decl_list) {
  *decl_list = PrepareMatcher(proto_list);
  EXPECT_EQ(proto_list.size(), decl_list->size());
  for (int i = 0; i < decl_list->size(); ++i) {
    SCOPED_TRACE(proto_list[i]);
    EXPECT_TRUE(matcher_->MatchAndSetOneDecl(decl_list->Mutable(i)));
  }
}

void ClifMatcherTest::TestNoMatch(const std::string& proto,
                                  protos::Decl* decl) {
  std::vector<std::string> proto_list(1, proto);
  DeclList decl_list = PrepareMatcher(proto_list);
  SCOPED_TRACE(proto);
  *decl = decl_list.Get(0);
  EXPECT_FALSE(matcher_->MatchAndSetOneDecl(decl));
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncCplusplusReturnValue) {
  TestMatch("decltype: FUNC func { name { cpp_name: 'FuncReturnsVoid' } }");
  protos::Decl decl;
  TestMatch("decltype: FUNC func { name { cpp_name: 'FuncReturnsInt' } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }", &decl);
  EXPECT_FALSE(decl.func().cpp_void_return());
  EXPECT_TRUE(decl.func().cpp_noexcept());
  TestMatch("decltype: FUNC func {"
            "name { cpp_name: 'FuncReturnsInt' } "
            "ignore_return_value: true "
            " } ", &decl);
  TestMatch("decltype: FUNC func { name {"
            "cpp_name: 'VoidFuncIntPointerParam' }"
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }", &decl);
  EXPECT_FALSE(decl.func().returns(0).type().cpp_raw_pointer());
  EXPECT_TRUE(decl.func().cpp_void_return());
  // Type mismatch check. A function can't match a class
  TestNoMatch("decltype: FUNC func { name {"
              "cpp_name: 'aClass' }"
              "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  // Type mismatch check. A function can't return an int into a class.
  TestNoMatch("decltype: FUNC func { name {"
              "cpp_name: 'FuncReturnsInt' }"
              "returns { type { lang_type: 'aClass' cpp_type: 'aClass' } } }");
  // Check that there is no crash when with a container return value
  // mismatches a C++ plain class.
  TestNoMatch("decltype: FUNC func { name {"
              "cpp_name: 'FuncReturnsInt' }"
              "returns { type { lang_type: 'aClass' "
              "                  cpp_type: 'ComposedType' "
              "                  params { "
              "                    lang_type: 'int' "
              "                    cpp_type: 'int' "
              "} } } }");
  // Type match check. A function can return an int64 into an int.
  TestMatch("decltype: FUNC func { name {"
            "cpp_name: 'FuncReturnsInt64' }"
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  std::string test_proto;
  StrAppend(&test_proto,
            "cpp_file: '", test_src_dir_, "/another_file.h'",
            "decltype: FUNC func { name {cpp_name: 'FuncInAnotherFile' } }");
  TestMatch(test_proto);
  TestNoMatch("cpp_file: 'nonexistent.h' decltype: FUNC func { name {"
            "cpp_name: 'FuncInAnotherFile' } }");

  // Returning a movable but uncopyable type
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'ClassMovableButUncopyable' } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Factory' } "
      "      returns { "
      "        type { "
      "           lang_type: 'ClassMovableButUncopyable' "
      "           cpp_type: 'ClassMovableButUncopyable' "
      "        } "
      "      } "
      "    } "
      "  } "
      "}");
  TestMatch("decltype: FUNC func { "
            "  name { cpp_name: 'FuncReturnsConstIntPtr' } "
            "  returns { "
            "    type { "
            "      lang_type: 'int' "
            "      cpp_type: 'int' "
            "    } "
            "  } "
            "}", &decl);
  EXPECT_EQ(decl.func().returns(0).type().cpp_type(), "const int *");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncReturnOutParam) {
  // Returns in pointer or ref params is ok....
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncIntPointerParam' } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } }"
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestMatch("decltype: FUNC func { "
             "name { cpp_name: 'FuncIntRefParam' } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } }"
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  // ... as long as they are non-const.
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncConstIntPointerParam' } "
              "returns { type { lang_type: 'int' cpp_type: 'int' } }"
              "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncConstIntRefParam' } "
              "returns { type { lang_type: 'int' cpp_type: 'int' } }"
              "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  // Type mismatch check.
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncConstIntRefParam' } "
              "returns { type { lang_type: 'int' cpp_type: 'int' } }"
              "returns { type { lang_type: 'aClass' cpp_type: 'aClass' } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCounts) {
  protos::Decl decl;
  // Parameter count.
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncTwoParams' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncOneReqOneOptParams' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "params { type { lang_type: 'int' cpp_type: 'int' }"
            "         default_value: 'None' } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncOneReqOneOptParams' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncOneReqOneOptParamsReturnsInt' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "params { type { lang_type: 'int' cpp_type: 'int' }"
            "         default_value: 'None' } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncOneReqOneOptParamsReturnsInt' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncOneParams' } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncTwoParams' } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } "
              "params { type { lang_type: 'int' cpp_type: 'int' }"
              "         default_value: 'None' } }");
}

// Input parameter type-checking.  See the comment at
// "MatchAndSetInputParamType" for the different cases.
TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase1) {
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncOneParam' } "
              "params { type { lang_type: 'int' cpp_type: 'int' "
              "                cpp_raw_pointer: true } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase2) {
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncIntPointerParam' } "
            "params { type { lang_type: 'int' cpp_type: 'int' "
            "                cpp_raw_pointer: true } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase3) {
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncIntPointerParam' } "
            "params { type { lang_type: 'int' cpp_type: 'int *' "
            "                cpp_raw_pointer: true } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase4) {
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncOneParam' } "
              "params { type { lang_type: 'int' cpp_type: 'int *' "
              "                cpp_raw_pointer: true } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase5) {
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncOneParam' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } } ");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase6) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncIntPointerParam' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } }",
            &decl);
  EXPECT_TRUE(decl.func().params(0).type().cpp_raw_pointer());
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase7) {
  protos::Decl decl;
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncOneParam' } "
              "params { type { lang_type: 'int' cpp_type: 'int *' } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamCase8) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncIntPointerParam' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } }",
            &decl);
  EXPECT_TRUE(decl.func().params(0).type().cpp_raw_pointer());
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncParamConstRefDropped) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncConstIntRefParam' } "
            "params { type { lang_type: 'int' cpp_type: 'const int &' } } }",
            &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(), "int");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncTemplateParamLValue) {
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncTemplateParamLValue' } "
            "params { type { "
            " lang_type: 'list<int>' "
            "cpp_type: 'ComposedType' "
            "params { "
            "  lang_type: 'int' "
            "  cpp_type: 'int' "
            "} } } } ");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncTemplateParamLValue' } "
              "params { type { "
              " lang_type: 'list<int>' "
              "cpp_type: 'SpecializationsHaveConstructors' "
              "params { "
              "  lang_type: 'int' "
              "  cpp_type: 'int' "
              "} } } } ");
  protos::Decl decl;
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncTemplateParamLValue' } "
              "params { type { "
              " lang_type: 'list<int>' "
              "cpp_type: 'ComposedType' "
              "params { "
              "  lang_type: 'int' "
              "  cpp_type: 'multiparent'   "
              "} } } } ", &decl);
  llvm::errs() << decl.not_found();
  EXPECT_TRUE(llvm::StringRef(decl.not_found()).contains(
      "ComposedType<int>"));
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncNamespaceParam0) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncNamespaceParam' } "
            "params { "
            "  type { lang_type: 'bClass' cpp_type: 'Namespace::bClass' } } }",
            &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(), "::Namespace::bClass");
}

TEST_F(ClifMatcherTest, TestMatchAndSetParamReference) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'const_ref_tests::PassByValue' } "
            "params { type { lang_type: 'ClassB' "
            "                cpp_type: 'const_ref_tests::ClassB' } } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'const_ref_tests::PassByConstRef' } "
            "params { type { lang_type: 'ClassB' "
            "                cpp_type: 'const_ref_tests::ClassB' } } }",
            &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(),
            "::const_ref_tests::ClassB");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'const_ref_tests::PassByRef' } "
              "params { type { lang_type: 'ClassB' "
              "                cpp_type: 'const_ref_tests::ClassB' } } }");
}

TEST_F(ClifMatcherTest, TestReferenceParameters) {
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'VoidFuncNamespaceParam' } "
              "params { type { lang_type: 'bClass' "
              "                cpp_type: 'aClass' } } }");

  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncGloballyQualifiedNamePtrParam' } "
            "params { type { lang_type: 'bClass' "
            "         cpp_type: 'Globally::Qualified::ForwardDecl *' "
            "         cpp_raw_pointer: true } } }",
            &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(),
            "::Globally::Qualified::ForwardDecl *");
}

TEST_F(ClifMatcherTest, TestMatchUncopyableClassParamType) {
  // This test will pass, but the compiler will generate
  // an error because
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncTakesUncopyableClass' } "
              "params { type { lang_type: 'FuncTakesUncopyableClass' "
              "         cpp_type: 'UncopyableClass' } } }");
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncTakesUncopyableClassConstRef' } "
            "params { type { lang_type: 'FuncTakesUncopyableClass' "
            "         cpp_type: 'UncopyableClass' } } }",
            &decl);
  EXPECT_FALSE(decl.func().params(0).type().cpp_has_def_ctor());
  EXPECT_FALSE(decl.func().params(0).type().cpp_copyable());
  EXPECT_FALSE(decl.func().params(0).type().cpp_abstract());
}


TEST_F(ClifMatcherTest, TestMatchSetTypeProperties) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncClassParamWithoutDefaultCtor' } "
            "params { type { lang_type: 'bClass' "
            "                cpp_type: 'ClassWithoutDefaultCtor' } } }",
            &decl);
  EXPECT_FALSE(decl.func().params(0).type().cpp_has_def_ctor());
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncClassParamWithDefaultCtor' } "
            "params { type { lang_type: 'bClass' "
            "                cpp_type: 'ClassWithDefaultCtor' } } }",
            &decl);
  EXPECT_TRUE(decl.func().params(0).type().cpp_has_def_ctor());
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'VoidFuncClassParamWithPrivateDefaultCtor' } "
            "params { type { lang_type: 'bClass' "
            "                cpp_type: "
            "                'ClassWithPrivateDefaultCtor' } } }",
            &decl);
  EXPECT_FALSE(decl.func().params(0).type().cpp_has_def_ctor());
  // Check for cpp_ctor flags.
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'ClassWithDeletedCopyCtor' } "
      "}", &decl);
  EXPECT_FALSE(decl.class_().cpp_copyable());
  EXPECT_FALSE(decl.class_().cpp_abstract());
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'ClassMovableButUncopyable' } "
      "}", &decl);
  EXPECT_FALSE(decl.class_().cpp_copyable());
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'ClassPureVirtual' } "
      "}", &decl);
  EXPECT_TRUE(decl.class_().cpp_has_def_ctor());
  EXPECT_TRUE(decl.class_().cpp_abstract());
  EXPECT_TRUE(decl.class_().cpp_copyable());
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'NoCopyAssign' } "
      "}", &decl);
  EXPECT_FALSE(decl.class_().cpp_copyable());
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'AbstractClass' } "
      "}", &decl);
  EXPECT_TRUE(decl.class_().cpp_abstract());
}

TEST_F(ClifMatcherTest, TestCppAbstract) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncAbstractParam' } "
            "params { type { lang_type: 'ClassPureVirtual' "
            "         cpp_type: 'ClassPureVirtual' } } }", &decl);
  EXPECT_TRUE(decl.func().params(0).type().cpp_abstract());

  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncAbstractParam' } "
            "params { type { lang_type: 'AbstractClass' "
            "         cpp_type: 'AbstractClass' } } }", &decl);
  EXPECT_TRUE(decl.func().params(0).type().cpp_abstract());
}

TEST_F(ClifMatcherTest, TestMatchAndSetTemplateTypes) {
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncTemplateParam' } "
            "params { type { lang_type: 'int' "
            "         cpp_type: 'ComposedType<int>' } } }");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncTemplateParam' } "
              "params { type { lang_type: 'int' "
              "         cpp_type: 'ComposedType<float>' } } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetFuncMulti) {
  // More than one return type...
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncReturnsTwoInts' } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestMatch("decltype: FUNC func { "
            "name { cpp_name: 'FuncTwoParamsTwoReturns' } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "params { type { lang_type: 'int' cpp_type: 'int' } } "
            "returns { type { lang_type: 'int' cpp_type: 'int'  } } "
            "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'FuncReturnsInt' }"
              "returns { type { lang_type: 'int' cpp_type: 'int' } } "
              "returns { type { lang_type: 'int' cpp_type: 'int' } } }");
  protos::Decl decl;
  TestNoMatch("decltype: FUNC func { "
              "name { cpp_name: 'UnwrappableFunction' }"
              "returns { type { lang_type: 'child' cpp_type: 'child' } } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } }", &decl);
  EXPECT_TRUE(llvm::StringRef(decl.not_found()).contains(
      "Do all output parameters follow all input parameters?"));
}

TEST_F(ClifMatcherTest, TestMatchAndSetClass) {
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'DerivedClass' } "
            "members { decltype: FUNC func { constructor: true "
            "   name { cpp_name: 'DerivedClass' } } } "
            "members { decltype: FUNC func { name { cpp_name: 'MemberA' } } } "
            "members { decltype: FUNC func { "
            "  name { cpp_name: 'MemberB' } "
            "  params { type { lang_type: 'int' cpp_type: 'int' } } "
            "  returns { type { lang_type: 'int' cpp_type: 'int' } } }"
            "} }");
  // First with the classmethod field set.
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'aClass' } "
            "members { decltype: FUNC func { "
            "          classmethod: true "
            "          name { cpp_name: 'StaticMember' } } } }");

  // Now without the classmethod field set.
  TestNoMatch("decltype: CLASS class_ { "
              "name { cpp_name: 'aClass' } "
              "members { decltype: FUNC func { "
              "          name { cpp_name: 'StaticMember' } } } }");

  // Globally qualified-name without the classmethod field set should
  // match. (With the classmethod field set should be caught by the
  // parser.)
  TestMatch(" decltype: FUNC func { "
            "          name { cpp_name: 'aClass::StaticMember' } } ");

  // No constructor that takes an int parameter. So this shouldn't
  // match.
  TestNoMatch("decltype: CLASS class_ { "
              "name { cpp_name: 'aClass' } "
              "members { decltype: FUNC func { constructor: true "
              "   name { cpp_name: 'aClass' } "
              "   params { type { lang_type: 'int' cpp_type: 'int' } } } } }");

  // Match against a final class. Unfortunately, the negative case is
  // a compilation error of test.h, which our test harness doesn't
  // support well.
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'aFinalClass' } "
            "members { decltype: FUNC func { "
            "  name { cpp_name: 'Foo' } "
            "  params { type { lang_type: 'aClass' cpp_type: 'aClass' } } } }"
            "final: true } ");
}

TEST_F(ClifMatcherTest, TestMatchAndSetClassTemplates) {
  // Default constructor lookup of non-template class.
  // If this doesn't work, then the test below it won't.
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'AnotherClass' } "
      "  members { decltype: FUNC func { constructor: true "
      "        name { cpp_name: 'AnotherClass' } } } "
      "}");
  // Match a constructor of an explicit template type.
  protos::Decl decl;
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'SpecializationsHaveConstructors<int>' } "
      "  members { decltype: FUNC func { constructor: true "
      "        name { cpp_name: 'SpecializationsHaveConstructors<int>' }"
      "        params { type { lang_type: 'int' cpp_type: 'int' } } } } "
      " } ", &decl);
  EXPECT_EQ(decl.class_().members(0).func().name().cpp_name(),
            "::SpecializationsHaveConstructors<int>::SpecializationsHaveConstructors");
  // Match a constructor of an explicit template type.
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'ComposedType<int>' } "
      "  members { decltype: FUNC func { constructor: true "
      "        name { cpp_name: 'ComposedType<int>' }"
      "        params { type { lang_type: 'int' cpp_type: 'int' } } "
      "} } }");
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'TypedeffedTemplate' } "
      "  members { decltype: FUNC func { constructor: true "
      "        name { cpp_name: 'TypedeffedTemplate' } "
      "        params { type { lang_type: 'int' cpp_type: 'int' } } "
      "} } }");
  TestMatch(
      "decltype: CLASS class_ { "
      "  name { cpp_name: 'ClassTemplateDeclaredInImportedFile' } "
      "  members { decltype: FUNC func { "
      "        name { cpp_name: 'SomeFunction' } "
      "        params { type { lang_type: 'int' cpp_type: 'int' } } "
      "        returns { type { lang_type: 'int' cpp_type: 'int' } } }"
      "} } ");
}

TEST_F(ClifMatcherTest, TestMatchAndSetOperatorOverload) {
  // Global operator, matched outside of class, so no added implicit "this".
  TestMatch("decltype: FUNC func { name {"
            "cpp_name: 'operator==' }"
            "params { type { lang_type: 'int' cpp_type: 'grandmother' } } "
            "params { type { lang_type: 'int' cpp_type: 'grandfather' } } "
            "returns { type { lang_type: 'int' cpp_type: 'bool' } } }");
  // Class operator, no added implicit this.
  protos::Decl decl;
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'OperatorClass' } "
      "members { decltype: FUNC func { name { cpp_name: 'operator==' }  "
      "          returns { type { lang_type: 'int' cpp_type: 'bool' } } "
      "          params { type { lang_type: 'OperatorClass'"
      "                   cpp_type: 'OperatorClass' } } } } }", &decl);
  EXPECT_FALSE(decl.class_().members(0).func().cpp_opfunction());
  // Class operator searched outside of class, so added implicit this.
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'OperatorClass' } "
      "members { decltype: FUNC func { name { cpp_name: 'operator!=' }  "
      "          cpp_opfunction: true "
      "          returns { type { lang_type: 'int' cpp_type: 'bool' } } "
      "          params { type { lang_type: 'OperatorClass'"
      "                   cpp_type: 'OperatorClass' } } }  "
      "} }", &decl);
  EXPECT_TRUE(decl.class_().members(0).func().cpp_opfunction());
  // Operator with fully-qualified name. Must match exactly.
  TestMatch("decltype: FUNC func { name {"
            "cpp_name: 'a_user::defined_namespace::operator==' }"
            "params { type { cpp_type: 'Class' } } "
            "params { type { cpp_type: 'int' } } "
            "returns { type { cpp_type: 'bool' } } }", &decl);
  // Operator with fully-qualified name inside class. Must match exactly.
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'Class' } "
            "members { decltype: FUNC func { name {"
            "  cpp_name: 'a_user::defined_namespace::operator==' }"
            "  params { type { cpp_type: 'Class' } } "
            "  params { type { cpp_type: 'int' } } "
            "  returns { type { cpp_type: 'bool' } } } } }", &decl);
  // Set cpp_opfunction when the match is outside a class.
  EXPECT_TRUE(decl.class_().members(0).func().cpp_opfunction());
}

TEST_F(ClifMatcherTest, TestBaseClassSetter) {
  protos::Decl decl;
  TestMatch("decltype: CLASS class_ { name { cpp_name: 'child' } } ", &decl);
  EXPECT_EQ(decl.class_().bases(0).cpp_name(), "::parent");
  EXPECT_EQ(decl.class_().bases(1).cpp_name(), "::GrandParents::grandparent");
  EXPECT_EQ(decl.class_().bases(2).cpp_name(),
            "::GrandParents::greatgrandparent");
  EXPECT_EQ(decl.class_().cpp_bases(0).name(), "::parent");
  EXPECT_EQ(decl.class_().cpp_bases(1).name(), "::GrandParents::grandparent");
  EXPECT_EQ(decl.class_().cpp_bases(1).namespace_(), "GrandParents");
  EXPECT_EQ(decl.class_().cpp_bases(1).name(), decl.class_().bases(1).cpp_name());
  EXPECT_TRUE(
      llvm::StringRef(decl.class_().cpp_bases(2).filename()).endswith(
          "test.h"));
}

TEST_F(ClifMatcherTest, TestMatchAndSetEnum) {
  // Note that this intentionally omits enumerator 'd' from the test.h
  // declaration. TODO: Check to be sure that the returned
  // proto got the 'd' added.
  TestMatch("decltype: ENUM enum { "
            "name { cpp_name: 'anEnum' native: 'anEnum' } "
            "members { cpp_name: 'a' native: 'a' } "
            "members { cpp_name: 'b' native: 'b' } "
            "members { cpp_name: 'c' native: 'c' } "
            "} namespace_: 'Namespace'");
  // This is a non-class enum.
  TestMatch("decltype: ENUM enum { "
            "name { cpp_name: 'anotherEnum' native: 'anotherEnum' } "
            "members { cpp_name: 'e' native: 'e' } "
            "members { cpp_name: 'f' native: 'f' } "
            "members { cpp_name: 'g' native: 'g' } "
            "} namespace_: 'Namespace'");
  // Everything should match but the 'e'.
  TestNoMatch("decltype: ENUM enum { "
              "name { cpp_name: 'anEnum' native: 'anEnum' } "
              "members { cpp_name: 'a' native: 'a' } "
              "members { cpp_name: 'b' native: 'b' } "
              "members { cpp_name: 'c' native: 'c' } "
              "members { cpp_name: 'e' native: 'e' } "
              "} namespace_: 'Namespace'");
  // Type mismatch check.
  TestNoMatch("decltype: ENUM enum { "
              "name { cpp_name: 'aClass' } "
              "members { cpp_name: 'a' native: 'a' } "
              "members { cpp_name: 'b' native: 'b' } "
              "members { cpp_name: 'c' native: 'c' } "
              "members { cpp_name: 'e' native: 'e' } "
              "}");
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'Namespace::UsingClass' } "
            "members { "
            "decltype: ENUM enum { "
            "name { native: 'some_name' "
            "       cpp_name: 'anEnumHiddenInAUsingDeclaration' } "
            "members { cpp_name: 'a' native: 'a' } "
            "members { cpp_name: 'b' native: 'b' } "
            "members { cpp_name: 'c' native: 'c' } "
            "} } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetVar) {
  // Have to wrap this in a class because clif doesn't support
  // non-class member vars.
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'Namespace::bClass' } "
            "members { "
            "  decltype: VAR var { "
            "    name { cpp_name: 'x' } "
            "    type { cpp_type: 'int' } "
            "} } }");
  // Test a not-found.
  TestNoMatch("decltype: CLASS class_ { "
              "name { cpp_name: 'Namespace::bClass' } "
              "members { "
              "  decltype: VAR var { "
              "    name { cpp_name: 'notfound' } "
              "    type { lang_type: 'float' cpp_type: 'float' } "
              "} } }");
  // // Type mismatch check
  // TestNoMatch("decltype: CLASS class_ { "
  //             "name { cpp_name: 'anEnum' } "
  //             "members { "
  //             "  decltype: VAR var { "
  //             "    name { cpp_name: 'x' } "
  //             "    type { cpp_type: 'int' } "
  //             "} } }");
}

TEST_F(ClifMatcherTest, TestMatchAndSetConst) {
  protos::Decl decl;
  TestMatch("decltype: CONST const { "
            "  name { cpp_name: 'sample' } "
            "  type { cpp_type: 'int' } "
            "}", &decl);
  EXPECT_EQ(decl.const_().name().cpp_name(), "::sample");

  // enum constants
  // builtin type
  TestMatch("decltype: CONST const { "
            "  name { cpp_name: 'e' } "
            "  type { cpp_type: 'int' } "
            "}", &decl);
  EXPECT_EQ(decl.const_().name().cpp_name(), "::Namespace::anotherEnum::e");
  // Non-builtin integer compatible type
  TestMatch("decltype: CONST const { "
            "  name { cpp_name: 'e' } "
            "  type { cpp_type: 'typedeffed_int' } "
            "} namespace_: 'Namespace'", &decl);
  EXPECT_EQ(decl.const_().name().cpp_name(), "::Namespace::anotherEnum::e");
  // incompatible type
  TestNoMatch("decltype: CONST const { "
            "  name { cpp_name: 'e' } "
            "  type { cpp_type: 'string' } "
            "}");

  // class level constants
  TestMatch("decltype: CLASS class_ { "
            "name { cpp_name: 'aClass' } "
            "members { "
            " decltype: CONST const { "
            "  name { cpp_name: 'constant_int' } "
            "  type { lang_type: 'constant_int' cpp_type: 'const int' } "
            " } } "
            "members { "
            " decltype: CONST const { "
            "  name { cpp_name: 'kStringConst' } "
            "  type { lang_type: 'stringconst' cpp_type: 'const char *' } }}"
            "members { "
            " decltype: CONST const { "
            "  name { cpp_name: 'kAnotherStringConst' } "
            "  type { lang_type: 'stringconst' cpp_type: 'const char *' } "
            " } } } ", &decl);
  EXPECT_EQ(decl.class_().members(1).const_().type().cpp_type(),
            "::clif::char_ptr");
  EXPECT_EQ(decl.class_().members(2).const_().type().cpp_type(),
            "::clif::char_ptr");
  // Test a not-found.
  TestNoMatch("decltype: CONST const { "
              "  name { cpp_name: 'notfound' } "
              "  type { lang_type: 'float' cpp_type: 'float' } "
              "}");
  // Type mismatch check
  TestNoMatch("decltype: CONST const { "
              "  name { cpp_name: 'aClass' } "
              "  type { lang_type: 'float' cpp_type: 'float' } "
              "}");
  // nonconst check
  TestNoMatch("decltype: CONST const { "
              "  name { cpp_name: 'simple' } "
              "}");
}

TEST_F(ClifMatcherTest, TestFuncFieldsFilled) {
  // Ensure the cpp_names actually gets the fully-qualified name.
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'int_id' } "
      "returns { type { lang_type: 'int' cpp_type: 'int' } } "
      "params { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().name().cpp_name(), "::some::int_id");
}

TEST_F(ClifMatcherTest, TestClassFieldsFilled) {
  // Ensure the cpp_names actually gets the fully-qualified name.
  protos::Decl decl;
  TestMatch("decltype: CLASS class_ {"
            "name { cpp_name: 'Namespace::bClass' } "
            " } ", &decl);
  EXPECT_EQ(decl.class_().name().cpp_name(), "::Namespace::bClass");
  EXPECT_TRUE(decl.class_().cpp_has_def_ctor());
  TestMatch("decltype: CLASS class_ {"
            "name { cpp_name: 'ClassWithoutDefaultCtor' } "
            "}", &decl);
  EXPECT_FALSE(decl.class_().cpp_has_def_ctor());
  EXPECT_TRUE(decl.class_().cpp_has_public_dtor());
}

TEST_F(ClifMatcherTest, TestPrivateDestructor) {
  protos::Decl decl;
  TestMatch("decltype: CLASS class_ {"
            "name { cpp_name: 'PrivateDestructorClass' } "
            " } ", &decl);
  EXPECT_FALSE(decl.class_().cpp_has_def_ctor());
  EXPECT_FALSE(decl.class_().cpp_has_public_dtor());
}

TEST_F(ClifMatcherTest, TestTypePromotion) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'UnsignedLongLongReturn' } "
      "returns { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().returns(0).type().cpp_type(), "unsigned long long");
  TestNoMatch("decltype: FUNC func {"
              "name { cpp_name: 'TakesBool' } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } "
              " } ");
  TestNoMatch("decltype: FUNC func {"
              "name { cpp_name: 'TakesInt' } "
              "params { type { lang_type: 'bool' cpp_type: 'bool' } } "
              " } ");
  TestNoMatch("decltype: FUNC func {"
              "name { cpp_name: 'TakesFloat' } "
              "params { type { lang_type: 'int' cpp_type: 'int' } } "
              " } ");
  TestNoMatch("decltype: FUNC func {"
              "name { cpp_name: 'TakesPtr' } "
              "params { type { lang_type: 'bool' cpp_type: 'bool' } } "
              " } ");
}

TEST_F(ClifMatcherTest, TestOverloadedCallable) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'OverloadedFunction' } "
      "params { type { "
      "           callable { "
      "             params { type { lang_type: 'char' cpp_type: 'child' } } "
      " } } } } ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.not_found(), "");
  decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'OverloadedFunction' } "
      "params { type { "
      "           callable { "
      "             params { type { lang_type: 'char' cpp_type: 'parent' } } "
      " } } } } ";
  TestNoMatch(decl_proto, &decl);
}

TEST_F(ClifMatcherTest, TestNoModifyInputFQName) {
  protos::Decl decl;
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FunctionWithPartiallyQualifiedDecl' } "
      "params { type { "
      "           lang_type: 'char'"
      "           cpp_type: '::Globally::Qualified::ForwardDecl *' } } "
      " }";
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(),
            "::Globally::Qualified::ForwardDecl *");
}

TEST_F(ClifMatcherTest, TestConstVsNonConstFuncParams) {
  protos::Decl decl;
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FuncConstVsNonConst' } "
      "params { type { "
      "           lang_type: 'int'"
      "           cpp_type: 'int' } } "
      "params { type { "
      "           lang_type: 'int'"
      "           cpp_type: 'int' } } "
      " }";
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(), "int");
  // Make sure we break ties with const methods.
  TestMatch(
      "decltype: CLASS class_ { "
      "name { cpp_name: 'ClassWithDefaultCtor' } "
      "  members: { decltype: FUNC func {"
      "    name { cpp_name: 'MethodConstVsNonConst' } "
      "  } }"
      "}");
}

TEST_F(ClifMatcherTest, TestFunctionTemplate) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'SimpleFunctionTemplateA' } "
      "params { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(), "int");

  decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'PointerArgTemplate' } "
      "params { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.func().params(0).type().cpp_type(), "int *");

  // Composed type passed to a template-deduction argument.
  decl_proto =
      "decltype: FUNC func {"
      "  name { cpp_name: 'SimpleFunctionTemplateA'} "
      "  params { "
      "    type { "
      "       lang_type: 'list<int>' cpp_type: 'ComposedType' "
      "       params { lang_type: 'int' cpp_type: 'int' } "
      "    } } } ";
  TestMatch(decl_proto);

  decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'UndeducableTemplate' } "
      "params { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  TestNoMatch(decl_proto, &decl);
}

TEST_F(ClifMatcherTest, TestClassTemplate) {
  std::string decl_proto = "decltype: CLASS class_ {"
      "name { cpp_name: 'ComposedType<int>' } "
      " } ";
  TestMatch(decl_proto);
}

TEST_F(ClifMatcherTest, TestImplicitConversion) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FunctionWithImplicitConversion' } "
      "params { type { lang_type: 'int' cpp_type: 'Source' } } "
      " } ";
  protos::Decl decl;
  TestNoMatch(decl_proto, &decl);
}

TEST_F(ClifMatcherTest, TestToPtrConversionSet) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FunctionToPtrConversion' } "
      "params { type { lang_type: 'int' cpp_type: 'grandmother' } } "
      "params { type { lang_type: 'int' cpp_type: 'grandmother' } } "
      "params { type { lang_type: 'int' cpp_type: 'grandmother' } } "
      "params { type { lang_type: 'int' cpp_type: 'grandmother*' } } "
      " } ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  // Zero and one-level of indirection should have these fields set,
  // but not more.
  EXPECT_TRUE(decl.func().params(0).type().cpp_toptr_conversion());
  EXPECT_TRUE(decl.func().params(0).type().cpp_touniqptr_conversion());
  EXPECT_TRUE(decl.func().params(1).type().cpp_toptr_conversion());
  EXPECT_TRUE(decl.func().params(1).type().cpp_touniqptr_conversion());
  EXPECT_TRUE(decl.func().params(2).type().cpp_toptr_conversion());
  EXPECT_TRUE(decl.func().params(2).type().cpp_touniqptr_conversion());
  EXPECT_FALSE(decl.func().params(3).type().cpp_toptr_conversion());
  EXPECT_FALSE(decl.func().params(3).type().cpp_touniqptr_conversion());
}

TEST_F(ClifMatcherTest, TestStdSmartPointers) {
  std::string decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FuncUniqPtrToBuiltinTypeArg' } "
      "params { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  protos::Decl decl1;
  TestMatch(decl_proto, &decl1);
  EXPECT_EQ(decl1.func().params(0).type().cpp_type(),
            "::std::unique_ptr<long long>");

  decl_proto = "decltype: FUNC func {"
      "name { cpp_name: 'FuncUniqPtrToBuiltinTypeReturn' } "
      "returns { type { lang_type: 'int' cpp_type: 'int' } } "
      " } ";
  protos::Decl decl2;
  TestMatch(decl_proto, &decl2);
  EXPECT_EQ(decl2.func().returns(0).type().cpp_type(),
            "::std::unique_ptr<long long>");
}

TEST_F(ClifMatcherTest, TestDeprecatedFunctions) {
  std::string decl_proto = "decltype: CLASS class_ {"
      "  name { cpp_name: 'ClassWithDeprecatedMethod' }"
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'MethodWithDeprecatedOverload' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'DeprecatedMethod' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "} ";
  TestMatch(decl_proto);

  decl_proto = "decltype: FUNC func { "
      "  name { cpp_name: 'FunctionWithDeprecatedOverload' } "
      "  params { "
      "    type { "
      "      cpp_type: 'Class'"
      "    } "
      "  } "
      "} ";
  TestMatch(decl_proto);

  decl_proto = "decltype: FUNC func { "
      "  name { cpp_name: 'DeprecatedFunction' } "
      "  params { "
      "    type { "
      "      cpp_type: 'Class'"
      "    } "
      "  } "
      "} ";
  TestMatch(decl_proto);

  decl_proto = "decltype: CLASS class_ {"
      "  name { cpp_name: 'ClassWithDeprecatedMethod' }"
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'DeprecatedMethodWithDeprecatedOverload' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'DeprecatedMethod' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "} ";
  TestNoMatch(decl_proto);
}

TEST_F(ClifMatcherTest, TestCppTypeInParamAndReturnType) {
  std::string decl_proto = "decltype: CLASS class_ {"
      "  name { cpp_name: 'ClassWithQualMethodsAndParams' }"
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Method1' } "
      "      params { "
      "        type { "
      "          cpp_type: 'int'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Method2' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Method3' } "
      "      returns { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Method4' } "
      "      params { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "  members { "
      "    decltype: FUNC func { "
      "      name { cpp_name: 'Method5' } "
      "      params { "
      "        type { "
      "          cpp_type: 'int'"
      "        } "
      "      } "
      "      returns { "
      "        type { "
      "          cpp_type: 'Class'"
      "        } "
      "      } "
      "    } "
      "  } "
      "} ";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
  EXPECT_EQ(decl.class_().members().size(), 5);

  EXPECT_EQ(decl.class_().members(0).func().params(0).cpp_exact_type(),
            "const int");
  EXPECT_FALSE(decl.class_().members(0).func().cpp_const_method());

  EXPECT_EQ(decl.class_().members(1).func().params(0).cpp_exact_type(),
            "const ::Class &");
  EXPECT_FALSE(decl.class_().members(1).func().cpp_const_method());

  EXPECT_EQ(decl.class_().members(2).func().returns(0).cpp_exact_type(),
            "::Class");
  EXPECT_FALSE(decl.class_().members(2).func().cpp_const_method());

  EXPECT_EQ(decl.class_().members(3).func().params(0).cpp_exact_type(),
            "const ::Class &");
  EXPECT_TRUE(decl.class_().members(3).func().cpp_const_method());

  EXPECT_EQ(decl.class_().members(4).func().params(0).cpp_exact_type(),
            "const int");
  EXPECT_EQ(decl.class_().members(4).func().returns(0).cpp_exact_type(),
            "::Class *");
  EXPECT_TRUE(decl.class_().members(4).func().cpp_const_method());
}

TEST_F(ClifMatcherTest, TestDefaultArguments) {
  std::string decl_proto = "decltype: CLASS class_ {"
      " name { cpp_name: 'Class' }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultArg'"
      "       }"
      "       params {"
      "         type {"
      "           cpp_type: 'Arg'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultFlag'"
      "       }"
      "       params {"
      "         name {"
      "           cpp_name: 'f'"
      "         }"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultBoolArgWithoutSideEffects'"
      "       }"
      "       params {"
      "         name {"
      "           cpp_name: 'b'"
      "         }"
      "         type {"
      "           cpp_type: 'bool'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'bool'"
      "         }"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultBoolArgWithSideEffects'"
      "       }"
      "       params {"
      "         name {"
      "           cpp_name: 'b'"
      "         }"
      "         type {"
      "           cpp_type: 'bool'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'bool'"
      "         }"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultNullptr'"
      "       }"
      "       params {"
      "         type {"
      "           cpp_type: 'Arg'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'MethodWithDefaultIntArg'"
      "       }"
      "       params {"
      "         type {"
      "           cpp_type: 'IntArg'"
      "         }"
      "         default_value: 'default'"
      "       }"
      "       returns {"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "       }"
      "     }"
      "   }"
      " }";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);

  EXPECT_EQ(decl.class_().members(0).func().params(0).default_value(),
            "default");
  EXPECT_EQ(decl.class_().members(1).func().params(0).default_value(), "3");
  EXPECT_EQ(decl.class_().members(2).func().params(0).default_value(), "false");
  EXPECT_EQ(decl.class_().members(3).func().params(0).default_value(),
            "default");
  EXPECT_EQ(decl.class_().members(4).func().params(0).default_value(), "0");
  EXPECT_EQ(decl.class_().members(5).func().params(0).default_value(),
            "default");
}

TEST_F(ClifMatcherTest, TestOpaqueClassCapsule) {
  std::string decl_proto = "decltype: TYPE fdecl {"
      "  name {"
      "    cpp_name: 'MyOpaqueClass'"
      "  }"
      "}";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
}

TEST_F(ClifMatcherTest, TestTypedefPtrOutputArg) {
  std::string decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'FuncWithPtrOutputArg'"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'OpaqueClass'"
      "    }"
      "  }"
      "}";
  protos::Decl decl1;
  TestMatch(decl_proto, &decl1);
  EXPECT_EQ(decl1.func().returns(0).type().cpp_type(), "::OpaqueClass *");

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'FuncWithPtrOutputArg'"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'OpaqueClass *'"
      "    }"
      "  }"
      "}";
  protos::Decl decl2;
  TestMatch(decl_proto, &decl2);
  EXPECT_EQ(decl2.func().returns(0).type().cpp_type(), "::OpaqueClass *");
}

TEST_F(ClifMatcherTest, TestFuncWithBaseClassParam) {
  std::string decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'BaseFunctionValue'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'DerivedClass'"
      "    }"
      "  }"
      "}";
  protos::Decl decl1;
  TestMatch(decl_proto, &decl1);
  EXPECT_EQ(decl1.func().params(0).type().cpp_type(), "::DerivedClass");

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'BaseFunctionPtr'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'DerivedClass'"
      "    }"
      "  }"
      "}";
  protos::Decl decl2;
  TestMatch(decl_proto, &decl2);
  EXPECT_EQ(decl2.func().params(0).type().cpp_type(), "::DerivedClass *");

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'BaseFunctionRef'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'DerivedClass'"
      "    }"
      "  }"
      "}";
  protos::Decl decl3;
  TestMatch(decl_proto, &decl3);
  EXPECT_EQ(decl3.func().params(0).type().cpp_type(), "::DerivedClass");

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'BaseFunctionPtr'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'DerivedClass2 *'"
      "    }"
      "  }"
      "}";
  protos::Decl decl4;
  TestMatch(decl_proto, &decl4);
  EXPECT_EQ(decl4.func().params(0).type().cpp_type(), "::DerivedClass2 *");

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'FuncWithUniqPtrToDynamicBaseArg'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'DynamicDerived'"
      "    }"
      "  }"
      "}";
  protos::Decl decl5;
  TestMatch(decl_proto, &decl5);
  EXPECT_EQ(decl5.func().params(0).type().cpp_type(),
            "::std::unique_ptr<::DynamicDerived>");
}

TEST_F(ClifMatcherTest, TestClassWithInheritedConstructor) {
  std::string decl_proto = "decltype: CLASS class_ {"
      " name { cpp_name: 'ClassWithInheritedConstructor' }"
      "   members {"
      "     decltype: FUNC func {"
      "       name {"
      "         cpp_name: 'Method'"
      "       }"
      "     }"
      "   }"
      "   members {"
      "     decltype: FUNC func {"
      "       constructor: true"
      "       params {"
      "         type {"
      "           cpp_type: 'int'"
      "         }"
      "       }"
      "     }"
      "   }"
      " }";
  protos::Decl decl;
  TestMatch(decl_proto, &decl);
}

TEST_F(ClifMatcherTest, TestMultilevelContainer) {
  protos::Decl decl;
  TestMatch("decltype: FUNC func { "
            "  name { cpp_name: 'Clone' } "
            "  params { "
            "    type { "
            "      lang_type: 'list<list<int>>' "
            "      cpp_type: 'ComposedType' "
            "      params { "
            "        lang_type: 'list<int>' "
            "        cpp_type: 'ComposedType' "
            "        params { lang_type: 'int' cpp_type: 'int' }"
            "      } "
            "    } "
            "  } "
            "  returns { "
            "    type { "
            "      lang_type: 'list<list<int>>' "
            "      cpp_type: 'ComposedType' "
            "      params { "
            "        lang_type: 'list<int>' "
            "        cpp_type: 'ComposedType' "
            "        params { lang_type: 'int' cpp_type: 'int' }"
            "      } "
            "    } "
            "  } "
            "} ", &decl);

  EXPECT_EQ(decl.func().params(0).type().cpp_type(),
            "::ComposedType< ::ComposedType<int> >");
  EXPECT_EQ(decl.func().returns(0).type().cpp_type(),
            "::ComposedType< ::ComposedType<int> >");
}

TEST_F(ClifMatcherTest, TestNestedClasses) {
  std::vector<std::string> proto_list;
  proto_list.emplace_back(
      "decltype: CLASS class_ {"
      "  name { cpp_name: 'OuterClass1' }"
      "  members {"
      "    decltype: CLASS class_ { "
      "      name { cpp_name: 'InnerClass' } "
      "      members { "
      "        decltype: VAR var { "
      "          name { cpp_name: 'a' }"
      "          type { cpp_type: 'int' } "
      "        } "
      "      } "
      "    } "
      "  } "
      "} ");
  proto_list.emplace_back(
      "decltype: CLASS class_ {"
      "  name { cpp_name: 'OuterClass2' }"
      "  members {"
      "    decltype: CLASS class_ { "
      "      name { cpp_name: 'InnerClass' } "
      "      members { "
      "        decltype: VAR var { "
      "          name { cpp_name: 'b' }"
      "          type { cpp_type: 'int' } "
      "        } "
      "      } "
      "    } "
      "  } "
      "} ");

  DeclList decl_list;
  TestMatch(proto_list, &decl_list);

  const Decl decl1 = decl_list.Get(0);
  EXPECT_EQ(decl1.class_().name().cpp_name(), "::OuterClass1");
  const ClassDecl inner_class1 = decl1.class_().members(0).class_();
  EXPECT_EQ(inner_class1.name().cpp_name(), "::OuterClass1::InnerClass");
  EXPECT_EQ(inner_class1.members(0).var().name().cpp_name(), "a");

  const Decl decl2 = decl_list.Get(1);
  EXPECT_EQ(decl2.class_().name().cpp_name(), "::OuterClass2");
  const ClassDecl inner_class2 = decl2.class_().members(0).class_();
  EXPECT_EQ(inner_class2.name().cpp_name(), "::OuterClass2::InnerClass");
  EXPECT_EQ(inner_class2.members(0).var().name().cpp_name(), "b");
}

TEST_F(ClifMatcherTest, TestTemplateFuncWithOutputArg) {
  std::string decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'TemplateFuncWithOutputArg1'"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'int'"
      "    }"
      "  }"
      "}";
  protos::Decl decl1;
  TestMatch(decl_proto, &decl1);

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'TemplateFuncWithOutputArg2'"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'float'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'int'"
      "    }"
      "  }"
      "}";
  protos::Decl decl2;
  TestMatch(decl_proto, &decl2);

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'TemplateFuncWithOutputArg3'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'Class'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'int'"
      "    }"
      "  }"
      "}";
  protos::Decl decl3;
  TestMatch(decl_proto, &decl3);

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'TemplateFuncWithOutputArg4'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'Class'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'float'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'int'"
      "    }"
      "  }"
      "}";
  protos::Decl decl4;
  TestMatch(decl_proto, &decl4);

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'TemplateFuncWithOutputArg5'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'Class'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'Class'"
      "    }"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'int'"
      "    }"
      "  }"
      "}";
  protos::Decl decl5;
  TestMatch(decl_proto, &decl5);
}

TEST_F(ClifMatcherTest, VariadicTemplateClass) {
  std::string decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'FuncWithVariadicTemplateClassInput'"
      "  }"
      "  params {"
      "    type {"
      "      cpp_type: 'VariadicTemplateClass'"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "    }"
      "  }"
      "}";
  protos::Decl decl1;
  TestMatch(decl_proto, &decl1);

  decl_proto = "decltype: FUNC func {"
      "  name {"
      "    cpp_name: 'FuncWithVariadicTemplateClassReturn'"
      "  }"
      "  returns {"
      "    type {"
      "      cpp_type: 'VariadicTemplateClass'"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "      params {"
      "        cpp_type: 'int'"
      "      }"
      "    }"
      "  }"
      "}";
  protos::Decl decl2;
  TestMatch(decl_proto, &decl2);
}

}  // namespace clif

