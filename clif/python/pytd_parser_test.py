# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for clif.python.pytd_parser."""

from __future__ import print_function
import textwrap
import pyparsing as pp
import unittest
from clif.python.pytd_parser import *  # pylint: disable=wildcard-import
# pylint: disable=undefined-variable


def Parse(string):
  try:
    return Clif.parseString(string, parseAll=True)
  except:
    print('Line/', '.123456789'*5)
    for n, s in enumerate(string.splitlines()):
      print('%4d:' % (n+1), s)
    raise


class PytdParserTest(unittest.TestCase):

  def setUp(self):
    reset_indentation()

  def EQ(self, t, a, b):
    p = Parse(a) if t is Clif else t.parseString(a, parseAll=True)
    self.assertEqual(p.asList(), b, 'got ' + p.dump())

  def TEQ(self, t, a, k, b):
    p = t.parseString(a, parseAll=True)
    self.assertIn(k, p, 'no "%s" key, got %s' % (k, list(p)))
    self.assertEqual(p[k].asList(), b, 'got ' + p[k].dump())

  def testBasic(self):
    self.EQ(QSTRING, '"abc"', ['abc'])
    self.EQ(ASTRING, '`abc`', ['abc'])
    self.EQ(NAME, ' abc ', ['abc'])
    self.EQ(PARENS(NAME), '( abc )', ['abc'])
    self.EQ(PARENS(pp.delimitedList(NAME)), '( a,b, c )', ['a', 'b', 'c'])
    self.EQ(PARENS(pp.delimitedList(NAME)), '( a,b,\n c)', ['a', 'b', 'c'])

  def testUse(self):
    self.EQ(crename, '`abc` as a.b.c', ['abc', 'a.b.c'])

  def testType(self):
    self.TEQ(type, 'int', 'named', [['int']])
    self.TEQ(type, '`int32` as int', 'named', [['int32', 'int']])
    self.TEQ(type, 'list<int>', 'named', [['list'], [[['int']]]])
    self.TEQ(type, 'list<a, b>', 'named', [['list'], [[['a']]], [[['b']]]])
    self.TEQ(type, '()->list<int>', 'callable',
             [[], [['', [['list'], [[['int']]]]]]])
    self.TEQ(type, '(a:int, b:str) -> int', 'callable',
             [[[['a'], [['int']]], [['b'], [['str']]]], [['', [['int']]]]])
    self.TEQ(type, '`std::function<int ()>` as ()->int', 'callable',
             ['std::function<int ()>', [], [['', [['int']]]]])
    self.TEQ(type, '()->None', 'callable', [[]])
    self.TEQ(type, '()->NoneOr<x>', 'callable',
             [[], [['', [['NoneOr'], [[['x']]]]]]])
    self.TEQ(type, '(x:T)->None', 'callable', [[[['x'], [['T']]]]])
    self.EQ(returns, '->(a:T, b:U)', [[[['a'], [['T']]], [['b'], [['U']]]]])

  def testName(self):
    self.EQ(cname, '`::x` as x', [['::x', 'x']])
    self.EQ(pp.OneOrMore(cname), 'y `::x` as x', [['y'], ['::x', 'x']])
    self.EQ(pp.OneOrMore(cname), 'y`::x` as x', [['y'], ['::x', 'x']])
    self.EQ(pp.OneOrMore(cname), '`::x` as x y', [['::x', 'x'], ['y']])
    self.EQ(pp.OneOrMore(cname+NEWLINE), '`::x` as x\ny',
            [['::x', 'x'], ['y']])

  def testVar(self):
    self.EQ(vardef, 'x : str', ['var', 0, ['x'], [['str']]])
    self.EQ(vardef, '`::x` as x: str', ['var', 0, ['::x', 'x'], [['str']]])
    self.EQ(vardef, 'x : dict<str, String>',
            ['var', 0, ['x'], [['dict'], [[['str']]], [[['String']]]]])
    self.EQ(vardef, 'x: str = property(`A`, `setA`)',
            ['var', 0, ['x'], [['str']], 'A', 'setA'])

  def testFunc(self):
    self.EQ(funcdef, 'def `F` as f()', ['func', 0, [], ['F', 'f'], []])
    self.EQ(funcdef, ' def f(x : str)',
            ['func', 1, [], ['f'], [[['x'], [['str']]]]])
    self.EQ(funcdef, ' def f(x : str=default)',
            ['func', 1, [], ['f'], [[['x'], [['str']], 'default', 15]]])
    self.EQ(funcdef, 'def f() ->(a:int, b:str)',
            ['func', 0, [], ['f'], [], [[['a'], [['int']]], [['b'], [['str']]]]]
           )
    self.EQ(funcdef, 'def f() -> x',
            ['func', 0, [], ['f'], [], [['', [['x']]]]])
    self.EQ(funcdef, 'def f() -> x:\n  return Zx(...)',
            ['func', 0, [], ['f'], [], [['', [['x']]]], [['Zx']]])
    self.EQ(funcdef, 'def f()', ['func', 0, [], ['f'], []])
    self.EQ(funcdef, 'def f(cb: (s: S) -> None)',
            ['func', 0, [], ['f'], [[['cb'], [[[['s'], [['S']]]]]]]])

  def testStaticmethods(self):
    self.EQ(stmeth_stmt, 'staticmethods from `K`:\n def f()',
            ['staticmethods', 0, 'K', [['func', 25, [], ['f'], []]]])

  def testEnum(self):
    self.EQ(enumdef, 'enum x', ['enum', 0, ['x']])
    self.EQ(enumdef, 'enum x with:\n  `A` as a\n  `B` as b\n',
            ['enum', 0, ['x'], [['A', 'a'], ['B', 'b']]])

  def testAlias(self):
    self.EQ(typedef_stmt, 'type x = y', ['type', 0, 'x', [['y']]])

  def testBlock(self):
    self.EQ(BLOCK(NAME), ':\n a\n b\n', [[['a'], ['b']]])

  def testBlock1(self):
    self.EQ(BLOCK(NAME), ':\n a\n\n b\n', [[['a'], ['b']]])

  def testBlockEx(self):
    self.EQ(BLOCK(NAME)-NAME, ':\n a\n b\nc', [[['a'], ['b']], 'c'])

  def testGlobal(self):
    self.EQ(global_decl, 'def f() ->(a:int, b:str)',
            ['func', 0, [], ['f'], [], [[['a'], [['int']]],
                                        [['b'], [['str']]]]])

  def testFromNs1(self):
    self.EQ(from_stmt, 'from "abc":\n  namespace `xyz`:\n    def f()',
            ['from', 0, 'abc',
             [['namespace', 14, 'xyz', [['func', 35, [], ['f'], []]]]]])

  def testFromF1(self):
    self.EQ(from_stmt, 'from "abc":\n  def f()',
            ['from', 0, 'abc', [['func', 14, [], ['f'], []]]])

  def testFromF2(self):
    self.EQ(from_stmt, 'from "abc":\n  enum X with:\n    `A` as a',
            ['from', 0, 'abc', [['enum', 14, ['X'], [['A', 'a']]]]])

  def testFromF21(self):
    self.EQ(Clif, 'from "abc":\n  def f()->None\n  def g(a: int) -> str\n',
            [['from', 0, 'abc',
              [['func', 14, [], ['f'], []],
               ['func', 30, [], ['g'], [[['a'], [['int']]]], [['', [['str']]]]]
              ]]])

  def testFromF22(self):
    self.EQ(Clif, 'from "abc":\n  def f()\nfrom "xyz":\n  def g(a: int)\n',
            [['from', 0, 'abc', [['func', 14, [], ['f'], []]]],
             ['from', 22, 'xyz',
              [['func', 36, [], ['g'], [[['a'], [['int']]]]]]]])

  def testClass(self):
    self.EQ(classdef, 'class Abc:\n  def f(self)',
            ['class', 0, [], ['Abc'], [],
             [['func', 13, [], ['f'], 'self', []]]])
    reset_indentation()
    self.EQ(classdef, 'class Abc(B):\n  def f(self)',
            ['class', 0, [], ['Abc'], [['B']],
             [['func', 16, [], ['f'], 'self', []]]])
    reset_indentation()
    self.EQ(classdef, 'class Abc(A, B):\n  def f(self)',
            ['class', 0, [], ['Abc'], [['A'], ['B']],
             [['func', 19, [], ['f'], 'self', []]]])
    reset_indentation()
    self.EQ(classdef, 'class Abc(`B` as replacement):\n  def f(self)',
            ['class', 0, [], ['Abc'], [['B', 'replacement']],
             [['func', 33, [], ['f'], 'self', []]]])
    reset_indentation()
    # Semantic error in the next test checked in pytd2proto.py.
    self.EQ(classdef, 'class Abc(A, `B` as replacement):\n  def f(self)',
            ['class', 0, [], ['Abc'], [['A'], ['B', 'replacement']],
             [['func', 36, [], ['f'], 'self', []]]])
    reset_indentation()
    self.EQ(classdef, 'class Abc:\n  implements f<x, y>',
            ['class', 0, [], ['Abc'], [],
             [['implements', 13, 'f', 'x', 'y']]])

  def testClassDecorators(self):
    self.EQ(classdef, '@shared\nclass Abc:\n  def f(self)',
            ['class', 0, ['shared'], ['Abc'], [],
             [['func', 21, [], ['f'], 'self', []]]])
    reset_indentation()
    self.EQ(classdef, '@final\nclass Abc:\n  @classmethod\n  def f(cls)',
            ['class', 0, ['final'], ['Abc'], [],
             [['func', 20, ['classmethod'], ['f'], 'cls', []]]])

  def testCapsule0(self):
    self.EQ(capsule_def, 'capsule Abc', ['capsule', 0, ['Abc']])

  def testCapsule(self):
    self.EQ(Clif, 'from "abc":\n  capsule Abc\n  def f(pointer: Abc)',
            [['from', 0, 'abc', [
                ['capsule', 14, ['Abc']],
                ['func', 28, [], ['f'], [[['pointer'], [['Abc']]]]]
                ]]])

  def testImport(self):
    self.EQ(import_stmt, 'from a.b.c import d', ['import', 11, 'a.b.c', 'd'])

  def testImportError(self):
    # Keep feature parity with unittest (avoid assertRaisesWithPredicateMatch).
    with self.assertRaises(pp.ParseException) as exception_ctx:
      self.EQ(import_stmt, 'from "a.b.c"\n capsule d', [])
    self.assertTrue(str(exception_ctx.exception).startswith('Expected name'))
    self.EQ(import_stmt, 'from a.b.c\n import d', ['import', 12, 'a.b.c', 'd'])

  def testInclude(self):
    self.EQ(include_stmt, 'from "a/b" import *', ['include', 0, 'a/b'])
    self.EQ(include_stmt, 'from "a/b" import * as c', ['include', 0, 'a/b', 'c']
           )

  def testInterface(self):
    self.EQ(interface_stmt, 'interface d<T>:\n def f(self, x: T)',
            ['interface', 0, 'd', 'T',
             [['func', 17, [], ['f'], 'self', [[['x'], [['T']]]]]]])

  def testCombined1(self):
    Parse(textwrap.dedent('''\
      from "abc":
        class A:
          enum X with:
            `kOne` as ONE
            `kTwo` as TWO

        def f()
      '''))

  def testCombined2(self):
    Parse(textwrap.dedent('''\
      from "foo.h":
        enum Status

        class Foo:
          `status_` as status: Status
          def Miss(cls, x: int)

      '''))

  def testCombined3(self):
    Parse(textwrap.dedent('''\
      from baz.xyzzy import Plugh
      use `ugh` as ugh

      from "foo.h" import *
      from "bar.h":
        namespace `foo::bar`:
          enum Status

          class Foo:
            `status_` as status: Status

      '''))

if __name__ == '__main__':
  unittest.main()
