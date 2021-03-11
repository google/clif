"""Tests for clif.pybind11.cindex.extractor."""

from absl.testing import absltest
from clif.protos import ast_pb2
from clif.pybind11.cindex import extractor


def gen_func_proto(name, return_type=None, param_types=None):
  func_decl = ast_pb2.Decl()
  func_decl.decltype = ast_pb2.Decl.Type.FUNC
  func_decl.func.name.cpp_name = name
  if return_type:
    func_decl.func.returns.append(ast_pb2.ParamDecl(
        cpp_exact_type=return_type))
  if param_types:
    for param_type in param_types:
      func_decl.func.params.append(ast_pb2.ParamDecl(
          cpp_exact_type=param_type))
  return func_decl


class FunctionTest(absltest.TestCase):
  """Test for extractor.Function object and extractor.Type object."""

  def test_simple_function(self):
    file_content = """
      int func(int a, int b, float c) {
        return 1;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type='int', param_types=['int', 'int', 'float'])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_const_params_and_returns(self):
    file_content = """
      const int func(const int a, const float b) {
        return 1;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type='const int',
        param_types=['const int', 'const float'])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_void_returns(self):
    file_content = """
      void func(int a) {
        return;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto('::func', param_types=['int'])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_reference_params_and_returns(self):
    # Leave empty spaces in type names to test whether we can handle them
    # correctly.
    file_content = """
      const    int func( int  & a,  float  &    b) {
        return 1;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type=' const     int   ',
        param_types=['int   & ', ' float     & '])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_pointer_params_and_returns(self):
    # Leave empty spaces in type names to test whether we can handle them
    # correctly.
    file_content = """
      const int * func( const  int  * a, float  *   b) {
        return nullptr;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type=' const     int   * ',
        param_types=[' const  int   *', ' float     *'])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_object_params_and_returns(self):
    # Leave empty spaces in type names to test whether we can handle them
    # correctly.
    file_content = """
      class A {
      };

      class B {
      };

      const B * func( const  A   & a, const B *  b) {
        return nullptr;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type=' const ::B   * ',
        param_types=[' const  ::A   &', ' const ::B *     '])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)

  def test_multiple_namespaces_params_and_returns(self):
    # Leave empty spaces in type names to test whether we can handle them
    # correctly.
    file_content = """
      namespace a {
        class A {
        };
      }  // namespace a

      namespace b {
      class B {
      };
      namespace c{
      class C {
      };
      }  // namespace c
      }  // namespace b

      const b::c::C * func( const  a::A   & a, const b::B *  b) {
        return nullptr;
      }
    """
    module = extractor.Module.from_source(file_content)
    clang_functions = module.query_func('::func')
    clif_function_decl = gen_func_proto(
        '::func', return_type=' const ::b::c::C   * ',
        param_types=[' const  ::a::A   &', ' const ::b::B *     '])
    clif_function = extractor.Function.from_clif(clif_function_decl)
    self.assertEqual(clang_functions[0], clif_function)


class ExtractorTest(absltest.TestCase):

  def _format_ast_proto(self, ast):
    lines = []
    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.CLASS:
        for member_decl in decl.class_.members:
          if member_decl.decltype == ast_pb2.Decl.Type.FUNC:
            lines.append(
                f'{member_decl.func.name.cpp_name}:'
                f'{len(member_decl.func.params)}:'
                f'is_pure_virtual:{member_decl.func.is_pure_virtual}')
    return '\n'.join(lines) + '\n'

  def test_overloaded_function(self):
    file_content = """
      int func1(int a);
      int func1(float a);
      float func1(float a, float b);
      void func2(int a);
      void func2(int a, int b);
      void func3(int a, int b);
    """
    module = extractor.Module.from_source(file_content)
    candidates = module.query_func('::func1')
    self.assertLen(candidates, 3)
    for candidate in candidates:
      self.assertTrue(candidate.is_overloaded)
    candidates = module.query_func('::func2')
    self.assertLen(candidates, 2)
    for candidate in candidates:
      self.assertTrue(candidate.is_overloaded)
    candidates = module.query_func('::func3')
    self.assertLen(candidates, 1)
    for candidate in candidates:
      self.assertFalse(candidate.is_overloaded)

  def test_multiple_namespaces_overloaded_function(self):
    file_content = """
    namespace a {
      int func1(int a);
      float func1(int a, int b);
      namespace b {
        int func1(float a);
      }
    }  // namespace a
    """
    module = extractor.Module.from_source(file_content)
    candidates = module.query_func('::a::func1')
    self.assertLen(candidates, 2)
    for candidate in candidates:
      self.assertTrue(candidate.is_overloaded)
    candidates = module.query_func('::a::b::func1')
    self.assertLen(candidates, 1)
    for candidate in candidates:
      self.assertFalse(candidate.is_overloaded)

  def test_global_namespace_pure_virtual_function(self):
    file_content = """
      class A {
       public:
        virtual int func1() = 0;
        int func2();
        virtual int func3();
      };

      class B {
       public:
        int func4();
      };
    """
    module = extractor.Module.from_source(file_content)

    self.assertTrue(module.query_func('::A::func1')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::A::func2')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::A::func3')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::B::func4')[0].is_pure_virtual)

  def test_nested_namespace_pure_virtual_function(self):
    file_content = """
      namespace a {
      namespace b {
        class A {
         public:
          virtual int func1() = 0;
          int func2();
          virtual int func3();
        };
      };  // namespace b
      };  // namespace a

      namespace c {
        class B {
         public:
          int func4();
        };
      };  // namespace c
    """
    module = extractor.Module.from_source(file_content)
    self.assertTrue(module.query_func('::a::b::A::func1')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::a::b::A::func2')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::a::b::A::func3')[0].is_pure_virtual)
    self.assertFalse(module.query_func('::c::B::func4')[0].is_pure_virtual)

  def test_overloaded_function_and_pure_virtual(self):
    file_content = """
      class A {
       public:
        virtual int func1() = 0;
        virtual float func1(int a) = 0;
        virtual void func1(int a, int b);
      };
    """
    module = extractor.Module.from_source(file_content)
    candidates = module.query_func('::A::func1')
    self.assertLen(candidates, 3)
    for candidate in candidates:
      if not candidate._arguments:
        self.assertTrue(candidate.is_pure_virtual)
      elif len(candidate._arguments) == 1:
        self.assertTrue(candidate.is_pure_virtual)
      else:
        self.assertFalse(candidate.is_pure_virtual)

  def test_complement_ast(self):
    file_content = """
      namespace a {
        class A {
         public:
          virtual int func1() = 0;
          virtual int func1(int a);
          virtual int func2();
        };
      };  // namespace a
    """
    module = extractor.Module.from_source(file_content)
    ast = ast_pb2.AST()
    class_decl = ast_pb2.Decl()
    class_decl.decltype = ast_pb2.Decl.Type.CLASS
    class_decl.class_.members.append(gen_func_proto('::a::A::func1', 'int'))
    class_decl.class_.members.append(
        gen_func_proto('::a::A::func1', 'int', ['int']))
    class_decl.class_.members.append(gen_func_proto('::a::A::func2', 'int'))
    ast.decls.append(class_decl)
    extractor._complement_matcher_ast(ast, module)
    ast_str = self._format_ast_proto(ast)
    self.assertIn('::a::A::func1:0:is_pure_virtual:True', ast_str)
    self.assertIn('::a::A::func1:1:is_pure_virtual:False', ast_str)
    self.assertIn('::a::A::func2:0:is_pure_virtual:False', ast_str)


if __name__ == '__main__':
  absltest.main()
