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
// C++ declarations for clif backend tests.  Not necessarily Google
// style compliant nor ever actually compiled into object code.

#ifndef CLIF_BACKEND_TEST_H_
#define CLIF_BACKEND_TEST_H_

#include <stdint.h>
// These are all declared in the same file to make lookup inside the
// TU complicated enough to be convincing.

// Declarations for testing TranslationUnitAST.

int simple;
const int sample = 0;

void Func();

void PolymorphicFunc(int x);
void PolymorphicFunc(char *x);

class aClass;

class aClass {
 public:
  static constexpr char kStringConst[] = "abcdefg";
  static constexpr char kAnotherStringConst[] = {'a', 'b'};
  int x;
  const int constant_int = 1;
  static void StaticMember();
 private:
  int y;
 protected:
  int z;
};

typedef aClass TypedeffedClass;

class aFinalClass final : public aClass {
  void Foo(aClass a);
};


enum Enum {
  E1 = 321,
  E2 = 432,
  E3 = 543
};

enum Flag {
  F1 = 1,
  F2 = 2,
  F3 = 4,
  F5 = 8
};

struct Arg {
  Enum e;
};

class IntArg {
 public:
  int a;
  operator int() {
    return a;
  }
};

class Class {
 public:
  int MethodWithDefaultArg(Arg arg = { EnumValue });
  int MethodWithDefaultIntArg(IntArg arg = (IntArg){ 100 });
  int MethodWithDefaultNullptr(const Arg* arg = nullptr);
  int MethodWithDefaultFlag(int flag = F1 | F2);
  bool MethodWithDefaultBoolArgWithSideEffects(bool b = BoolFunc() || true);
  bool MethodWithDefaultBoolArgWithoutSideEffects(bool b = false);
  bool MethodWithoutDefaultArg(int input);
  void MethodWithDefaultArgs(int input = 0, int* output = nullptr);
  static bool BoolFunc();
  void Func();
  void MemberA();
  void PolymorphicFunc(int x);
 private:
  static const Enum EnumValue;
};

const Enum Class::EnumValue = E2;

class AbstractClass {
 public:
  virtual void Func() = 0;
};


class DerivedClass : public Class {
 public:
  DerivedClass() { }
  int MemberB(int x);
  void PolymorphicFunc(void *y);
};

class DerivedClass2 : public Class { };

void BaseFunctionValue(Class c);
void BaseFunctionPtr(Class* c);
void BaseFunctionRef(const Class& c);

namespace Namespace {

int simple;

void Func();

class Class {
 public:
  void Func();
  void PolymorphicFunc(int x);
  void PolymorphicFunc(void *y);
};

class bClass {
 public:
  int x;
};

enum class anEnum { a, b, c, d };
enum anotherEnum { e, f, g, h};

typedef int typedeffed_int;

// Class to test using clauses outside the namespace.
class UsingClass {
 public:
  int x;
  using anEnumHiddenInAUsingDeclaration = anEnum;
};

}  // namespace Namespace

namespace Globally {
namespace Qualified {
class ForwardDecl;
}
void FunctionWithPartiallyQualifiedDecl(Qualified::ForwardDecl* d);
}  // namespace Globally
void FuncGloballyQualifiedNamePtrParam(
    const ::Globally::Qualified::ForwardDecl* c);

namespace some {
int int_id(int x);

}  // namespace some

//
using Namespace::UsingClass;

// Declarations for testing ClifMatcher

// Tests for return type
// The return value can not be ignored.
__attribute__((warn_unused_result)) int FuncWithMustUseReturn();
void FuncReturnsVoid();
int FuncReturnsInt() noexcept;
int64_t FuncReturnsInt64();
float FuncReturnsFloat();
void VoidFuncIntPointerParam(int *x);
int FuncIntPointerParam(int *x);
int FuncIntRefParam(int &x); // NOLINT
int FuncReturnsTwoInts(int *x);
const int* FuncReturnsConstIntPtr();
const Class* FuncReturnsConstClassPtr();
const int FuncReturnsConstInt();
const Class FuncReturnsConstClass();

// Test for implicit conversion between clif type and clang type.
// If the implicit conversion between types involves adding pointers,
// clif_matcher fails.
struct ImplicitConvertTo {};

class ImplicitConvertFrom1 {
 public:
  operator ImplicitConvertTo*();
};

void FuncImplicitConversion1(ImplicitConvertTo* a);

// If the implicit conversion between types does not involve pointers,
// clif_matcher passes.
class ImplicitConvertFrom2 {
 public:
  operator ImplicitConvertTo();
};

void FuncImplicitConversion2(ImplicitConvertTo a);

// Test for const and non-const overloading methods.
class ConstOverloading {
 public:
  const int* FuncConstOverloading() const;
  int* FuncConstOverloading();
};

namespace std {
template< typename T > class shared_ptr;
}

std::shared_ptr<const Class> FuncReturnsSmartPtrOfConstClass();
std::shared_ptr<const int> FuncReturnsSmartPtrOfConstInt();

// tests for parameter counts
void FuncOneParam(int x);
void FuncTwoParams(int x, int y);
void FuncOneReqOneOptParams(int x, int y = 0);
int FuncOneReqOneOptParamsReturnsInt(int x, int y = 0);
int FuncTwoParamsTwoReturns(int x, int y, int* z);

// More parameter checking
void VoidFuncConstIntRefParam(const int &x);
void VoidFuncNamespaceParam(const Namespace::bClass b);

void FuncConstVsNonConst(const int&x, const int& y);
void FuncConstVsNonConst(const int&x, int& y);  // NOLINT

// Be sure that we describe the presence of a default ctor accurately.
class ClassWithDefaultCtor {
 public:
  ClassWithDefaultCtor() { }
  void MethodConstVsNonConst() const;
  void MethodConstVsNonConst();
};
void VoidFuncClassParamWithDefaultCtor(ClassWithDefaultCtor c);
class ClassWithoutDefaultCtor {
 public:
  ClassWithoutDefaultCtor(int x) { } // NOLINT
};
void VoidFuncClassParamWithoutDefaultCtor(ClassWithoutDefaultCtor c);
void VoidFuncClassParamWithDefaultCtor(ClassWithDefaultCtor c);
class ClassWithPrivateDefaultCtor {
 private:
  ClassWithPrivateDefaultCtor(int x) { } // NOLINT
};
void VoidFuncClassParamWithPrivateDefaultCtor(ClassWithPrivateDefaultCtor c);
class ClassWithDeletedCopyCtor {
 public:
  ClassWithDeletedCopyCtor(const ClassWithDeletedCopyCtor&) = delete;
  explicit ClassWithDeletedCopyCtor(const ClassWithDeletedCopyCtor*);
  void DeletedFunc() = delete;
};

class ClassMovableButUncopyable {
 public:
  // Delete copy-constructor and copy assignment operator.
  ClassMovableButUncopyable(const ClassMovableButUncopyable&) = delete;
  ClassMovableButUncopyable& operator=(const ClassMovableButUncopyable&) =
      delete;

  // Ensure move-constructor and move assignment operator exist.
  ClassMovableButUncopyable(ClassMovableButUncopyable&&) = default;
  ClassMovableButUncopyable& operator=(ClassMovableButUncopyable&&) = default;

  // Tests for movable but uncopyable return values.
  ClassMovableButUncopyable Factory();
  ClassMovableButUncopyable* FactoryPointer();
  ClassMovableButUncopyable& FactoryRef();
  const ClassMovableButUncopyable& FactoryConstRef();

  // Tests for movable but uncopyable output parameters.
  void FuncMovableButUncopyableOutputParam(ClassMovableButUncopyable*);
  void FuncMovableButUncopyableOutputParamNonPtr(ClassMovableButUncopyable);
  void FuncMovableButUncopyableOutputParamConstPtr(
      const ClassMovableButUncopyable*);
};

class UncopyableUnmovableClass {
 public:
  explicit UncopyableUnmovableClass(int x);
  UncopyableUnmovableClass(const UncopyableUnmovableClass& other) = delete;
  UncopyableUnmovableClass(UncopyableUnmovableClass&& other) = delete;
};

void FuncUncopyableClassInputParam(UncopyableUnmovableClass uc);
void FuncUncopyableClassConstRefInputParam(const UncopyableUnmovableClass& uc);
void FuncUncopyableUnmovableClassOutputParam(UncopyableUnmovableClass* uc);
UncopyableUnmovableClass FuncUncopyableUnmovableClassReturnType();

class ClassPureVirtual {
 public:
  virtual void SomeFunction() = 0;
  virtual void NotPureVirtual();
};

class ClassOverridesPureVirtual: public ClassPureVirtual {
 public:
  void SomeFunction() override;
};

void SomeFunctionNotPureVirtual();
void FuncAbstractParam(const ClassPureVirtual* x);
void FuncAbstractParam(const AbstractClass& x);
void FuncForwardDeclared(const Globally::Qualified::ForwardDecl* x);

// tests to be sure we don't match a return in const param.
void FuncConstIntPointerParam(const int *x);
void FuncConstIntRefParam(const int &x);

class AnotherClass { public: void Foo(); };

template<typename T> class SpecializationsHaveConstructors {
 public:
  SpecializationsHaveConstructors(T t);
};

template<class T>
class ComposedType : public AnotherClass{
 public:
  T t;
  ComposedType(int x);
  T FunctionWithTemplatedReturnType();
  void FunctionWithTemplatedParameter(const T t);
};

typedef ComposedType<int> TypedeffedTemplate;

void FuncTemplateParam(ComposedType<int> x);
void FuncTemplateParamLValue(const ComposedType<int>& x);
template <typename A>
void SimpleFunctionTemplate(A x);
template <typename A>
void FunctionTemplateConst(const A x);
template<typename A, typename B> void UndeducableTemplate(A x);
template<typename A> void PointerArgTemplate(A* x);
ComposedType<ComposedType<int>> Clone(const ComposedType<ComposedType<int>>);

namespace GrandParents {

class greatgrandparent {};
class grandparent : public virtual greatgrandparent {};
}  // namespace GrandParents

using GrandParents::greatgrandparent;
using GrandParents::grandparent;

class parent : public grandparent {};
class child : public parent {};

class base1_1 {};
class base1_2 {};
class base2_1 {};

class base1 : public base1_1, private base1_2 {};
class base2 : virtual public base2_1 {};
class base3 : virtual public base2_1 {};

class derive1 : public base1, private base2 {};
// Virtual diamond inheritance for regular classes.
class derive2 : public base2, public base3 {};

// Virtual diamond inheritance for template classes.
template <class T>
class base4 {};

template <class T>
class base5 : virtual public base4<T> {};

template <class T>
class base6 : virtual public base4<T> {};

template <class T>
class derive3 : public base5<T>, public base6<T> {};

using derive3_int = derive3<int>;

// Non-virtual diamond inheritance will lead to an error.
class base7 : public base2_1 {};
class base8 : public base2_1 {};
class derive4 : public base7, public base8 {};


class grandfather {};
class grandmother {};
class multiparent : public grandfather, public grandmother {};
class multichild : public multiparent {};

// Smart pointers are tested by clif/testing/python:all,
// because this file doesn't have the full C++ compilation
// environment, and we want to avoid that dependency here anyway.
// std::unique_ptr<child> unique_ptr_child;

// Output parameter before input parameter.
void UnwrappableFunction(child* y, int z);

class PrivateDestructorClass {
 private:
  ~PrivateDestructorClass() {}
};

class NoCopyAssign {
  int a_;
  NoCopyAssign& operator=(const NoCopyAssign&) = delete;
 public:
  explicit NoCopyAssign(int a = 0) : a_(a) {}
  int A() { return a_; }
};

unsigned long long UnsignedLongLongReturn();  // NOLINT[runtime/int]
void TakesBool(bool x);
void TakesInt(int x);
void TakesFloat(float x);
void TakesPtr(int* x);

// Global operator overload.
bool operator==(const grandmother& gm, const grandfather& gp);

// Local operator overload
class OperatorClass {
 public:
  bool operator==(const OperatorClass&);
  bool operator==(const int&);
};

// Overload to be found by global lookup even though Clif defines it
// in a class. (cpp_opfunction)
int operator*(const OperatorClass&);
int operator*(int, const OperatorClass&);

class OperatorClass2 {
  int operator*() const { return 1; }
};

bool operator!=(const OperatorClass&, const OperatorClass&);

namespace user {
class OperatorClass3 {
  int operator*(int) const { return 1; }
};
int operator*(int, const OperatorClass3&) { return 2; }
}  // namespace user
int operator+(int, const user::OperatorClass3&) { return 0; }

class ConversionClass {
 public:
  operator bool() const { return false; }
  operator int() const { return 0; }
};

// Hack because we don't have a complete compilation environment here.
namespace std {
template< class > class function;
template< class R, class... Args > class function<R(Args...)>;

template< typename T > class unique_ptr;
}

class DynamicBase {
 public:
  virtual ~DynamicBase();
};

class DynamicDerived : public DynamicBase {};

DynamicBase* FuncWithBaseReturnValue();
void FuncWithBaseParam(DynamicBase*);

void FuncUniqPtrToBuiltinTypeArg(std::unique_ptr<long long int>);  // NOLINT [runtime/int]
std::unique_ptr<long long int> FuncUniqPtrToBuiltinTypeReturn();  // NOLINT [runtime/int]
void FuncWithUniqPtrToDynamicBaseArg(std::unique_ptr<DynamicBase>);

class OpaqueClass;
typedef OpaqueClass* MyOpaqueClass;
void FuncWithPtrOutputArg(MyOpaqueClass* opaque);

template <typename T>
void TemplateFuncWithOutputArg1(T* t);
template <typename T>
float TemplateFuncWithOutputArg2(T* t);
template <typename T>
void TemplateFuncWithOutputArg3(const T& t, int* i);
template <typename T>
float TemplateFuncWithOutputArg4(const T& t, int* i);
template <typename T>
T TemplateFuncWithOutputArg5(const T& t, int* i);

namespace example {
template <typename Real>
class Vector {};
template <class ObjectType>
class ObjectTypeHolder {
 public:
  typedef ObjectType T;
  void FailTerribly(ObjectTypeHolder<T>* other);
};
}  // namespace example

class ClassWithQualMethodsAndParams {
 public:
  void Method1(const int a);

  void Method2(const Class& s);

  Class Method3();

  void Method4(const Class& s) const;

  void Method5(const int a, Class* s) const;
};

class ClassWithDeprecatedMethod {
 public:
  void MethodWithDeprecatedOverload(Class& c);  // NOLINT

  __attribute__((deprecated("A deprecated method")))
  void MethodWithDeprecatedOverload(Class* c);

  __attribute__((deprecated("A deprecated method")))
  void DeprecatedMethod(Class* c);

  __attribute__((deprecated("A deprecated method")))
  void DeprecatedMethodWithDeprecatedOverload(Class* c);

  __attribute__((deprecated("A deprecated method")))
  void DeprecatedMethodWithDeprecatedOverload(Class& c);  // NOLINT
};

void OverloadedFunction(int x);
void OverloadedFunction(std::function<void(child)> x);
// Use templates with callable arguments as input parameters for functions.
void CallableTemplateArgFunction(
    example::Vector<std::function<void(child, int)>> x);
void CallableTemplateArgFunction2(
    example::Vector<std::function<child()>> x);
void CallableTemplateArgFunction3(
    example::Vector<std::function<int(child)>> x);
// Use templates with callable arguments as output parameters for functions.
void CallableTemplateArgFunction4(
    example::Vector<std::function<void(int)>>* x);
// Use templates with callable arguments as return values for functions.
example::Vector<std::function<void(int)>> CallableTemplateArgFunction5();

void FunctionWithDeprecaredOverload(Class& c);  // NOLINT

__attribute__((deprecated("A deprecated function")))
void FunctionWithDeprecatedOverload(Class* c);

__attribute__((deprecated("A deprecated function")))
void DeprecatedFunction(Class* c);

void FunctionToPtrConversion(grandmother g0,
                             grandmother& g1,  // NOLINT
                             grandmother* g2,
                             grandmother** g3);

class ClassWithNonDefaultConstructor {
 public:
  explicit ClassWithNonDefaultConstructor(int i);

 protected:
  void Method();
};

template <typename T = int>
class set {};
template <typename T>
using clif_set = set<>;

void func_template_alias_set_input(set<> s);
void func_template_alias_set_output(set<>* s);
set<> func_template_alias_set_return();
void func_template_unique_ptr(set<std::unique_ptr<int>> s);

template <typename value, typename T = int>
class map {};
template <typename K, typename V>
using clif_map = map<V>;

template <typename T>
void template_func(clif_map<T, T> s);

template <typename T>
using clif_shared_ptr = std::shared_ptr<T>;

template <typename T>
void template_func(clif_shared_ptr<T> s);

void func_template_alias_map(map<int> s);

class ClassWithInheritedConstructor : public ClassWithNonDefaultConstructor {
 public:
  using ClassWithNonDefaultConstructor::ClassWithNonDefaultConstructor;
  using ClassWithNonDefaultConstructor::Method;
};

class ClassWithTemplateFunctions {
 public:
  template <typename T>
  explicit ClassWithTemplateFunctions(T i);

  class NestClass {};

  template <typename T>
  void Method(T i);
};

class ClassUsingInheritedTemplateFunctions : public ClassWithTemplateFunctions {
 public:
  using ClassWithTemplateFunctions::ClassWithTemplateFunctions;
  using ClassWithTemplateFunctions::Method;
  using ClassWithTemplateFunctions::NestClass;
};

class ClassWithNonExplicitConstructor {
 public:
  ClassWithNonExplicitConstructor(const int& i);
};

class OuterClass1 {
 public:
  class InnerClass {
   public:
    int a;
  };
};

class OuterClass2 {
 public:
  class InnerClass {
   public:
    int b;
  };
};

template <typename... T>
class VariadicTemplateClass {};

void FuncWithVariadicTemplateClassInput(
    const VariadicTemplateClass<int, int, int>& v);
VariadicTemplateClass<int, int, int> FuncWithVariadicTemplateClassReturn();

// Preprocessor directive to test inclusions from another file.
#line 100 "another_file.h"

namespace clif {
// Conversion function matcher ignores type of first argument.
void PyObjAs(int x, int **y);
void PyObjAs(int x, grandfather **y);
}  // namespace clif

namespace a_user {
namespace defined_namespace {
void Clif_PyObjAs(int x, bool **y);
void Clif_PyObjAs(int x, grandmother **y);
void Clif_PyObjAs(int x, std::unique_ptr<int>* g);
void Clif_PyObjAs(int x, std::unique_ptr<grandmother>* g);

bool operator==(const Class& x, int);

}  // namespace defined_namespace
}  // namespace a_user

// Instantiation of template class declared in a separate file can be matched.
template<typename T> class ClassTemplateInAnotherFile {
 public:
  ClassTemplateInAnotherFile() {}
  T* SomeFunction(T t);
};

class ClassInAnotherFile {
 public:
  int SomeFunction(int t);
};

namespace const_ref_tests {

class ClassB { };

class ClassA {
 public:
  ClassA(const ClassB& other) { }
};

void PassByValue(ClassA ls);
void PassByConstRef(const ClassA& ls);
void PassByRef(ClassA& ls);  //NOLINT [runtime/reference]
}  // namespace const_ref_tests


// Preprocessor directive to get back to the original file.
#line 300 "test.h"

// Instantiation of template class with non-class template parameters.
typedef ClassTemplateInAnotherFile<int> ClassTemplateDeclaredInImportedFile;
ClassTemplateDeclaredInImportedFile f;

// Instantiation of template class with class template parameters.
typedef ClassTemplateInAnotherFile<AnotherClass>
    ClassTemplateDeclaredInImportedFile2;

typedef std::function<void(int)> SimpleCallback;
// functions with non const & std::function parameters
void FunctionSimpleCallbackNonConstRef(int input, SimpleCallback callback);
// function with const & std::function parameters
void FunctionSimpleCallbackConstRef(int input, const SimpleCallback& callback);

// Test the automatic type selector for matching integer types(lang_type: int).
class TypeSelectInt {
 public:
  char x_0;
  signed char x_1;
  unsigned char x_2;

  int x_3;
  short x_4;
  long x_5;
  long long x_6;

  unsigned int x_7;
  unsigned short x_8;
  unsigned long x_9;
  unsigned long long x_10;
};

// Test the automatic type selector for matching floating types(lang_type: float).
class TypeSelectFloat {
 public:
  float x_0;
  double x_1;
};

// Artificially make the string candidate C++ types.
namespace std {
class clif_string {
 public:
  clif_string(const char* char_string) {}
};
}  // namespace std

class clif_string {};

namespace absl {
class Cord {};
class string_view {};
}  // namespace absl

// Test the automatic type selector for matching bytes types(lang_type: bytes).
class TypeSelectBytes {
 public:
  std::clif_string x_0;
  ::clif_string x_1;
  absl::Cord x_2;
  absl::string_view x_3;
};

// Test the automatic type selector for matching function's input/output parameters and returns.
class TypeSelectFunctionTypes {
 public:
  int Func(float p1, absl::Cord* p2);
};

// Test the automatic type selector for matching pointer types.
class TypeSelectTypePointers {
 public:
  double* x_0;
  int* Func(float* p1, absl::Cord* p2);
};

// Test the automatic type selector for matching const types.
class TypeSelectConstTypes {
 public:
  const float x_0;
  const double* x_1;
  static constexpr char kStringConst[] = "abcdefg";
  const int& FuncConstRefReturn(const float p1, const float& p2,
                                const absl::Cord* p3);
  const int* FuncConstPtrReturn();
};

template <int>
class ClassWithIntegralTemplateParam {};

typedef ClassWithIntegralTemplateParam<3> ClassWithIntegralTemplateParam3;

ComposedType<ClassWithIntegralTemplateParam3>
FuncReturnComposedIntegralTemplate();

void FuncWithIntegralTemplateType(ClassWithIntegralTemplateParam3 param);
void FuncWithIntegralTemplateTypeRef(
    const ClassWithIntegralTemplateParam3& param);

namespace absl {
template <typename T>
class StatusOr {
 public:
  StatusOr(const T&);
};
}  // namespace absl

absl::StatusOr<int> StatusOrIntReturn();

template<int N>
struct Primary { };

template<int N>
using AliasForPrimary = Primary<N>;

struct AliasForPrimary5 : AliasForPrimary<5> { };

#endif  // CLIF_BACKEND_TEST_H_
