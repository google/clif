# Copyright 2023 Google LLC
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

from absl.testing import absltest

from clif.testing.python import nested_callbacks_str_bytes


class NestedCallbacksStrBytesTest(absltest.TestCase):

  def test_call_level_callback_si_s(self):
    def cb_1(i):
      if not isinstance(i, int):
        return "cb_1_FAIL"
      return "cb_1_" + str(i)

    def cb_2(cb):
      r = cb(20)
      if not isinstance(r, str):
        return "cb_2_FAIL"
      return "cb_2_" + r

    def cb_3(cb):
      r = cb(cb_1)
      if not isinstance(r, str):
        return "cb_3_FAIL"
      return "cb_3_" + r

    def cb_4(cb):
      r = cb(cb_2)
      if not isinstance(r, str):
        return "cb_4_FAIL"
      return "cb_4_" + r

    m = nested_callbacks_str_bytes
    self.assertEqual(m.call_level_1_callback_si_s(cb_1), "cb_1_1001")
    self.assertEqual(m.call_level_2_callback_si_s(cb_2), "cb_2_level_0_si_20")
    self.assertEqual(m.call_level_3_callback_si_s(cb_3), "cb_3_cb_1_1001")
    self.assertEqual(
        m.call_level_4_callback_si_s(cb_4), "cb_4_cb_2_level_0_si_20"
    )

  def test_call_level_callback_si_b(self):
    def cb_1(i):
      if not isinstance(i, int):
        return "cb_1_FAIL"
      return ("cb_1_" + str(i)).encode()

    def cb_2(cb):
      r = cb(20)
      if not isinstance(r, bytes):
        return "cb_2_FAIL"
      return ("cb_2_" + r).encode()

    def cb_3(cb):
      r = cb(cb_1)
      if not isinstance(r, bytes):
        return "cb_3_FAIL"
      return ("cb_3_" + r).encode()

    def cb_4(cb):
      r = cb(cb_2)
      if not isinstance(r, bytes):
        return "cb_4_FAIL"
      return ("cb_4_" + r).encode()

    m = nested_callbacks_str_bytes
    self.assertEqual(m.call_level_1_callback_si_b(cb_1), b"cb_1_1001")
    self.assertEqual(m.call_level_2_callback_si_b(cb_2), b"cb_2_FAIL")  # BUG
    self.assertEqual(m.call_level_3_callback_si_b(cb_3), b"cb_3_FAIL")  # BUG
    self.assertEqual(m.call_level_4_callback_si_b(cb_4), b"cb_4_FAIL")  # BUG


if __name__ == "__main__":
  absltest.main()
