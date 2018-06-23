import unittest

from eztest import stringbuilder


class TestStringBuilder(unittest.TestCase):
    def test_init(self):
        sb = stringbuilder.StringBuilder()
        self.assertEqual(sb.length, 0)
        self.assertListEqual(sb.data, [])

        sb = stringbuilder.StringBuilder('abc')
        self.assertEqual(sb.length, 3)
        self.assertListEqual(sb.data, ['abc'])

        sb1 = stringbuilder.StringBuilder('abc')
        sb = stringbuilder.StringBuilder(sb1)
        self.assertEqual(sb.length, 3)
        self.assertListEqual(sb.data, ['abc'])


if __name__ == '__main__':
    unittest.main()