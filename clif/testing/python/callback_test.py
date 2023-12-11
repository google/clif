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

"""Tests for clif.testing.python.callback."""

import contextlib
import io
from unittest import mock

from absl import logging
from absl.testing import absltest
from absl.testing import parameterized

from clif.python import callback_exception_guard
from clif.testing.python import callback


def Callback(input_data):
  return 0, input_data


def Callback2(input_data):
  return input_data


def InvalidCallback1():
  return 0


def InvalidCallback2(a, b, c):  # pylint: disable=unused-argument
  return 0


def StringCallback():
  return 'abcd'


def RaisingCallback():
  raise ValueError('raised a value error')


def ObjCopyMoveTraceCallback(obj):
  return obj.trace


class CallbackTest(parameterized.TestCase):

  def CallbackMethod(self, data):
    return 1, data

  def CallbackInvalid(self):
    return 2

  def testNewStyleConstRef(self):
    self.assertEqual(
        callback.NewStyleCallbackConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(13, InvalidCallback2)

  def testNewStyleNonConstRef(self):
    self.assertEqual(
        callback.NewStyleCallbackNonConstRef([1, 2], Callback), [1, 2])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackNonConstRef(12, InvalidCallback1)
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackNonConstRef(13, InvalidCallback2)

  def testNewStyleConstRefWithSelfCallback(self):
    self.assertEqual(
        callback.NewStyleCallbackConstRef([2, 3], self.CallbackMethod),
        [2, 3])
    with self.assertRaises(TypeError):
      callback.NewStyleCallbackConstRef(23, self.CallbackInvalid)

  def testSelfCallback(self):
    # assert not raises:
    callback.SelfCallback(Callback)

  def testStringCallbackStr(self):
    def Cb(s):
      self.assertIsInstance(s, str)
      self.assertEqual(s, 'foo')

    callback.StringCallbackStr(Cb)

  def testStringCallbackBytes(self):
    def Cb(s):
      self.assertIsInstance(s, bytes)
      self.assertEqual(s, b'foo')

    callback.StringCallbackBytes(Cb)

  def testCallableOutput(self):
    returned_callback = callback.FunctionWithCallableReturn(Callback2)
    self.assertEqual(returned_callback(5), 5)

  def testBytesCallback(self):
    res = callback.LambdaCallback(StringCallback)
    self.assertIsInstance(res, bytes)
    self.assertEqual(res, b'abcd')

  def testPyObjectCallback(self):
    res = callback.PyObjectCallback(StringCallback)
    self.assertIsInstance(res, str)
    self.assertEqual(res, 'abcd')

  def testPyObjectCallbackRaises(self):
    with self.assertRaisesWithLiteralMatch(ValueError, 'raised a value error'):
      callback.PyObjectCallback(RaisingCallback)

  @parameterized.parameters((None,), (io.StringIO(),))
  def testCallbackExceptionPrintAndClear(self, file):
    @callback_exception_guard.print_and_clear(
        substitute_return_value=48, file=file
    )
    def Cb(val):
      if val < 0:
        raise ValueError(f'Negative value: {val}')
      return val * 13

    self.assertEqual(callback.CallCallbackPassIntReturnInt(Cb, 3), 39)
    ctx_io = io.StringIO()
    with contextlib.redirect_stderr(ctx_io):
      self.assertEqual(callback.CallCallbackPassIntReturnInt(Cb, -1), 48)
    if file is None:
      captured = ctx_io
    else:
      self.assertEqual(ctx_io.getvalue(), '')
      captured = file
    self.assertIn('ValueError: Negative value: -1', captured.getvalue())

  @mock.patch.object(logging, 'error', autospec=True)
  def testCallbackExceptionLogAndClear(self, mock_logging_error):
    @callback_exception_guard.log_and_clear(substitute_return_value=63)
    def Cb(val):
      if val > 0:
        raise ValueError(f'Positive value: {val}')
      return val * 17

    self.assertEqual(callback.CallCallbackPassIntReturnInt(Cb, -3), -51)
    mock_logging_error.assert_not_called()
    self.assertEqual(callback.CallCallbackPassIntReturnInt(Cb, 5), 63)
    mock_logging_error.assert_called()
    self.assertEqual(
        mock_logging_error.call_args_list[-1].args[0],
        'ValueError: Positive value: 5',
    )

  @parameterized.parameters(
      callback.CallCallbackPassConstPtrCopyMoveType,
      callback.CallCallbackPassConstPtrCopyOnlyType,
  )
  def testCallCallbackPassConstPtrCopyableType(self, call_cb):
    trace = call_cb(ObjCopyMoveTraceCallback)
    self.assertEqual(trace, 'DefaultCtor@DefaultCtor_CpCtor')

  @parameterized.parameters('MoveOnlyType', 'StayPutType')
  def testCallCallbackPassConstPtrMoveOnlyType(self, cml_type):
    call_cb_fn_name = f'CallCallbackPassConstPtr{cml_type}'
    call_cb = getattr(callback, call_cb_fn_name, None)
    if call_cb is None:
      self.skipTest(f'Unavailable: {call_cb_fn_name}')
    # TODO: Uncomment in callback.clif
    expected_error = (
        'return_value_policy = copy, but type '
        f'clif_testing::copy_move_types_library::{cml_type} is non-copyable!'
    )
    with self.assertRaisesWithLiteralMatch(RuntimeError, expected_error):
      call_cb(ObjCopyMoveTraceCallback)


if __name__ == '__main__':
  absltest.main()
