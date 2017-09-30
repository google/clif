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

"""Tests for clif.python.pytd2proto."""

from __future__ import print_function
import os
import textwrap
from google.protobuf import text_format
import unittest
from clif.python import pytd2proto
from clif.python import pytd_parser

# The unit tests are run from a build directory outside of the source directory.
# Hence, it is OK to create a file in the build directory only for testing.
TMP_FILE = 'clif_python_pytd2proto_test'


class ToprotoTest(unittest.TestCase):

  def ClifEqual(self, pytd, clif, types=None,
                include_typemaps=False, add_extra_init=True):
    pytd = textwrap.dedent(pytd)
    with open(TMP_FILE, 'w') as pytd_file:
      pytd_file.write(pytd)
    p = pytd2proto.Postprocessor(
        config_headers=types,
        include_paths=[os.environ['CLIF_DIR']])
    with open(TMP_FILE, 'r') as pytd_file:
      try:
        pb = p.Translate(pytd_file)
      except:
        print('\nLine', '.123456789' * 4)
        for i, s in enumerate(pytd.splitlines()):
          print('%4d:%s\\n' % (i+1, s))
        raise
    if not include_typemaps:
      del pb.typemaps[:]
    for m in pb.macros:
      m.definition = b''
    out = text_format.MessageToString(pb)
    expected = textwrap.dedent(clif).replace(
        'cpp_type: "string"', 'cpp_type: "std::string"')
    if add_extra_init:
      expected += 'extra_init: "PyEval_InitThreads();"\n'
    self.assertMultiLineEqual(out, expected)

  def ClifEqualWithTypes(self, pytd, clif, **kw):
    self.ClifEqual(pytd, clif, types=['clif/python/types.h'], **kw)

  def setUp(self):
    pytd_parser.reset_indentation()

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
                      cpp_type: "string"
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
                  cpp_type: "string"
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
                      cpp_type: "string"
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
                cpp_type: "string"
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
              }
            }
          }
        }
        decls {
          decltype: FUNC
          cpp_file: "foo.h"
          line_number: 5
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

  def testCapsuleFromDef(self):
    self.ClifEqual("""\
        from "some.h":
          capsule Foo
          def f(a: Foo)
      """, """\
        source: "clif_python_pytd2proto_test"
        decls {
          decltype: TYPE
          cpp_file: "some.h"
          line_number: 2
          fdecl {
            name {
              native: "Foo"
              cpp_name: "Foo"
            }
          }
        }
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
                lang_type: "Foo"
                cpp_type: "Foo *"
                cpp_raw_pointer: true
              }
            }
          }
        }
        extra_init: "PyEval_InitThreads();"
        typemaps {
          lang_type: "Foo"
          cpp_type: "Foo *"
        }
      """, include_typemaps=True, add_extra_init=False)

  def testImport(self):
    self.ClifEqual("""\
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
      """)

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
              native: "a.b.c.Bar"
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
        class Foo:
          def __radd__(self, other: int) -> int
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
                    cpp_type: "Foo"
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

  def testFromReplacementClass(self):
    self.ClifEqual("""\
      from "foo.h":
        class Foo(`Bar` as replacement):
          pass
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
            bases {
              native: "replacement"
              cpp_name: "Bar"
            }
          }
        }
      """)

  def testFromReplacementClassErrNoCppNameForReplacememt(self):
    with self.assertRaises(NameError):
      self.ClifEqual("""\
        from "foo.h":
          class Foo(replacement):
            pass
        """, '')

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
                      cpp_type: "string"
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
                    cpp_type: "string"
                  }
                }
                returns {
                  name {
                    native: "y"
                    cpp_name: "y"
                  }
                  type {
                    lang_type: "str"
                    cpp_type: "string"
                  }
                }
                py_keep_gil: true
              }
            }
          }
        }
      """)

  def testFromClassBadInitName(self):
    # 
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

  def testFromClassOps(self):
    # 
    self.ClifEqualWithTypes("""\
      from "foo.h":
        class Foo:
          def __init__(self, a: int)
          def __eq__(self, other: Foo) -> bool
          def __le__(self, other: Foo) -> bool
          def __nonzero__(self) -> bool
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
                  native: "__nonzero__"
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
              line_number: 8
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
                    cpp_type: "string"
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
                    cpp_type: "string"
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
                    cpp_type: "string"
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
                    cpp_type: "string"
                  }
                }
                returns {
                  type {
                    lang_type: "bytes"
                    cpp_type: "string"
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
                    cpp_type: "string"
                  }
                }
                params {
                  name {
                    native: "v"
                    cpp_name: "v"
                  }
                  type {
                    lang_type: "bytes"
                    cpp_type: "string"
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


class IncludeTest(unittest.TestCase):

  def setUp(self):
    self._path_prefix = os.environ['CLIF_DIR']
    self._cpp_string = 'std::string'

  def testInclude(self):
    typetable = {}
    capsule = {}
    macro = {}
    init = []
    with open(self._path_prefix + '/clif/python/types.h') as t:
      list(pytd2proto._read_include(t, 'fname', '', typetable, capsule, macro,
                                    init))
    self.assertIn(self._cpp_string, typetable.get('bytes'), str(typetable))
    self.assertFalse(init)

  def testIncludeAs(self):
    typetable = {}
    capsule = {}
    macro = {}
    init = []
    with open(self._path_prefix + '/clif/python/types.h') as t:
      list(pytd2proto._read_include(t, 'fname', 'v.', typetable, capsule, macro,
                                    init))
    self.assertIn(self._cpp_string, typetable.get('v.bytes'), str(typetable))
    self.assertNotIn('bytes', typetable, str(typetable))
    self.assertFalse(init)


if __name__ == '__main__':
  unittest.main()
