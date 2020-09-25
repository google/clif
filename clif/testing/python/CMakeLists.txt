# Copyright 2017-2020 Google LLC
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

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/__init__.py" "")

# A single target to run all the integration tests added in this file.
# Running a command like this will run all the integration tests:
#
# $> ninja runPyClifIntegrationTests
add_custom_target(runPyClifIntegrationTests
  COMMAND ${PYTHON_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_BINARY_DIR} -p "*_test.py"
  WORKING_DIRECTORY ${CLIF_BIN_DIR}
)

# A convenience function to add a pyclif_library as a dependency for the target
# runPyClifIntegrationTests. It also adds a single test target with a name
# ending in "_test". This single test target can be run with a command like
# this:
#
# $> ninja [pyclif_library_target_name]_test
function(add_pyclif_library_for_test name)
  cmake_parse_arguments(PYCLIF_TEST_LIBRARY "" "" "TEST" ${ARGN})
  if (NOT DEFINED PYCLIF_TEST_LIBRARY_TEST)
    set(PYCLIF_TEST_LIBRARY_TEST "${name}_test.py")
  endif()

  add_pyclif_library(${name}
    ${ARGN}
  )

  clif_target_name(${name} lib_target_name)
  add_dependencies(runPyClifIntegrationTests ${lib_target_name})

  configure_file(${PYCLIF_TEST_LIBRARY_TEST} ${PYCLIF_TEST_LIBRARY_TEST} COPYONLY)

  add_custom_target("${lib_target_name}_test"
    COMMAND ${PYTHON_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_BINARY_DIR} -p "${PYCLIF_TEST_LIBRARY_TEST}"
    WORKING_DIRECTORY ${CLIF_BIN_DIR}
    DEPENDS ${lib_target_name}
  )
endfunction(add_pyclif_library_for_test name)

add_pyclif_library_for_test(t1 t1.clif)

add_pyclif_library_for_test(t2 t2.clif
  CC_DEPS clif_testing_t2
)

add_pyclif_library_for_test(t3 t3.clif)

add_pyclif_library_for_test(t4 t4.clif
  CC_DEPS clif_testing_t4
  PROTO_DEPS clif_testing_nested_proto_wrapper clifAstProtoWrapperShared
)

add_pyclif_library_for_test(t6 t6.clif)

add_pyclif_library_for_test(t7 t7.clif)

add_pyclif_library_for_test(t9 t9.clif
  CC_DEPS clif_testing_t9)

add_pyclif_library_for_test(t10 t10.clif
  CLIF_DEPS clif_testing_python_t2
)

add_pyclif_library_for_test(t12 t12.clif)

add_pyclif_library_for_test(absl_uint128 absl_uint128.clif)

add_pyclif_library_for_test(callback callback.clif)

add_pyclif_library_for_test(call_method call_method.clif)

add_pyclif_library_for_test(circular circular.clif)

add_pyclif_library_for_test(class_module_attr class_module_attr.clif)

add_pyclif_library_for_test(const_char_ptr const_char_ptr.clif)

add_pyclif_library_for_test(const_pointer_return const_pointer_return.clif)

add_pyclif_library_for_test(default_args default_args.clif)

add_pyclif_library_for_test(diamond_inheritance diamond_inheritance.clif)

add_pyclif_library_for_test(enable_instance_dict enable_instance_dict.clif)

add_pyclif_library_for_test(extend_from_clifaux extend_from_clifaux.clif)

add_pyclif_library_for_test(extend_methods extend_methods.clif)

add_pyclif_library_for_test(extend_properties extend_properties.clif)

add_pyclif_library_for_test(extension_type_refcount extension_type_refcount.clif)

add_pyclif_library_for_test(_hidden hidden.clif
  TEST hidden_test.py)

add_pyclif_library_for_test(imported_methods imported_methods.clif)

add_pyclif_library_for_test(iterator iterator.clif)

add_pyclif_library_for_test(implicit_conversion implicit_conversion.clif)

add_pyclif_library_for_test(nested_callbacks nested_callbacks.clif)

add_pyclif_library_for_test(nested_fields nested_fields.clif)

add_pyclif_library_for_test(nested_types nested_types.clif)

add_pyclif_library_for_test(nonzero_mapping nonzero_mapping.clif)

add_pyclif_library_for_test(number_methods number_methods.clif)

add_pyclif_library_for_test(operators operators.clif)

add_pyclif_library_for_test(output_parameter output_parameter.clif)

add_pyclif_library_for_test(overload overload.clif)

add_pyclif_library_for_test(pass_none pass_none.clif)

add_pyclif_library_for_test(sequence_methods sequence_methods.clif)

add_pyclif_library_for_test(shared_ptr_proto_member shared_ptr_proto_member.clif
  PROTO_DEPS clifAstProtoWrapperShared)

add_pyclif_library_for_test(slots slots.clif)

add_pyclif_library_for_test(smart_ptrs smart_ptrs.clif)

add_pyclif_library_for_test(static_methods static_methods.clif)

add_pyclif_library_for_test(std_containers std_containers.clif)

add_pyclif_library_for_test(std_variant std_variant.clif
  CC_DEPS clif_testing_std_variant)

add_pyclif_library_for_test(template_alias template_alias.clif)

add_pyclif_library_for_test(templates templates.clif)

add_pyclif_library_for_test(virtual_funcs virtual_funcs.clif)

add_pyclif_library_for_test(virtual_derived_before_base virtual_derived_before_base.clif)
