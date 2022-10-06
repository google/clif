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

"""Tests for clif.testing.python.default_args."""

from absl.testing import absltest

from clif.testing.python import default_args


class DefaultArgsTest(absltest.TestCase):

  def testMixKnownAndUnknownDefaultArgs(self):
    a = default_args.MyClass()
    b = default_args.MyClass.Arg()
    b.e = 2
    c = default_args.MyClass.Arg()
    c.e = 3
    self.assertEqual(a.MethodWithMultipleUnknownDefaultArgs(1, b, c), 10)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithMultipleUnknownDefaultArgs\(\) argument b '
        'needs a non-default value'):
      a.MethodWithMultipleUnknownDefaultArgs(1, c=c, d=4)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithMultipleUnknownDefaultArgs\(\) argument c '
        'needs a non-default value'):
      a.MethodWithMultipleUnknownDefaultArgs(1, b, d=4)
    self.assertEqual(a.MethodWithMultipleUnknownDefaultArgs(1, b), 10)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithMultipleUnknownDefaultArgs\(\) argument b '
        'needs a non-default value'):
      a.MethodWithMultipleUnknownDefaultArgs(1, c=c)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithMultipleUnknownDefaultArgs\(\) argument b '
        'needs a non-default value'):
      a.MethodWithMultipleUnknownDefaultArgs(1, d=4)
    self.assertEqual(a.MethodWithMultipleUnknownDefaultArgs(1), 10)

    self.assertEqual(a.MethodWithKnownDefaultArgs(1, 2, c, 4), 10)
    self.assertEqual(a.MethodWithKnownDefaultArgs(1, 2, c), 10)
    self.assertEqual(a.MethodWithKnownDefaultArgs(1, c=c, d=4), 10)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithKnownDefaultArgs\(\) argument c needs a '
        'non-default value'):
      a.MethodWithKnownDefaultArgs(1, 2, d=4)
    self.assertEqual(a.MethodWithKnownDefaultArgs(1, 2), 10)
    self.assertEqual(a.MethodWithKnownDefaultArgs(1, c=c), 10)
    with self.assertRaisesRegex(
        ValueError, r'MethodWithKnownDefaultArgs\(\) argument c needs a '
        'non-default value'):
      a.MethodWithKnownDefaultArgs(1, d=4)
    self.assertEqual(a.MethodWithKnownDefaultArgs(1), 10)

  def testUniquePtrUnknownDefaultArgs(self):
    a = default_args.MyClass()
    self.assertEqual(a.MethodWithUnKnownUniquePtrDefaultArg(1, c=3, d=4), 8)
    self.assertEqual(a.MethodWithUnKnownUniquePtrDefaultArg(1, c=3), 8)
    self.assertEqual(a.MethodWithUnKnownUniquePtrDefaultArg(1, d=4), 8)
    self.assertEqual(a.MethodWithUnKnownUniquePtrDefaultArg(1), 8)
    b = default_args.MyClass.Arg()
    b.e = 2
    self.assertEqual(a.MethodWithUnKnownUniquePtrDefaultArg(1, b, d=4), 10)

  def testDefaultArgs(self):
    a = default_args.MyClass()
    arg = default_args.MyClass.Arg()
    arg.e = 100
    with self.assertRaisesRegex(
        ValueError, r'MethodWithDefaultClassArg\(\) argument arg needs a '
        'non-default value'):
      a.MethodWithDefaultClassArg(i=113)
    self.assertEqual(a.MethodWithDefaultClassArg(arg=arg), 200)
    self.assertEqual(a.MethodWithUnknownDefaultArg(i=100), 110)
    self.assertEqual(a.MethodWithUnknownDefaultArg(i=100, arg=arg), 200)
    self.assertEqual(
        a.MethodWithUnknownDefaultArgLambdaExpression(i=100), b'110')
    self.assertEqual(
        a.MethodWithUnknownDefaultArgLambdaExpression(i=100, arg=arg), b'200')
    self.assertEqual(a.MethodWithDefaultEnumArg(i=5000), 5432)
    self.assertEqual(a.MethodWithDefaultPtrArg(i=1234), 1234)
    self.assertEqual(a.MethodWithDefaultFlag(i=32), 35)
    self.assertEqual(a.MethodThrowAwayDefault(input1=1, input2=2), 3)
    # Invoking methods that ignore the return values should not blow up.
    a.MethodThrowAwayDefault2(input1=1, input2=2)
    a.MethodWithOutputDefault3(input1=123, input2=456)
    self.assertEqual(a.MethodWithOutputDefault4(), 1000)
    self.assertEqual(a.MethodWithOutputDefault5(input1=10), 1000)
    a.MethodWithOutputDefault6()
    a.MethodWithOutputDefault7(input1=10)
    a.MethodWithOutputDefault8()

if __name__ == '__main__':
  absltest.main()
