# Copyright 2020 Google LLC
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

import absolute_import
import division
import print_function

import lib_hello
import googletest


class LibHello(googletest.TestCase):

  def testHello(self):
    res = lib_hello.hello('world')
    self.assertEqual(res, 'Hello, world!')

  def testHelloAndBye(self):
    res = lib_hello.hello_and_bye('world')
    self.assertEqual(res, 'Hello, world! Bye, world!')

if __name__ == '__main__':
  googletest.main()
