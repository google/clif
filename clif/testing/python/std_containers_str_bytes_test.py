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

from clif.testing.python import std_containers_str_bytes


UC16 = '\u039E'  # Any 16-bit code point (Greek Xi).
UC32 = '\U0001FAA2'  # Any 32-bit code point (Knot).
X80 = b'\x80'  # Malformed UTF-8: sensitive to accidental decode-encode cycles.


class StdContainersStrBytesTest(absltest.TestCase):

  def testReturnListStr(self):
    lst = std_containers_str_bytes.ReturnListStr(False)
    self.assertEqual(lst, [UC32])

  def testReturnListBytes(self):
    lst = std_containers_str_bytes.ReturnListBytes(True)
    self.assertEqual(lst, [X80])

  def testPassListStr(self):
    n = std_containers_str_bytes.PassListStr([UC32])
    self.assertEqual(n, 4)

  def testPassListBytes(self):
    n = std_containers_str_bytes.PassListBytes([X80])
    self.assertEqual(n, 1)

  def testPassCallbackPassListStr(self):
    def cb(v):
      assert len(v) == 1
      return isinstance(v[0], str)

    self.assertTrue(std_containers_str_bytes.PassCallbackPassListStr(cb))

  def testPassCallbackPassListBytes(self):
    def cb(v):
      assert len(v) == 1
      return isinstance(v[0], bytes)

    self.assertTrue(std_containers_str_bytes.PassCallbackPassListBytes(cb))

  def testPassCallbackReturnListStr(self):
    def cb():
      return [UC32]

    n = std_containers_str_bytes.PassCallbackReturnListStr(cb)
    self.assertEqual(n, 4)

  def testPassCallbackReturnListBytes(self):
    def cb():
      return [X80]

    n = std_containers_str_bytes.PassCallbackReturnListBytes(cb)
    self.assertEqual(n, 1)

  def testVirtualPassListStr(self):
    class Drvd(std_containers_str_bytes.VirtualBaseVectorString):

      def PassListStr(self, v):
        assert len(v) == 1
        return isinstance(v[0], str)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassList(Drvd(), 'PassListStr')
    )

  def testVirtualPassListBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBaseVectorString):

      def PassListBytes(self, v):
        assert len(v) == 1
        return isinstance(v[0], bytes)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassList(Drvd(), 'PassListBytes')
    )

  def testVirtualReturnListStr(self):
    class Drvd(std_containers_str_bytes.VirtualBaseVectorString):

      def ReturnListStr(self):
        return [UC32]

    n = std_containers_str_bytes.CallVirtualReturnList(Drvd(), 'ReturnListStr')
    self.assertEqual(n, 4)

  def testVirtualReturnListBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBaseVectorString):

      def ReturnListBytes(self):
        return [X80]

    n = std_containers_str_bytes.CallVirtualReturnList(
        Drvd(), 'ReturnListBytes'
    )
    self.assertEqual(n, 1)

  def testReturnTupleStrStr(self):
    tup = std_containers_str_bytes.ReturnTupleStrStr()
    self.assertEqual(tup, ('first', 'second'))

  def testReturnTupleBytesBytes(self):
    tup = std_containers_str_bytes.ReturnTupleBytesBytes()
    self.assertEqual(tup, (b'first', b'second'))

  def testReturnTupleStrBytes(self):
    tup = std_containers_str_bytes.ReturnTupleStrBytes()
    self.assertEqual(tup, ('first', b'second'))

  def testReturnTupleBytesStr(self):
    tup = std_containers_str_bytes.ReturnTupleBytesStr()
    self.assertEqual(tup, (b'first', 'second'))

  def testPassTupleStrStr(self):
    n = std_containers_str_bytes.PassTupleStrStr((UC32, UC16))
    self.assertEqual(n, 6)

  def testPassTupleBytesBytes(self):
    n = std_containers_str_bytes.PassTupleBytesBytes((X80, X80))
    self.assertEqual(n, 2)

  def testPassTupleStrBytes(self):
    n = std_containers_str_bytes.PassTupleStrBytes((UC32, X80))
    self.assertEqual(n, 5)

  def testPassTupleBytesStr(self):
    n = std_containers_str_bytes.PassTupleBytesStr((X80, UC16))
    self.assertEqual(n, 3)

  def testPassCallbackPassTupleStrStr(self):
    def cb(p):
      assert len(p) == 2
      return isinstance(p[0], str) and isinstance(p[1], str)

    self.assertTrue(std_containers_str_bytes.PassCallbackPassTupleStrStr(cb))

  def testPassCallbackPassTupleBytesBytes(self):
    def cb(p):
      assert len(p) == 2
      return isinstance(p[0], bytes) and isinstance(p[1], bytes)

    self.assertTrue(
        std_containers_str_bytes.PassCallbackPassTupleBytesBytes(cb)
    )

  def testPassCallbackPassTupleStrBytes(self):
    def cb(p):
      assert len(p) == 2
      return isinstance(p[0], str) and isinstance(p[1], bytes)

    self.assertTrue(std_containers_str_bytes.PassCallbackPassTupleStrBytes(cb))

  def testPassCallbackPassTupleBytesStr(self):
    def cb(p):
      assert len(p) == 2
      return isinstance(p[0], bytes) and isinstance(p[1], str)

    self.assertTrue(std_containers_str_bytes.PassCallbackPassTupleBytesStr(cb))

  def testPassCallbackReturnTupleStrStr(self):
    def cb():
      return (UC32, UC16)

    n = std_containers_str_bytes.PassCallbackReturnTupleStrStr(cb)
    self.assertEqual(n, 6)

  def testPassCallbackReturnTupleBytesBytes(self):
    def cb():
      return (X80, X80)

    n = std_containers_str_bytes.PassCallbackReturnTupleBytesBytes(cb)
    self.assertEqual(n, 2)

  def testPassCallbackReturnTupleStrBytes(self):
    def cb():
      return (UC32, X80)

    n = std_containers_str_bytes.PassCallbackReturnTupleStrBytes(cb)
    self.assertEqual(n, 5)

  def testPassCallbackReturnTupleBytesStr(self):
    def cb():
      return (X80, UC16)

    n = std_containers_str_bytes.PassCallbackReturnTupleBytesStr(cb)
    self.assertEqual(n, 3)

  def testVirtualPassTupleStrStr(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def PassTupleStrStr(self, p):
        assert len(p) == 2
        return isinstance(p[0], str) and isinstance(p[1], str)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassTuple(Drvd(), 'PassTupleStrStr')
    )

  def testVirtualPassTupleBytesBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def PassTupleBytesBytes(self, p):
        assert len(p) == 2
        return isinstance(p[0], bytes) and isinstance(p[1], bytes)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassTuple(
            Drvd(), 'PassTupleBytesBytes'
        )
    )

  def testVirtualPassTupleStrBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def PassTupleStrBytes(self, p):
        assert len(p) == 2
        return isinstance(p[0], str) and isinstance(p[1], bytes)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassTuple(
            Drvd(), 'PassTupleStrBytes'
        )
    )

  def testVirtualPassTupleBytesStr(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def PassTupleBytesStr(self, p):
        assert len(p) == 2
        return isinstance(p[0], bytes) and isinstance(p[1], str)

    self.assertTrue(
        std_containers_str_bytes.CallVirtualPassTuple(
            Drvd(), 'PassTupleBytesStr'
        )
    )

  def testVirtualReturnTupleStrStr(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def ReturnTupleStrStr(self):
        return (UC32, UC16)

    n = std_containers_str_bytes.CallVirtualReturnTuple(
        Drvd(), 'ReturnTupleStrStr'
    )
    self.assertEqual(n, 6)

  def testVirtualReturnTupleBytesBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def ReturnTupleBytesBytes(self):
        return (X80, X80)

    n = std_containers_str_bytes.CallVirtualReturnTuple(
        Drvd(), 'ReturnTupleBytesBytes'
    )
    self.assertEqual(n, 2)

  def testVirtualReturnTupleStrBytes(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def ReturnTupleStrBytes(self):
        return (UC32, X80)

    n = std_containers_str_bytes.CallVirtualReturnTuple(
        Drvd(), 'ReturnTupleStrBytes'
    )
    self.assertEqual(n, 5)

  def testVirtualReturnTupleBytesStr(self):
    class Drvd(std_containers_str_bytes.VirtualBasePairString):

      def ReturnTupleBytesStr(self):
        return (X80, UC16)

    n = std_containers_str_bytes.CallVirtualReturnTuple(
        Drvd(), 'ReturnTupleBytesStr'
    )
    self.assertEqual(n, 3)

  def testReturnNestedTupleStrBytesBytesStr(self):
    tup = std_containers_str_bytes.ReturnNestedTupleStrBytesBytesStr()
    self.assertEqual(tup, ((UC32, X80), (X80, UC16)))

  def testPassNestedTupleBytesStrStrBytes(self):
    n = std_containers_str_bytes.PassNestedTupleBytesStrStrBytes(
        ((X80, UC16), (UC32, X80))
    )
    self.assertEqual(n, 8)

  def testPassCallbackPassNestedTupleStrBytesStrBytes(self):
    def cb(np):
      assert [len(p) for p in np] == [2, 2]
      return (
          isinstance(np[0][0], str)
          and isinstance(np[0][1], bytes)
          and isinstance(np[1][0], str)
          and isinstance(np[1][1], bytes)
      )

    self.assertTrue(
        std_containers_str_bytes.PassCallbackPassNestedTupleStrBytesStrBytes(cb)
    )

  def testPassCallbackReturnNestedTupleBytesStrBytesStr(self):
    def cb():
      return ((X80, UC32), (X80, UC16))

    n = std_containers_str_bytes.PassCallbackReturnNestedTupleBytesStrBytesStr(
        cb
    )
    self.assertEqual(n, 8)

  def testVirtualPassNestedTuple(self):
    class Drvd(std_containers_str_bytes.VirtualBaseNestedPairString):

      def PassNestedTuple(self, np):
        assert [len(p) for p in np] == [2, 2]
        return (
            isinstance(np[0][0], str)
            and isinstance(np[0][1], str)
            and isinstance(np[1][0], bytes)
            and isinstance(np[1][1], bytes)
        )

    self.assertTrue(std_containers_str_bytes.CallVirtualPassNestedTuple(Drvd()))

  def testVirtualReturnNestedTuple(self):
    class Drvd(std_containers_str_bytes.VirtualBaseNestedPairString):

      def ReturnNestedTuple(self):
        return ((X80, X80), (UC32, UC16))

    n = std_containers_str_bytes.CallVirtualReturnNestedTuple(Drvd())
    self.assertEqual(n, 8)


if __name__ == '__main__':
  absltest.main()
