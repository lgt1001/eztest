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

    def test_append(self):
        sb = stringbuilder.StringBuilder()
        sb.append('abc')
        self.assertEqual(sb.length, 3)
        self.assertListEqual(sb.data, ['abc'])
        self.assertEqual(len(sb), 3)
        self.assertEqual(str(sb), 'abc')

        sb.append('def')
        self.assertEqual(sb.length, 6)
        self.assertListEqual(sb.data, ['abc', 'def'])
        self.assertEqual(len(sb), 6)
        self.assertEqual(str(sb), 'abcdef')

        sb.append(None)
        self.assertEqual(sb.length, 6)
        self.assertListEqual(sb.data, ['abc', 'def'])
        self.assertEqual(len(sb), 6)
        self.assertEqual(str(sb), 'abcdef')

        sb.append('')
        self.assertEqual(sb.length, 6)
        self.assertListEqual(sb.data, ['abc', 'def', ''])
        self.assertEqual(len(sb), 6)
        self.assertEqual(str(sb), 'abcdef')

    def test_append_line(self):
        sb = stringbuilder.StringBuilder()
        sb.append_line('abc')
        self.assertEqual(sb.length, 4)
        self.assertListEqual(sb.data, ['abc\n'])
        self.assertEqual(len(sb), 4)
        self.assertEqual(str(sb), 'abc\n')

        sb.append_line('def')
        self.assertEqual(sb.length, 8)
        self.assertListEqual(sb.data, ['abc\n', 'def\n'])
        self.assertEqual(len(sb), 8)
        self.assertEqual(str(sb), 'abc\ndef\n')

        sb.append_line(None)
        self.assertEqual(sb.length, 9)
        self.assertListEqual(sb.data, ['abc\n', 'def\n', '\n'])
        self.assertEqual(len(sb), 9)
        self.assertEqual(str(sb), 'abc\ndef\n\n')

        sb.append_line('')
        self.assertEqual(sb.length, 10)
        self.assertListEqual(sb.data, ['abc\n', 'def\n', '\n', '\n'])
        self.assertEqual(len(sb), 10)
        self.assertEqual(str(sb), 'abc\ndef\n\n\n')

    def test_to_string(self):
        sb = stringbuilder.StringBuilder()
        sb.append_line('abc')
        sb.append_line('def')
        sb.append_line(None)
        sb.append_line('')
        self.assertEqual(sb.to_string('|'), 'abc\n|def\n|\n|\n')
        self.assertEqual(sb.to_string('-|-'), 'abc\n-|-def\n-|-\n-|-\n')

        sb = stringbuilder.StringBuilder()
        sb.append('abc')
        sb.append('def')
        sb.append(None)
        sb.append('')
        self.assertEqual(sb.to_string('|'), 'abc|def|')
        self.assertEqual(sb.to_string('-|-'), 'abc-|-def-|-')

    def test_add(self):
        sb = stringbuilder.StringBuilder()
        sb = sb + 'abc'
        self.assertEqual(str(sb), 'abc')

        sb.append('def')
        sb += 'ghi'
        self.assertEqual(str(sb), 'abcdefghi')


if __name__ == '__main__':
    unittest.main()