from absl.testing import absltest

from clif.testing.python import absl_cord


class AbslCordTest(absltest.TestCase):

  def testPassAbslCord(self):
    self.assertEqual(absl_cord.PassAbslCordStr('P str'), b'P str')
    self.assertEqual(absl_cord.PassAbslCordBytes(b'P bytes'), b'P bytes')

  def testReturnAbslCord(self):
    self.assertEqual(absl_cord.ReturnAbslCordStr(b'R str'), 'R str')
    self.assertEqual(absl_cord.ReturnAbslCordBytes(b'R bytes'), b'R bytes')


if __name__ == '__main__':
  absltest.main()
