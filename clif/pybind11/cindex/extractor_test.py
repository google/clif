"""Tests for clif.pybind11.cindex.extractor."""

from absl.testing import absltest
from clif.protos import ast_pb2
from clif.pybind11.cindex import extractor


class ExtractorTest(absltest.TestCase):

  def _format_ast_proto(self, ast):
    lines = []
    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.CLASS:
        for member_decl in decl.class_.members:
          if member_decl.decltype == ast_pb2.Decl.Type.FUNC:
            lines.append(f'{member_decl.func.name.cpp_name}:is_pure_virtual:'
                         f'{member_decl.func.is_pure_virtual}')
    return '\n'.join(lines) + '\n'

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
    self.assertTrue(module.query_func('::A::func1').func.is_pure_virtual)
    self.assertFalse(module.query_func('::A::func2').func.is_pure_virtual)
    self.assertFalse(module.query_func('::A::func3').func.is_pure_virtual)
    self.assertFalse(module.query_func('::B::func4').func.is_pure_virtual)

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
    self.assertTrue(module.query_func('::a::b::A::func1').func.is_pure_virtual)
    self.assertFalse(module.query_func('::a::b::A::func2').func.is_pure_virtual)
    self.assertFalse(module.query_func('::a::b::A::func3').func.is_pure_virtual)
    self.assertFalse(module.query_func('::c::B::func4').func.is_pure_virtual)

  def test_complement_ast(self):
    file_content = """
      namespace a {
        class A {
         public:
          virtual int func1() = 0;
          virtual int func2();
        };
      };  // namespace a
    """
    module = extractor.Module.from_source(file_content)
    ast = ast_pb2.AST()
    class_decl = ast_pb2.Decl()
    class_decl.decltype = ast_pb2.Decl.Type.CLASS
    func_decl = ast_pb2.Decl()
    func_decl.decltype = ast_pb2.Decl.Type.FUNC
    func_decl.func.name.cpp_name = '::a::A::func1'
    class_decl.class_.members.append(func_decl)
    func_decl = ast_pb2.Decl()
    func_decl.decltype = ast_pb2.Decl.Type.FUNC
    func_decl.func.name.cpp_name = '::a::A::func2'
    class_decl.class_.members.append(func_decl)
    ast.decls.append(class_decl)
    ast = extractor._complement_matcher_ast(ast, module)
    ast_str = self._format_ast_proto(ast)
    self.assertIn('::a::A::func1:is_pure_virtual:True', ast_str)
    self.assertIn('::a::A::func2:is_pure_virtual:False', ast_str)


if __name__ == '__main__':
  absltest.main()
