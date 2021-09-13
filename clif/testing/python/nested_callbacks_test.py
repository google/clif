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

from absl.testing import absltest

from clif.testing.python import nested_callbacks


class NestedCallbacksTest(absltest.TestCase):

  def testNestedCb(self):

    def nested_cb_cb(cb, num):
      return cb(num + 5) + 6

    res = nested_callbacks.nested_cb(nested_cb_cb, 7)
    self.assertEqual(res, 146)

  def testVirtualOverride(self):

    # Based on cl/272290922.
    class VirtualDerived(nested_callbacks.VirtualBase):

      def virtual_method(self, cb, num):
        return cb(num + 8) + 9

    d = VirtualDerived()
    res = nested_callbacks.call_virtual_method_from_cpp(d)
    self.assertEqual(res, 123)


if __name__ == '__main__':
  absltest.main()
