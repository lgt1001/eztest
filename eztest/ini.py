"""Load data from INI file.
The INI file format is an informal standard for configuration files for some platforms or software.
INI files are simple text files with a basic structure composed of sections, properties, and values.

e.g.:
;comment text
[people]
name=value

usage:
a = INI("/tmp/example.ini")         # Load INI data from file.
a.get("people")                     # Get section "people".
a.get("people", "name")             # Get value of property "name" under section "people".
a.get("people", "hello", "world")   # Get value of property "hello" under section "people", or default value "world" if section or property not found.

a.contains("people")                # Whether INI file contains section "people".
a.contains("people", "name")        # Whether INI file contains property "name" under section "people".

a.set("new section")                # Define section "new section".
a.set("new section", "new property name", "new value")  # Define property "new property name" and its value under section "new section".

a.remove("new section", "new property name")    # Remove property "new property name" from section "new section".
a.remove("new section")             # Remove section "new section".

a.save()                            # Save to INI file.
a.save("/tmp/new_file.ini")         # Save to /tmp/new_file.ini file.

class People:
    def __init__(self):
        self.name = None

p = People()
a.get("people").to_object(p)            # Set p with same properties under section "people" in INI file.
a.get("people").contains("name")        # Whether section "people" contains property "name".
a.get("people").get("name")             # Get value of property "name".
a.get("people").get("hello", "world")   # Get value of property "hello", or default value if not found.
a.get("people").set("new property name", "new value")   # Define property "new property name" and its value
a.get("people").clear()                 # Clear all properties.
a.get("people").from_object(p)          # Set "people" section from p object.

Common escape sequences in INI file.
Sequence	Meaning
\\	        \ (a single backslash, escaping the escape character)
\0	        Null character
\t	        Tab character
\r	        Carriage return
\n	        Line feed
\;	        Semicolon
"""
import inspect
import json
import os
import re
import sys

from .utility import to_boolean

PROPERTY_TYPES = [bin, bool, bytearray, complex, dict, float, hex, int, list, oct, set, str, tuple]
if sys.version_info <= (2, 7):
    PROPERTY_TYPES.append(basestring, long, unicode)
if sys.version_info >= (3, 0):
    PROPERTY_TYPES.append(bytes)


class INI:
    """Ini class is used for configuration file. The content in this file should be:

    ;comment text
    [section]
    name=value
    You also can view the standard of configuration from "http://en.wikipedia.org/wiki/INI_file"
    """
    __slots__ = ['file_path', 'sections']

    def __init__(self, file_path=None):
        """Initialization. Load settings from configuration file.

        :param str file_path: configuration file's path.
        """
        self.file_path = file_path
        self.sections = []
        if self.file_path:
            if not os.path.abspath(self.file_path):
                self.file_path = os.path.join(os.getcwd(), self.file_path)
            if os.path.exists(self.file_path):
                self._load()

    def _load(self):
        """Load settings from configuration file."""
        with open(self.file_path, 'r') as f:
            try:
                s = None
                while True:
                    line = f.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line == '':
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        s = Section(line[1:-1])
                        self.sections.append(s)
                    elif line.startswith(';'):
                        continue
                    elif s is not None:
                        i = line.find('=')
                        if i > 0:
                            k = line[0:i].strip()
                            if not k:
                                continue
                            v = line[i + 1:].strip()
                            if v == '\\0':
                                v = None
                            elif v.find('\\') >= 0:
                                nv = ""
                                token = None
                                for c in v:
                                    if token:
                                        token += c
                                        if token == '\\\\':
                                            nv += '\\'
                                        elif token == '\\t':
                                            nv += '\t'
                                        elif token == '\\r':
                                            nv += '\r'
                                        elif token == '\\n':
                                            nv += '\n'
                                        else:
                                            nv += token
                                        token = None
                                    elif c == '\\':
                                        token = c
                                    else:
                                        nv += c
                                if token:
                                    nv += token
                                v = nv
                            s.set(k, v)
            except Exception as e:
                raise Exception('Failed to load data: {}'.format(str(e)))

    def set(self, section_name, property_name=None, property_value=None):
        """Add/update section or property value.

        :param str section_name: section name.
        :param str property_name: property name in section.
        :param property_value: property value in section.
        """
        if not section_name:
            return ValueError('section_name cannot be null or empty')
        for s in self.sections:
            if s.name == section_name:
                s1 = s
                break
        else:
            s1 = Section(section_name)
            self.sections.append(s1)
        if property_name is not None:
            s1.set(property_name, property_value)

    def contains(self, section_name, property_name=None):
        """Whether ini file contains specified section or property name.

        :param str section_name: section name.
        :param str property_name: property name in section.
        :return bool: True if section_name or property_name found, otherwise False.
        """
        if not section_name:
            return False
        for s in self.sections:
            if s.name == section_name:
                s1 = s
                break
        else:
            return False
        return True if property_name is None else s1.contains(property_name)

    def get(self, section_name, property_name=None, default_value=None):
        """Get section or property value according to section name and property name.

        :param str section_name : section name.
        :param str property_name : property name in section.
        :param default_value: default value for property.
        :return Section|str: Section if section_name found and no property_name provided, None if section_name not found;
            Property value if property_name provided and found, otherwise default_value.
        """
        if not section_name:
            return ValueError('section_name cannot be null or empty')
        for s in self.sections:
            if s.name == section_name:
                s1 = s
                break
        else:
            return
        return s1 if property_name is None else s1.get(property_name, default_value)

    def save(self, file_path=None):
        """Save settings into configuration file."""
        file_path = file_path or self.file_path
        if not file_path:
            raise ValueError('Please provide file path.')
        with open(file_path, 'w') as f:
            try:
                for s in self.sections:
                    f.write('[{}]{}'.format(s.name, os.linesep))
                    for key, value in s.properties.items():
                        if isinstance(value, dict):
                            value = json.dumps(value)
                        elif isinstance(value, list):
                            value = ','.join([str(v) for v in value])
                        elif isinstance(value, set):
                            value = ','.join(list(value))
                        elif isinstance(value, bytearray) or (sys.version_info >= (3, 0) and isinstance(value, bytes)):
                            value = value.decode('utf-8')
                        elif value is not None:
                            value = str(value)

                        if value is None:
                            value = '\\0'
                        else:
                            value = value.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')

                        f.write('{}={}{}'.format(key, value, os.linesep))
                    f.write(os.linesep)
            except Exception as e:
                raise Exception('Failed to write data into file: {}'.format(str(e)))

    def remove(self, section_name, property_name=None):
        """Remove section or property.

        :param section_name : section name.
        :param property_name : property name in section.
        """
        if not section_name:
            return ValueError('section_name cannot be null or empty')
        for s in self.sections:
            if s.name == section_name:
                s1 = s
                break
        else:
            return
        if property_name is None:
            self.sections.remove(s1)
            return
        s1.remove(property_name)


class Section:
    """Section class, contains section name and its properties."""
    __slots__ = ['name', 'properties']

    def __init__(self, section_name=None):
        """Initialization.

        :param str section_name: section name.
        """
        self.name = section_name
        self.properties = dict()

    def set(self, property_name, property_value=None):
        """Add/update property

        :param str property_name: property name.
        :param property_value: property value.
        """
        if not property_name:
            raise ValueError('property_name can not be null or empty.')
        self.properties[property_name] = property_value

    def contains(self, property_name):
        """Whether section contains specified property name.

        :param str property_name: property name.
        :return bool: True if Section contains the property, otherwise False.
        """
        if not property_name:
            return False
        return property_name in self.properties

    def remove(self, property_name):
        """Remove a property by property name.

        :param str property_name: property name.
        """
        if not property_name:
            raise ValueError('property_name can not be null or empty.')
        if property_name in self.properties:
            del self.properties[property_name]

    def get(self, property_name, default_value=None):
        """Get property value by property name.

        :param str property_name: property name.
        :param default_value: return default value if it does not exist.
        :return str: property value if found, otherwise returns default_value.
        """
        if not property_name:
            raise ValueError('property_name can not be null or empty.')
        return self.properties.get(property_name, default_value)

    def clear(self):
        """Clear all properties."""
        self.properties = dict()

    def to_object(self, obj):
        """Copy values of property in section to property in the object.

        :param obj: the object which should be evaluated.
        :return dict: a dictionary with keys don't exist in obj.
        """
        if obj is None:
            raise ValueError('obj can not be None.')
        result = dict()
        for key, value in self.properties.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                t = type(attr)
                if t is bin:
                    v = bin(int(value, 2))
                elif t is bool:
                    v = to_boolean(value)
                elif t is bytearray:
                    v = bytearray(value, encoding='utf-8')
                elif t is complex:
                    g = re.match(r'^(-?\d+)(([\+\-]\d+)[ij])?$', value)
                    if g:
                        v = complex(int(g.group(1)), int(g.group(3)))
                    else:
                        v = value
                elif t is dict:
                    v = json.loads(value)
                elif t is float:
                    v = float(value)
                elif t is hex:
                    v = hex(int(value, 16))
                elif t is int:
                    v = int(value)
                elif t is list:
                    v = value.split(',')
                elif t is set:
                    v = set(value.split(','))
                elif t is tuple:
                    v = tuple(value.split(','))
                elif t is oct:
                    v = oct(int(value, 8))
                elif t is str:
                    v = str(value)
                else:
                    if sys.version_info <= (2, 7):
                        if t is long:
                            v = long(value)
                        elif t is unicode:
                            v = unicode(value, encoding='utf-8')
                        else:
                            v = value
                    elif sys.version_info >= (3, 0) and t is bytes:
                        v = bytes(value, encoding='utf-8')
                    else:
                        v = value
                setattr(obj, key, v)
            else:
                result[key] = value
        return obj

    def from_object(self, obj):
        """Copy values from object.

        :param obj: object.
        :return Section: self.
        """
        if obj is None:
            raise ValueError('obj can not be None.')
        for key, value in inspect.getmembers(obj):
            if type(value) in PROPERTY_TYPES:
                self.set(key, value)
        return self
