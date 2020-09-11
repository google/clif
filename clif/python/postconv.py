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

"""Prepare postconversions for Clif_PyObjFrom.

For each cpp_type conversion

  Clif_PyObjFrom(cpp_type, py::PostConv(conv_array, array_len, template))

call we prepare the template with ConversionTemplate
after we transformed the type postconversion map from AST
into indexes to the generated conv_array. The len is the same as the map.

Example:
postconversion = {'str': 'BytesToUnicode', 'ztype': 'AnotherConversion'}

GenPostConvTable()
generates
#define _0 py::postconv::PASS
#define _1 BytesToUnicode
#define _2 AnotherConversion
and transform the postconversion to {'str': 1, 'ztype': 2}.

Now Initializer() will translate lang_type to template string as
int -> {}
str -> _1
list<int> -> {}
list<str> -> {_1}
dict<int, pair<str, ztype>> -> {_0,{_1,_2}}
"""

PASS = '{}'


def GenPostConvTable(postconv_types):
  """Transform postconv_types dict(typename: convfunctionname) and yields it."""
  size = len(postconv_types)
  if size:
    yield ''
    yield '#define _0 py::postconv::PASS'
    # We need to sort for deterministic output.
    for index, pytype in enumerate(sorted(postconv_types), 1):
      size -= 1
      yield '#define _%d ' % index + postconv_types[pytype]
      postconv_types[pytype] = '_%d' % index


def Initializer(ast_type, postconv_types_index_map, nested=False):
  """Tranform [complex] ast_type to a postconversion initializer_list."""
  if ast_type.HasField('callable'):
    # TODO: Fix postconv for callable.
    # print ast_type
    return PASS
  if not postconv_types_index_map: return PASS
  if ast_type.params:  # container type
    index = '{%s}' % ','.join(
        Initializer(t, postconv_types_index_map, nested=True)
        for t in ast_type.params)
  else:
    index = postconv_types_index_map.get(ast_type.lang_type, '_0')
  # If no table-based conversions needed, return "no_conversion".
  return index if nested or index.strip('{_0,}') else PASS
