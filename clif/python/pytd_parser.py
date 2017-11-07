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

"""PYTD PyParser module.

Use
  Clif class representing CLIF PYTD grammar.
  Clif.parseString() invoke the parser.
"""

import pyparsing as pp
version = pp.__version__

W = pp.Keyword
S = pp.Suppress
SW = lambda kw: S(W(kw))
Group = pp.Group        # pylint: disable=invalid-name
Optional = pp.Optional  # pylint: disable=invalid-name
LineNum = pp.lineno     # pylint: disable=invalid-name


# Grammar for Python Type Declaration (CLIF version)


def fail_block(s, unused_loc, expr, err):
  raise pp.ParseFatalException(s, err.loc, 'invalid statement in %s' % expr)

_indentation_stack = [1]  # Holds cols to indent from.
BLOCK = lambda el: (S(':') + NEWLINE -  # pylint: disable=g-long-lambda
                    pp.indentedBlock(el, _indentation_stack)
                    .setFailAction(fail_block))


def reset_indentation():  # pylint: disable=invalid-name
  _indentation_stack[:] = [1]

K = lambda el: pp.Keyword(el).setParseAction(lambda el, loc, t: [t[0], loc])
# pylint: disable=undefined-variable
E = lambda el: pp.Empty().setParseAction(lambda: el)
Tag = lambda el: pp.Empty().setParseAction(lambda s, loc, t: [el, loc])  # pylint: disable=invalid-name
# pylint: enable=undefined-variable
NEWLINE = pp.lineEnd.setWhitespaceChars(' ').suppress().ignore(
    pp.pythonStyleComment)


def PARENS(el):           # pylint: disable=invalid-name
  el.ignore(pp.pythonStyleComment)
  return S('(') - el - S(')')

ANGLED = lambda el: S('<') - el - S('>')

QSTRING = pp.QuotedString('"')
ASTRING = pp.QuotedString('`')
DSTRING = pp.QuotedString('"""', multiline=True, convertWhitespaceEscapes=False)
NAME = pp.Word(pp.alphas+'_', pp.alphanums+'_').setName('name')
dotted_name = pp.delimitedList(NAME, '.', combine=True)

rename = ASTRING + S('as')
crename = rename - dotted_name
cname = Group(Optional(rename) + NAME)('name')
tname = Group(Optional(rename) + dotted_name)('name')

type = pp.Forward().setName('type')  # pylint: disable=redefined-builtin
pdef = Group(Group(NAME)('name') + S(':') - type +
             Optional(S('=') + K('default')))
plist = pp.ZeroOrMore(S(',') + pdef)

decorators = Group(pp.ZeroOrMore(S('@') - NAME + NEWLINE))('decorators')
parameters = Group(PARENS(Optional(pdef + plist)))('params')
mparameters = PARENS((W('self') | W('cls'))('self') + Group(plist)('params'))

docstring = Group(DSTRING + NEWLINE)('docstring')
postproc = Group(S('return') - pp.WordEnd() + NAME - S('(...)'))('postproc')
docpost = docstring + postproc
func_block = Optional(BLOCK(docstring ^ postproc ^ docpost))('func_block')

types = Group(E('') + type) | PARENS(pp.delimitedList(pdef))
returns = S('->') - (SW('None') | Group(types)('returns'))
callable_type = Group(Optional(rename) +
                      Optional(S('lambda')) + parameters + returns)
# tname | (NAME+composed_type) does not work :(
named_type = Group(tname + Optional(ANGLED(pp.delimitedList(Group(type)))))
type <<= callable_type('callable') ^ named_type('named')

# Since all XXXdef's only used inside BLOCK that does Group inside, skip Group.
G = lambda X: X

_func = Tag('func')
funcdef = G(_func + decorators + S('def') - cname +
            parameters + Optional(returns) - Optional(func_block))
methoddef = G(_func + decorators + S('def') - cname +
              mparameters + Optional(returns) - Optional(func_block))
_cnamedef = cname + S(':') - type
vardef = G(Tag('var') + _cnamedef + Optional(
    S('=') - S('property') + PARENS(ASTRING('getter') +
                                    Optional(S(',') + ASTRING('setter')))) +
           Optional(docstring))
composed_type = NAME - ANGLED(pp.delimitedList(NAME))
interface_stmt = G(K('interface') - composed_type) - BLOCK(methoddef | vardef)
implementsdef = G(K('implements') - composed_type)

nested_decl = pp.Forward()
classdef = G(Tag('class') + decorators + S('class') - cname +
             Group(Optional(PARENS(pp.delimitedList(cname))))('bases') -
             Optional(S(':') + NEWLINE + Optional(docstring) +
                      pp.indentedBlock(nested_decl, _indentation_stack)))
constdef = G(K('const') - _cnamedef)
enumdef = G(K('enum') - cname + Optional(S('with') - BLOCK(crename)))
capsule_def = G(K('capsule') - cname)
stmeth_stmt = G(K('staticmethods') - S('from') + ASTRING - BLOCK(funcdef))

_decl = classdef | enumdef | constdef
global_decl = funcdef | capsule_def | _decl | interface_stmt | stmeth_stmt
nested_decl <<= vardef | methoddef | _decl | K('pass') | implementsdef

import_stmt = G(S('from') + pp.WordEnd() + dotted_name - K('import') + NAME)
# Put 'import' first.
import_stmt.setParseAction(lambda t: [t[1], t[2], t[0], t[3]])
ns_stmt = G(K('namespace') - ASTRING + BLOCK(global_decl))
from_stmt = G(K('from') + QSTRING + BLOCK(global_decl | ns_stmt))
include_stmt = G(Tag('include') + S('from') + QSTRING + S('import') - S('*') +
                 Optional(S('as') - NAME))
typedef_stmt = G(K('type') - NAME + S('=') + type)
use_stmt = G(K('use') - crename)

stmt = Group(NEWLINE |
             from_stmt | import_stmt | include_stmt |
             typedef_stmt | use_stmt | interface_stmt
            )

# Top-level parser.
Clif = Optional(Group(Tag('docstring') + DSTRING)) + pp.OneOrMore(stmt)  # pylint: disable=invalid-name
Clif.ignore(pp.pythonStyleComment)
Clif.validate()
