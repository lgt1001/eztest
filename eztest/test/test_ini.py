import os
import unittest

from eztest import ini


class Person(object):
    def __init__(self):
        self.name = None
        self.age = 18
        self.is_adult = True
        self.location = None
        self.height = '100'
        self.byte_p = bytearray()
        self.dict_p = dict()
        self.list_p = list()

    def get_location(self):
        return self.location


class TestINISection(unittest.TestCase):
    def test_section_definition(self):
        section = ini.Section('hello')
        self.assertEqual(section.name, 'hello')
        self.assertEqual(section.properties, dict())

    def test_section_set_property(self):
        section = ini.Section('hello')
        section.set('name')
        self.assertDictEqual(section.properties, dict(name=None))

        section.set('name', 'Bob')
        self.assertDictEqual(section.properties, dict(name='Bob'))

        section.set('age', 30)
        self.assertDictEqual(section.properties, dict(name='Bob', age=30))

    def test_section_get_property_value(self):
        section = ini.Section('hello')
        section.set('name', 'Bob')
        section.set('age', 30)
        self.assertEqual(section.get('name'), 'Bob')
        self.assertEqual(section.get('age'), 30)
        self.assertEqual(section.get('nothing'), None)
        self.assertEqual(section.get('nothing', 'false'), 'false')

    def test_section_contain(self):
        section = ini.Section('hello')
        section.set('name', 'Bob')
        section.set('age', 30)
        self.assertTrue(section.contains('name'))
        self.assertFalse(section.contains('nothing'))

    def test_section_remove_property(self):
        section = ini.Section('hello')
        section.set('name', 'Bob')
        section.set('age', 30)

        section.remove('age')
        self.assertTrue(section.contains('name'))
        self.assertFalse(section.contains('age'))
        self.assertEqual(section.get('age'), None)

    def test_section_clear(self):
        section = ini.Section('hello')
        section.set('name', 'Bob')
        section.set('age', 30)

        section.clear()
        self.assertDictEqual(section.properties, dict())

    def test_section_to_object(self):
        section = ini.Section('hello')
        section.set('name', 'Bob')
        section.set('age', '30')
        section.set('is_adult', True)
        section.set('height', 200)
        section.set('nothing', 'nothing')
        section.set('byte_p', 'hello')
        section.set('dict_p', '{"name": "value"}')
        section.set('list_p', 'a,b,c')

        person = Person()
        section.to_object(person)

        with self.assertRaises(ValueError):
            section.to_object(None)

        self.assertEqual(person.name, 'Bob')
        self.assertEqual(person.age, 30)
        self.assertEqual(person.is_adult, True)
        self.assertEqual(person.location, None)
        self.assertEqual(person.height, '200')
        self.assertFalse(hasattr(person, 'nothing'))
        self.assertEqual(person.byte_p, b'hello')
        self.assertDictEqual(person.dict_p, dict(name='value'))
        self.assertEqual(person.list_p, ['a','b','c'])

    def test_section_from_object(self):
        section = ini.Section('hello')
        person = Person()
        person.name = 'Bob'
        person.age = 30
        person.is_adult = True
        person.location = 'US'
        person.height = '200'

        with self.assertRaises(ValueError):
            section.from_object(None)

        section.from_object(person)

        self.assertEqual(section.get('name'), 'Bob')
        self.assertEqual(section.get('age'), 30)
        self.assertEqual(section.get('is_adult'), True)
        self.assertEqual(section.get('location'), 'US')
        self.assertEqual(section.get('height'), '200')
        self.assertFalse(section.contains('get_location'))


class TestINI(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestINI, self).__init__(*args, **kwargs)
        self.filename = 'test.ini'
        content = ''';comment text
        [people]
        name=Bob
        ;male=True
        age=30
        is_adult=True
        location=CA\\nUS
        dict_p={"name":"value"}
        list_p=a,b,c
        byte_p=\\0

        [mail]
        server=test.com
        port=25'''
        with open(self.filename, 'w') as f:
            f.write(content)
        self.data = ini.INI(self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_ini_contains(self):
        _ini = self.data
        self.assertTrue(_ini.contains('people'))
        self.assertFalse(_ini.contains('people', 'male'))
        self.assertFalse(_ini.contains('people', 'Hello'))
        self.assertTrue(_ini.contains('people', 'byte_p'))
        self.assertTrue(_ini.contains('mail'))
        self.assertTrue(_ini.contains('mail', 'server'))
        self.assertFalse(_ini.contains('Hello'))

    def test_ini_get(self):
        _ini = self.data
        self.assertEqual(_ini.get('people', 'name'), 'Bob')
        self.assertEqual(_ini.get('people', 'male'), None)
        self.assertEqual(_ini.get('people', 'age'), '30')
        self.assertEqual(_ini.get('people', 'is_adult'), 'True')
        self.assertEqual(_ini.get('people', 'location'), 'CA\nUS')
        self.assertEqual(_ini.get('people', 'dict_p'), '{"name":"value"}')
        self.assertEqual(_ini.get('people', 'list_p'), 'a,b,c')
        self.assertEqual(_ini.get('people', 'byte_p'), None)
        self.assertEqual(_ini.get('people', 'hello', 'world'), 'world')

        self.assertEqual(_ini.get('mail', 'server'), 'test.com')
        self.assertEqual(_ini.get('mail', 'port'), '25')

        self.assertIsInstance(_ini.get('people'), ini.Section)
        self.assertIsNone(_ini.get('Hello'))
        self.assertIsNone(_ini.get('people', 'Hello'))

    def test_ini_set(self):
        _ini = self.data
        _ini.set('people', 'name', 'Tom')
        self.assertEqual(_ini.get('people', 'name'), 'Tom')

        _ini.set('newsecton')
        self.assertTrue(_ini.contains('newsecton'))

        _ini.set('newsecton2', 'name2')
        self.assertTrue(_ini.contains('newsecton2', 'name2'))

        _ini.set('newsecton3', 'name3', 'value3')
        self.assertEqual(_ini.get('newsecton3', 'name3'), 'value3')

    def test_ini_remove(self):
        _ini = self.data
        _ini.remove('mail', 'port')
        self.assertFalse(_ini.contains('mail', 'port'))

        _ini.remove('mail')
        self.assertFalse(_ini.contains('mail'))

    def test_ini_save(self):
        _ini = ini.INI()
        _ini.set('sec1', 'name1', 'value1')
        _ini.set('sec1', 'age', 10)
        _ini.set('sec1', 'list_p', [1, 2, 3])
        _ini.set('sec1', 'dict_p', dict(name='value'))
        _ini.set('sec1', 'location', 'CA\nUS')
        _ini.set('sec1', 'nothing', None)

        _ini.set('sec2', 'name2', 'value2')

        _ini.save(self.filename)

        with open(self.filename, 'r') as f:
            content = f.read()

        self.assertIn('[sec1]', content)
        self.assertIn('name1=value1', content)
        self.assertIn('age=10', content)
        self.assertIn('list_p=1,2,3', content)
        self.assertIn('dict_p={"name": "value"}', content)
        self.assertIn('location=CA\\nUS', content)
        self.assertIn('nothing=\\0', content)

        self.assertIn('[sec2]', content)
        self.assertIn('name2=value2', content)


if __name__ == '__main__':
    unittest.main()