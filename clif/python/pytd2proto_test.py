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

"""Tests for pytd2proto."""

import os
import textwrap
import unittest

from google.protobuf import text_format
from clif.python import pytd2proto
from clif.python import pytd_parser

# The unit tests are run from a build directory outside of the source directory.
# Hence, it is OK to create a file in the build directory only for testing.
TMP_FILE = 'clif_python_pytd2proto_test'


def _ParseFile(pytd, types):
  with open(TMP_FILE, 'w') as pytd_file:
    pytd_file.write(pytd)
  p = pytd2proto.Postprocessor(
      config_headers=types,
      include_paths=[os.environ['CLIF_DIR']])
  with open(TMP_FILE, 'r') as pytd_file:
    pb = p.Translate(pytd_file)
  return pb


def FixTypes(text):
  # If executed with a different defaults for types, text type representation
  # should be fixed here.
  return text


class ToprotoTest(unittest.TestCase):

  def ClifEqual(self,
                pytd,
                clif,
                types=None,
                include_typemaps=False,
                include_namemaps=False,
                add_extra_init=True):
    pytd = textwrap.dedent(pytd)
    try:
      pb = _ParseFile(pytd, types)
    except:
      print('\nLine', '.123456789' * 4)
      for i, s in enumerate(pytd.splitlines()):
        print('%4d:%s\\n' % (i+1, s))
      raise
    if not include_typemaps:
      del pb.typemaps[:]
    if not include_namemaps:
      del pb.namemaps[:]
    for m in pb.macros:
      m.definition = b''
    out = text_format.MessageToString(pb)
    expected = FixTypes(textwrap.dedent(clif))
    if add_extra_init:
      expected += 'extra_init: "PyEval_InitThreads();"\n'
    self.assertMultiLineEqual(out, expected)

  def ClifEqualWithTypes(self, pytd, clif, **kw):
    self.ClifEqual(pytd, clif, types=['clif/python/types.h'], **kw)

  def setUp(self):
    super().setUp()
    pytd_parser.reset_indentation()
    self.maxDiff = 100000  # pylint: disable=invalid-name

  def testOptionIsExtendedFromPythonFalseTrue(self):
    for value in ('False', 'True'):
      pytd = f'OPTION is_extended_from_python = {value}'
      pb = _ParseFile(pytd, None)
      self.assertDictEqual(dict(pb.options), {'is_extended_from_python': value})

  def testUnknownOptionName(self):
    pytd = '\n'.join([
        'OPTION is_extended_from_python=True',
        'OPTION xyz=0'])
    with self.assertRaises(ValueError) as ctx:
      _ParseFile(pytd, None)
    self.assertEqual(str(ctx.exception), 'Unknown OPTION name at line 2: xyz')

  def testDuplicateOptionName(self):
    pytd = '\n'.join([
        'OPTION is_extended_from_python=True',
        '',
        'OPTION is_extended_from_python=False'])
    with self.assertRaises(ValueError) as ctx:
      _ParseFile(pytd, None)
    self.assertEqual(
        str(ctx.exception),
        'Duplicate OPTION name at line 3: is_extended_from_python')

  def testInvalidOptionValue(self):
    pytd = '\n'.join([
        '', '', '',
        '  OPTION  is_extended_from_python  =  1e-5  '])
    with self.assertRaises(ValueError) as ctx:
      _ParseFile(pytd, None)
    self.assertEqual(
        str(ctx.exception),
        'Invalid OPTION value at line 4: 1e-5 (must be False or True)')

  def testParsingNonzeroRaisesNameError(self):
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          namespace `TheNamespace`:
            class `CppAlpha` as Alpha:
              def __nonzero__(self) -> bool
        """, '')

  def testForwardAndCircularTypeUsages(self):
    self.ClifEqualWithTypes("""\
        from "foo.h":
          namespace `TheNamespace`:

            class `CppAlpha` as Alpha:
              def TakeBeta(self, b: list<Beta>)
              def TakeNested(self, n: Beta.Nested)
            class Beta:
              def TakeAlpha(self, a: Alpha)
              class Nested:
                pass
              def GiveNested(self) -> Nested
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 4
          namespace_: "TheNamespace"
          class_ {
            name {
              native: "Alpha"
              cpp_name: "TheNamespace::CppAlpha"
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "TakeBeta"
                  cpp_name: "TakeBeta"
                }
                params {
                  name {
                    native: "b"
                    cpp_name: "b"
                  }
                  type {
                    lang_type: "list<Beta>"
                    cpp_type: "std::vector"
                    params {
                      lang_type: "Beta"
                      cpp_type: "TheNamespace::Beta"
                    }
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 6
              func {
                name {
                  native: "TakeNested"
                  cpp_name: "TakeNested"
                }
                params {
                  name {
                    native: "n"
                    cpp_name: "n"
                  }
                  type {
                    lang_type: "Beta.Nested"
                    cpp_type: "TheNamespace::Beta::Nested"
                  }
                }
              }
            }
          }
        }
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 7
          namespace_: "TheNamespace"
          class_ {
            name {
              native: "Beta"
              cpp_name: "TheNamespace::Beta"
            }
            members {
              decltype: FUNC
              line_number: 8
              func {
                name {
                  native: "TakeAlpha"
                  cpp_name: "TakeAlpha"
                }
                params {
                  name {
                    native: "a"
                    cpp_name: "a"
                  }
                  type {
                    lang_type: "Alpha"
                    cpp_type: "TheNamespace::CppAlpha"
                  }
                }
              }
            }
            members {
              decltype: CLASS
              line_number: 9
              class_ {
                name {
                  native: "Nested"
                  cpp_name: "Nested"
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 11
              func {
                name {
                  native: "GiveNested"
                  cpp_name: "GiveNested"
                }
                returns {
                  type {
                    lang_type: "Nested"
                    cpp_type: "Nested"
                  }
                }
              }
            }
          }
        }
      """)

  def testFromDef(self):
    self.ClifEqualWithTypes("""\
        type str = bytes
        from "some.h":
          def f(a: int, b:()->str) -> list<str>
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: FUNC
          cpp_file: "some.h"
          line_number: 3
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            params {
              name {
                native: "a"
                cpp_name: "a"
              }
              type {
                lang_type: "int"
                cpp_type: "int"
              }
            }
            params {
              name {
                native: "b"
                cpp_name: "b"
              }
              type {
                lang_type: "()->str"
                callable {
                  returns {
                    type {
                      lang_type: "str"
                      cpp_type: "::std::string"
                    }
                  }
                }
              }
            }
            returns {
              type {
                lang_type: "list<str>"
                cpp_type: "std::vector"
                params {
                  lang_type: "str"
                  cpp_type: "::std::string"
                }
              }
            }
          }
        }
      """)

  def testFromDefCallable(self):
    self.ClifEqualWithTypes("""\
        type str = bytes
        from "some.h":
          def f(cb: (a:str)->None)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: FUNC
          cpp_file: "some.h"
          line_number: 3
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            params {
              name {
                native: "cb"
                cpp_name: "cb"
              }
              type {
                lang_type: "(a:str)->None"
                callable {
                  params {
                    name {
                      native: "a"
                      cpp_name: "a"
                    }
                    type {
                      lang_type: "str"
                      cpp_type: "::std::string"
                    }
                  }
                }
              }
            }
          }
        }
      """)

  def testFromDefEmptyCallable(self):
    self.ClifEqual("""\
        from "some.h":
          def f(cb: ()->None)
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: FUNC
          cpp_file: "some.h"
          line_number: 2
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            params {
              name {
                native: "cb"
                cpp_name: "cb"
              }
              type {
                lang_type: "()->None"
                callable {
                  cpp_opfunction: true
                }
              }
            }
          }
        }
      """)

  def testOptional(self):
    self.ClifEqualWithTypes("""\
        type str = bytes
        from "some.h":
          def f(a: str = default)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: FUNC
          cpp_file: "some.h"
          line_number: 3
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            params {
              name {
                native: "a"
                cpp_name: "a"
              }
              type {
                lang_type: "str"
                cpp_type: "::std::string"
              }
              default_value: "default"
            }
          }
        }
      """)

  def testUseAsNewName(self):
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        use `Foo<int>` as foo
        """, '')

  def testUseLastWins(self):
    self.ClifEqualWithTypes("""
        use `FIRST` as dict
        use `SECOND` as dict
        use `FIRST` as dict
        from "foo.h":
          def f() -> dict
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 6
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            returns {
              type {
                lang_type: "dict"
                cpp_type: "FIRST"
              }
            }
          }
        }
      """)

  def testRenameAsNewName(self):
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            def get_a(self) -> (a: `Foo<int>` as foo)
        """, '')

  def testNestedName(self):
    self.ClifEqualWithTypes("""\
        from "foo.h":
          class O:
            class I:
              x: int
              enum IE
          def set_a(a: O.I)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "O"
              cpp_name: "O"
            }
            members {
              decltype: CLASS
              line_number: 3
              class_ {
                name {
                  native: "I"
                  cpp_name: "I"
                }
                members {
                  decltype: VAR
                  line_number: 4
                  var {
                    name {
                      native: "x"
                      cpp_name: "x"
                    }
                    type {
                      lang_type: "int"
                      cpp_type: "int"
                    }
                  }
                }
                members {
                  decltype: ENUM
                  line_number: 5
                  enum {
                    name {
                      native: "IE"
                      cpp_name: "IE"
                    }
                  }
                }
              }
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 6
          func {
            name {
              native: "set_a"
              cpp_name: "set_a"
            }
            params {
              name {
                native: "a"
                cpp_name: "a"
              }
              type {
                lang_type: "O.I"
                cpp_type: "O::I"
              }
            }
          }
        }
      """)

  def testNestedNameWithinNamespace(self):
    self.ClifEqualWithTypes("""\
        from "foo.h":
          namespace `bar`:
            class O:
              class I:
                def __init__(self)
        """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 3
          namespace_: "bar"
          class_ {
            name {
              native: "O"
              cpp_name: "bar::O"
            }
            members {
              decltype: CLASS
              line_number: 4
              class_ {
                name {
                  native: "I"
                  cpp_name: "I"
                }
                members {
                  decltype: FUNC
                  line_number: 5
                  func {
                    name {
                      native: "__init__"
                      cpp_name: "I"
                    }
                    constructor: true
                  }
                }
              }
            }
          }
        }
        """)

  def testNestedNameUsage(self):
    self.ClifEqualWithTypes("""\
        from "foo.h":
          class O:
            enum E
            class I:
              local_i: E
              abs_i: O.E
            local_o: I
            abs_o: O.I
        """, """\
          source: "clif_python_pytd2proto_test"
          usertype_includes: "clif/python/types.h"
          decls {
            decltype: CLASS
            cpp_file: "foo.h"
            line_number: 2
            class_ {
              name {
                native: "O"
                cpp_name: "O"
              }
              members {
                decltype: ENUM
                line_number: 3
                enum {
                  name {
                    native: "E"
                    cpp_name: "E"
                  }
                }
              }
              members {
                decltype: CLASS
                line_number: 4
                class_ {
                  name {
                    native: "I"
                    cpp_name: "I"
                  }
                  members {
                    decltype: VAR
                    line_number: 5
                    var {
                      name {
                        native: "local_i"
                        cpp_name: "local_i"
                      }
                      type {
                        lang_type: "E"
                        cpp_type: "E"
                      }
                    }
                  }
                  members {
                    decltype: VAR
                    line_number: 6
                    var {
                      name {
                        native: "abs_i"
                        cpp_name: "abs_i"
                      }
                      type {
                        lang_type: "O.E"
                        cpp_type: "O::E"
                      }
                    }
                  }
                }
              }
              members {
                decltype: VAR
                line_number: 7
                var {
                  name {
                    native: "local_o"
                    cpp_name: "local_o"
                  }
                  type {
                    lang_type: "I"
                    cpp_type: "I"
                  }
                }
              }
              members {
                decltype: VAR
                line_number: 8
                var {
                  name {
                    native: "abs_o"
                    cpp_name: "abs_o"
                  }
                  type {
                    lang_type: "O.I"
                    cpp_type: "O::I"
                  }
                }
              }
            }
          }
      """)

  def testNestedNameWithDuplicates(self):
    self.ClifEqualWithTypes("""\
        from "foo.h":
          class O1:
            class I:
              x: int
          class O2:
            class I:
              y: int
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "O1"
              cpp_name: "O1"
            }
            members {
              decltype: CLASS
              line_number: 3
              class_ {
                name {
                  native: "I"
                  cpp_name: "I"
                }
                members {
                  decltype: VAR
                  line_number: 4
                  var {
                    name {
                      native: "x"
                      cpp_name: "x"
                    }
                    type {
                      lang_type: "int"
                      cpp_type: "int"
                    }
                  }
                }
              }
            }
          }
        }
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 5
          class_ {
            name {
              native: "O2"
              cpp_name: "O2"
            }
            members {
              decltype: CLASS
              line_number: 6
              class_ {
                name {
                  native: "I"
                  cpp_name: "I"
                }
                members {
                  decltype: VAR
                  line_number: 7
                  var {
                    name {
                      native: "y"
                      cpp_name: "y"
                    }
                    type {
                      lang_type: "int"
                      cpp_type: "int"
                    }
                  }
                }
              }
            }
          }
        }
      """)

  def testImport(self):
    self.ClifEqual(
        """\
      # It's a PYTD comment!
      from "clif/python/types.h" import *

      # def Replacer(a:str, b:str) -> str
      from clif.helpers import Replacer

      use `string_view` as bytes
      type str = bytes
      from "foo.h":
        def f() -> (a:str, b:str):
          return Replacer(...)
        """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 10
          func {
            name {
              native: "f"
              cpp_name: "f"
            }
            returns {
              name {
                native: "a"
                cpp_name: "a"
              }
              type {
                lang_type: "str"
                cpp_type: "string_view"
              }
            }
            returns {
              name {
                native: "b"
                cpp_name: "b"
              }
              type {
                lang_type: "str"
                cpp_type: "string_view"
              }
            }
            postproc: "clif.helpers.Replacer"
          }
        }
        extra_init: "PyEval_InitThreads();"
        namemaps {
          name: "Replacer"
          fq_name: "clif.helpers.Replacer"
        }
        """,
        include_namemaps=True,
        add_extra_init=False)

  def testFromStaticmethods(self):
    self.ClifEqual("""\
      from "foo.h":
        staticmethods from `Bar`:
          def f()
          def g()
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 3
          func {
            name {
              native: "f"
              cpp_name: "::Bar::f"
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 4
          func {
            name {
              native: "g"
              cpp_name: "::Bar::g"
            }
          }
        }
      """)

  def testFromNamespaceStaticmethods(self):
    self.ClifEqual("""\
      from "foo.h":
        namespace `bar`:
          staticmethods from `Bar`:
            def f()
            def g()
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 4
          namespace_: "bar"
          func {
            name {
              native: "f"
              cpp_name: "bar::Bar::f"
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 5
          namespace_: "bar"
          func {
            name {
              native: "g"
              cpp_name: "bar::Bar::g"
            }
          }
        }
      """)

  def testFromNamespace(self):
    self.ClifEqualWithTypes("""\
      from "foo.h":
        namespace `bar`:
          const X: int
          class K:
            def __init__(self, i: int)
            def M(self, i: list<object>)
          enum E
          def F() -> object
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CONST
          cpp_file: "foo.h"
          line_number: 3
          namespace_: "bar"
          const {
            name {
              native: "X"
              cpp_name: "bar::X"
            }
            type {
              lang_type: "int"
              cpp_type: "int"
            }
          }
        }
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 4
          namespace_: "bar"
          class_ {
            name {
              native: "K"
              cpp_name: "bar::K"
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "__init__"
                  cpp_name: "K"
                }
                params {
                  name {
                    native: "i"
                    cpp_name: "i"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                constructor: true
              }
            }
            members {
              decltype: FUNC
              line_number: 6
              func {
                name {
                  native: "M"
                  cpp_name: "M"
                }
                params {
                  name {
                    native: "i"
                    cpp_name: "i"
                  }
                  type {
                    lang_type: "list<object>"
                    cpp_type: "std::vector"
                    params {
                      lang_type: "object"
                      cpp_type: "PyObject*"
                      cpp_raw_pointer: true
                    }
                  }
                }
                py_keep_gil: true
              }
            }
          }
        }
        decls {
          decltype: ENUM
          cpp_file: "foo.h"
          line_number: 7
          namespace_: "bar"
          enum {
            name {
              native: "E"
              cpp_name: "bar::E"
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 8
          namespace_: "bar"
          func {
            name {
              native: "F"
              cpp_name: "bar::F"
            }
            returns {
              type {
                lang_type: "object"
                cpp_type: "PyObject*"
                cpp_raw_pointer: true
              }
            }
            py_keep_gil: true
          }
        }
      """)

  def testFromEmptyClass(self):
    self.ClifEqual("""\
      from a.b.c import Bar
      from "foo.h":
        class Foo(Bar):
          pass
        class Baz:
          pass
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 3
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            bases {
              native: "Bar"
            }
          }
        }
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 5
          class_ {
            name {
              native: "Baz"
              cpp_name: "Baz"
            }
          }
        }
      """)

  def testFromRenamedClass(self):
    self.ClifEqual(
        """\
      from "foo.h":
        class `Foo` as PyFoo:
          pass
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "PyFoo"
              cpp_name: "Foo"
            }
          }
        }
      """)

  def testFromRenamedFQClass(self):
    with self.assertRaises(NameError):
      self.ClifEqual(
          """\
        from "foo.h":
          class `ns::Foo` as PyFoo:
            pass
        """, '')

  def testFromRenamedClassTemplate(self):
    self.ClifEqual(
        """\
      from "foo.h":
        class `Foo<int>` as PyFoo:
          pass
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "PyFoo"
              cpp_name: "Foo<int>"
            }
          }
        }
      """)

  def testFromRenamedClassTemplateWithFQParameter(self):
    self.ClifEqual(
        """\
      from "foo.h":
        class `Foo<ns::Type>` as PyFoo:
          pass
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "PyFoo"
              cpp_name: "Foo<ns::Type>"
            }
          }
        }
      """)

  def testFromClassEnumErrShortName(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo:
            enum Bar
          def get_a(f: Foo) -> Bar
        """, '')

  def testFromClassEnum(self):
    self.ClifEqual("""\
      from "foo.h":
        class Foo:
          enum Bar
        def get_a(f: Foo) -> Foo.Bar
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: ENUM
              line_number: 3
              enum {
                name {
                  native: "Bar"
                  cpp_name: "Bar"
                }
              }
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 4
          func {
            name {
              native: "get_a"
              cpp_name: "get_a"
            }
            params {
              name {
                native: "f"
                cpp_name: "f"
              }
              type {
                lang_type: "Foo"
                cpp_type: "Foo"
              }
            }
            returns {
              type {
                lang_type: "Foo.Bar"
                cpp_type: "Foo::Bar"
              }
            }
          }
        }
      """)

  def testFromClassRightOp(self):
    self.ClifEqualWithTypes("""\
      from "foo.h":
        namespace `userns`:
          class Foo:
            def __radd__(self, other: int) -> int
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 3
          namespace_: "userns"
          class_ {
            name {
              native: "Foo"
              cpp_name: "userns::Foo"
            }
            members {
              decltype: FUNC
              line_number: 4
              func {
                name {
                  native: "__radd__"
                  cpp_name: "operator+"
                }
                params {
                  name {
                    native: "other"
                    cpp_name: "other"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                params {
                  name {
                    native: "self"
                    cpp_name: "this"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "userns::Foo"
                  }
                }
                returns {
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                cpp_opfunction: true
              }
            }
          }
        }
      """)

  def testFromReplacementClassErrExtraCppName(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo(`Bar` as B):
            pass
        """, '')

  def testFromClassErrManyBases(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo(A, B):
            pass
        """, '')

  def testFromReplacemntClassErrManyBases(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo(A, `Bar` as B):
            pass
        """, '')

  def testStrConst(self):
    self.ClifEqualWithTypes("""\
      type str = bytes
      from "foo.h":
        const Foo: str
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CONST
          cpp_file: "foo.h"
          line_number: 3
          const {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            type {
              lang_type: "str"
              cpp_type: "const char *"
            }
          }
        }
      """)

  def testFromClass(self):
    self.ClifEqualWithTypes("""\
      type str = bytes
      from "foo.h":
        class Foo:
          enum Status with:
            `kBad` as BAD
            `kGood` as GOOD
          `status_` as status: Status
          @do_not_release_gil
          def `Find` as f(self, a: dict<str, list<int>>) -> (x:str, y:str)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 3
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: ENUM
              line_number: 4
              enum {
                name {
                  native: "Status"
                  cpp_name: "Status"
                }
                members {
                  native: "BAD"
                  cpp_name: "kBad"
                }
                members {
                  native: "GOOD"
                  cpp_name: "kGood"
                }
              }
            }
            members {
              decltype: VAR
              line_number: 7
              var {
                name {
                  native: "status"
                  cpp_name: "status_"
                }
                type {
                  lang_type: "Status"
                  cpp_type: "Status"
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 8
              func {
                name {
                  native: "f"
                  cpp_name: "Find"
                }
                params {
                  name {
                    native: "a"
                    cpp_name: "a"
                  }
                  type {
                    lang_type: "dict<str, list<int>>"
                    cpp_type: "std::unordered_map"
                    params {
                      lang_type: "str"
                      cpp_type: "::std::string"
                    }
                    params {
                      lang_type: "list<int>"
                      cpp_type: "std::vector"
                      params {
                        lang_type: "int"
                        cpp_type: "int"
                      }
                    }
                  }
                }
                returns {
                  name {
                    native: "x"
                    cpp_name: "x"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                returns {
                  name {
                    native: "y"
                    cpp_name: "y"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                py_keep_gil: true
              }
            }
          }
        }
      """)

  def testFromClassBadInitName(self):
    # TODO: Add check for warning about Init->Foo renaming.
    self.ClifEqualWithTypes("""\
      from "foo.h":
        class Foo:
          def `Init` as __init__(self, a: int)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: FUNC
              line_number: 3
              func {
                name {
                  native: "__init__"
                  cpp_name: "Foo"
                }
                params {
                  name {
                    native: "a"
                    cpp_name: "a"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                constructor: true
              }
            }
          }
        }
      """)

  def testFromClassBadOverload(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo:
            def Bar(self, other: int)
            def Bar(self, other: str)
        """, '')

  def testFromClassBadOps(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo:
            def __iadd__(self, other: int)  # "-> self" missed
        """, '')

  def testFromClassBadROp(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo:
            def __radd__(self, other: int)
            @sequential
            def __getitem__(self, i: int)
        """, '')

  def testFromClassOps(self):
    # TODO: Extend the test to all special names when C++ back is ready
    self.ClifEqualWithTypes("""\
      from "foo.h":
        class Foo:
          def __init__(self, a: int)
          def __eq__(self, other: Foo) -> bool
          def __le__(self, other: Foo) -> bool
          def __bool__(self) -> bool
          def __iadd__(self, other: int) -> self
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: FUNC
              line_number: 3
              func {
                name {
                  native: "__init__"
                  cpp_name: "Foo"
                }
                params {
                  name {
                    native: "a"
                    cpp_name: "a"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                constructor: true
              }
            }
            members {
              decltype: FUNC
              line_number: 4
              func {
                name {
                  native: "__eq__"
                  cpp_name: "operator=="
                }
                params {
                  name {
                    native: "other"
                    cpp_name: "other"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                returns {
                  type {
                    lang_type: "bool"
                    cpp_type: "bool"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "__le__"
                  cpp_name: "operator<="
                }
                params {
                  name {
                    native: "other"
                    cpp_name: "other"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                returns {
                  type {
                    lang_type: "bool"
                    cpp_type: "bool"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 6
              func {
                name {
                  native: "__bool__"
                  cpp_name: "operator bool"
                }
                returns {
                  type {
                    lang_type: "bool"
                    cpp_type: "bool"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 7
              func {
                name {
                  native: "__iadd__"
                  cpp_name: "operator+="
                }
                params {
                  name {
                    native: "other"
                    cpp_name: "other"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                postproc: "->self"
                ignore_return_value: true
              }
            }
          }
        }
      """)

  def testFromClassFreeOps(self):
    self.ClifEqualWithTypes("""\
      from "foo.h":
        class Foo:
          def `::FooEQ` as __eq__(self, other: Foo) -> bool
          def `::FooBool` as __bool__(self) -> bool
          def `::FooSet` as Set(self, key: int, value: int)
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: FUNC
              line_number: 3
              func {
                name {
                  native: "__eq__"
                  cpp_name: "::FooEQ"
                }
                params {
                  name {
                    native: "self"
                    cpp_name: "this"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                params {
                  name {
                    native: "other"
                    cpp_name: "other"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                returns {
                  type {
                    lang_type: "bool"
                    cpp_type: "bool"
                  }
                }
                cpp_opfunction: true
              }
            }
            members {
              decltype: FUNC
              line_number: 4
              func {
                name {
                  native: "__bool__"
                  cpp_name: "::FooBool"
                }
                params {
                  name {
                    native: "self"
                    cpp_name: "this"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                returns {
                  type {
                    lang_type: "bool"
                    cpp_type: "bool"
                  }
                }
                cpp_opfunction: true
              }
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "Set"
                  cpp_name: "::FooSet"
                }
                params {
                  name {
                    native: "self"
                    cpp_name: "this"
                  }
                  type {
                    lang_type: "Foo"
                    cpp_type: "Foo"
                  }
                }
                params {
                  name {
                    native: "key"
                    cpp_name: "key"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                params {
                  name {
                    native: "value"
                    cpp_name: "value"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
                cpp_opfunction: true
              }
            }
          }
        }
      """)

  def testFromClassFQIterErrNotNext(self):
    # It also tests that FQ class name allowed for __iter__ classes.
    with self.assertRaises(SyntaxError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            class `x::a` as __iter__:
              b:int
        """, '')

  def testFromClassDupIterErr(self):
    # It also tests that __iter__ class has only def __next__.
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            class `iter` as __iter__:
              def __next__(self) -> int
            def __iter__(self) -> bytes
        """, '')

  def testFromClassVarErrDupName(self):
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            @getter
            def `a` as get_a(self) -> int
            def get_a(self) -> int
        """, '')

  def testFromClassVarErrPropertySetter(self):
    with self.assertRaises(ValueError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            a: int = property(`get_a`)
            @getter
            def `a` as get_a(self) -> int
        """, '')

  def testFromClassVarErrGetterSignature(self):
    with self.assertRaises(TypeError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            @getter
            def `a` as get_a(self, a: int) -> int
        """, '')

  def testFromClassVarErrSetterSignature(self):
    with self.assertRaises(TypeError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            @setter
            def `a` as set_a(self, a: int) -> int
        """, '')

  def testFromClassVarErrFQName(self):
    with self.assertRaises(NameError):
      self.ClifEqualWithTypes("""\
        from "foo.h":
          class Foo:
            `x::a` as a: int
        """, '')

  def testFromClassVarGetter(self):
    self.ClifEqualWithTypes("""\
      from "foo.h":
        class Foo:
          @getter
          def a(self) -> bool
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 2
          class_ {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
            members {
              decltype: VAR
              line_number: 3
              var {
                name {
                  cpp_name: "a"
                }
                type {
                  lang_type: "bool"
                  cpp_type: "bool"
                }
                cpp_get {
                  name {
                    native: "a"
                  }
                }
              }
            }
          }
        }
      """)

  def testFromClassImplements(self):
    self.ClifEqualWithTypes("""\
      interface Foo<T>:
        value: dict<T>
        def Get(self, n: str) -> T
        def Set(self, n: str, v: T)
        def Copy(self) -> Foo
      type str = bytes
      from "foo.h":
        class FooInt:
          implements Foo<int>
          def Len(self) -> int
        class FooStr:
          implements Foo<bytes>
      """, """\
        source: "clif_python_pytd2proto_test"
        usertype_includes: "clif/python/types.h"
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 8
          class_ {
            name {
              native: "FooInt"
              cpp_name: "FooInt"
            }
            members {
              decltype: VAR
              line_number: 2
              var {
                name {
                  native: "value"
                  cpp_name: "value"
                }
                type {
                  lang_type: "dict<int>"
                  cpp_type: "std::unordered_map"
                  params {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 3
              func {
                name {
                  native: "Get"
                  cpp_name: "Get"
                }
                params {
                  name {
                    native: "n"
                    cpp_name: "n"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                returns {
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 4
              func {
                name {
                  native: "Set"
                  cpp_name: "Set"
                }
                params {
                  name {
                    native: "n"
                    cpp_name: "n"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                params {
                  name {
                    native: "v"
                    cpp_name: "v"
                  }
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "Copy"
                  cpp_name: "Copy"
                }
                returns {
                  type {
                    lang_type: "FooInt"
                    cpp_type: "FooInt"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 10
              func {
                name {
                  native: "Len"
                  cpp_name: "Len"
                }
                returns {
                  type {
                    lang_type: "int"
                    cpp_type: "int"
                  }
                }
              }
            }
          }
        }
        decls {
          decltype: CLASS
          cpp_file: "foo.h"
          line_number: 11
          class_ {
            name {
              native: "FooStr"
              cpp_name: "FooStr"
            }
            members {
              decltype: VAR
              line_number: 2
              var {
                name {
                  native: "value"
                  cpp_name: "value"
                }
                type {
                  lang_type: "dict<bytes>"
                  cpp_type: "std::unordered_map"
                  params {
                    lang_type: "bytes"
                    cpp_type: "::std::string"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 3
              func {
                name {
                  native: "Get"
                  cpp_name: "Get"
                }
                params {
                  name {
                    native: "n"
                    cpp_name: "n"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                returns {
                  type {
                    lang_type: "bytes"
                    cpp_type: "::std::string"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 4
              func {
                name {
                  native: "Set"
                  cpp_name: "Set"
                }
                params {
                  name {
                    native: "n"
                    cpp_name: "n"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "::std::string"
                  }
                }
                params {
                  name {
                    native: "v"
                    cpp_name: "v"
                  }
                  type {
                    lang_type: "bytes"
                    cpp_type: "::std::string"
                  }
                }
              }
            }
            members {
              decltype: FUNC
              line_number: 5
              func {
                name {
                  native: "Copy"
                  cpp_name: "Copy"
                }
                returns {
                  type {
                    lang_type: "FooStr"
                    cpp_type: "FooStr"
                  }
                }
              }
            }
          }
        }
        extra_init: "PyEval_InitThreads();"
        macros {
          name: "Foo"
          definition: ""
        }
        """, add_extra_init=False)

  def testDocString(self):
    self.ClifEqualWithTypes('''\
      from clif.helpers import Replacer
      from "animals.h":
        class Animal:
          """Animal class comment"""
        class DogCat:
          """DogCat
          multiline
          comment"""
          def bark(self) -> None:
            """bark comment"""
          def meow(self) -> int:
            """meow
            multiline"""
            return Replacer(...)
      ''', """\
      source: "clif_python_pytd2proto_test"
      usertype_includes: "clif/python/types.h"
      decls {
        decltype: CLASS
        cpp_file: "animals.h"
        line_number: 3
        class_ {
          name {
            native: "Animal"
            cpp_name: "Animal"
          }
          docstring: "Animal class comment"
        }
      }
      decls {
        decltype: CLASS
        cpp_file: "animals.h"
        line_number: 5
        class_ {
          name {
            native: "DogCat"
            cpp_name: "DogCat"
          }
          members {
            decltype: FUNC
            line_number: 9
            func {
              name {
                native: "bark"
                cpp_name: "bark"
              }
              docstring: "bark comment"
            }
          }
          members {
            decltype: FUNC
            line_number: 11
            func {
              name {
                native: "meow"
                cpp_name: "meow"
              }
              returns {
                type {
                  lang_type: "int"
                  cpp_type: "int"
                }
              }
              postproc: "clif.helpers.Replacer"
              docstring: "meow\\n      multiline"
            }
          }
          docstring: "DogCat\\n    multiline\\n    comment"
        }
      }
    """, add_extra_init=True)


class IncludeTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self._path_prefix = None
    self._cpp_string = 'string'

  def testInclude(self):
    typetable = pytd2proto._TypeTable()
    capsule = {}
    macro = {}
    init = []
    with open(self._path_prefix + '/python/types.h') as t:
      list(pytd2proto._read_include(t, 'fname', '', typetable, capsule, macro,
                                    init))
    self.assertIn(self._cpp_string, typetable.get_last_cpp_type('bytes'),
                  str(typetable))
    self.assertFalse(init)

  def testIncludeAs(self):
    typetable = pytd2proto._TypeTable()
    capsule = {}
    macro = {}
    init = []
    with open(self._path_prefix + '/python/types.h') as t:
      list(pytd2proto._read_include(t, 'fname', 'v.', typetable, capsule, macro,
                                    init))

    actual_cpp_types = typetable.get_last_cpp_type('v.bytes')
    self.assertIn(self._cpp_string, actual_cpp_types, str(typetable))
    self.assertFalse(typetable.has_type('bytes'), str(typetable))
    self.assertFalse(init)


# NOTE: Currently this test is a py_library.
# if __name__ == '__main__':
#   unittest.main()
