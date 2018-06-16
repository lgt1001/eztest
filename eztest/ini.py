"""Load data from INI file.
The INI file format is an informal standard for configuration files for some platforms or software.
INI files are simple text files with a basic structure composed of sections, properties, and values.

e.g.:
;comment text
[people]
name=value

usage:
a = INI('/tmp/example.ini')     # Load INI data from file.
a.get('people')                 # Get section 'people'.
a.get('people', 'name')         # Get value of property 'name' under section 'people'.
a.get('people', 'hello', 'world')   # Get value of property 'hello' under section 'people', or default value 'world' if section or property not found.

a.contains('people')            # Whether INI file contains section 'people'.
a.contains('people', 'name')    # Whether INI file contains property 'name' under section 'people'.

a.set('new section')            # Define section 'new section'.
a.set('new section', 'new property name', 'new value')  # Define property 'new property name' and its value under section 'new section'.

a.remove('new section', 'new property name')    # Remove property 'new property name' from section 'new section'.
a.remove('new section')         # Remove section 'new section'.

a.save()                        # Save to INI file.

class People:
    def __init__(self):
        self.name = None

p = People()
a.get('people').convert2obj(p)      # Set p with same properties under section 'people' in INI file.
a.get('people').contains('name')    # Whether section 'people' contains property 'name'.
a.get('people').get('name')         # Get value of roperty 'name'.
a.get('people').get('hello', 'world')   # Get value of roperty 'hello', or default value if not found.
a.get('people').set('new property name', 'new value')   # Define property 'new property name' and its value
a.get('people').clear()             # Clear all properties.


Common escape sequences in INI file.
Sequence	Meaning
\\	        \ (a single backslash, escaping the escape character)
\0	        Null character
\t	        Tab character
\r	        Carriage return
\n	        Line feed
\;	        Semicolon
"""
import os


class INI:
    """Ini class is used for configuration file. The content in this file should be:

    ;comment text
    [section]
    name=value
    You also can view the standard of configuration from "http://en.wikipedia.org/wiki/INI_file"
    """
    __slots__ = ['path', 'sections']

    def __init__(self, file_path=None):
        """Initialization. Load settings from configuration file.

        :param str file_path: configuration file's path.
        """
        self.path = file_path
        self.sections = []
        if file_path:
            if not os.path.abspath(self.path):
                self.path = os.path.join(os.getcwd(), self.path)
            if os.path.exists(self.path):
                self._load()

    def _load(self):
        """Load settings from congiruation file."""
        with open(self.path, 'r') as f:
            try:
                s = None
                while True:
                    line = f.readline()
                    if not line:  # It's end of lines.
                        break
                    line = line.strip()     # clean " "/blank space from head and tail.
                    if line == "":  # empty line, go to next line.
                        continue
                    if line.startswith('[') and line.endswith("]"):  # It's section definition
                        s = Section(line[1:-1])     # build a section.
                        self.sections.append(s)     # append this section to self.Sections.
                    elif line.startswith(";"):  # this is comment line.
                        continue
                    elif s is not None:  # it's property definition.
                        i = line.find("=")
                        if i > 0:  # it's valid property definition.
                            k = line[0:i].strip()   # append this property to section.Properties.
                            if not k:
                                continue
                            v = line[i + 1:].strip()
                            if v == '\\0':
                                v = None
                            elif v.find('\\') >= 0:    # replace "\\","\r","\t","\n" to their escape character.
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
                raise Exception("Failed to load data: {}".format(str(e)))

    def set(self, section_name, property_name=None, property_value=None):
        """Add/update section or property value.

        :param str section_name: section name.
        :param str property_name: property name in section.
        :param property_value: property value in section.
        """
        if not section_name:
            return ValueError("section_name cannot be null or empty")
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
            return ValueError("section_name cannot be null or empty")
        for s in self.sections:
            if s.name == section_name:
                s1 = s
                break
        else:
            return
        return s1 if property_name is None else s1.get(property_name, default_value)

    def save(self):
        """Save settings into configuration file."""
        with open(self.path, 'w') as f:
            try:
                for s in self.sections:
                    f.write("[%s]%s" % (s.name, os.linesep))
                    for key, value in s.properties.items():
                        f.write("%s=%s%s" % (key, value, os.linesep))
                    f.write(os.linesep)
            except Exception as e:
                raise Exception("Failed to write data into file: {}".format(str(e)))

    def remove(self, section_name, property_name=None):
        """Remove section or property.

        :param section_name : section name.
        :param property_name : property name in section.
        """
        if not section_name:
            return ValueError("section_name cannot be null or empty")
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
            raise ValueError("property_name can not be null or empty.")
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
            raise ValueError("property_name can not be null or empty.")
        if property_name in self.properties:
            del self.properties[property_name]

    def get(self, property_name, default_value=None):
        """Get property value by property name.

        :param str property_name: property name.
        :param default_value: return default value if it does not exist.
        :return str: property value if found, otherwise returns default_value.
        """
        if not property_name:
            raise ValueError("property_name can not be null or empty.")
        return self.properties.get(property_name, default_value)

    def clear(self):
        """Clear all properties."""
        self.properties = dict()

    def convert2obj(self, obj):
        """Copy values of property in section to property in the object.

        :param obj: the object which should be evaluated.
        :return dict: a dictionary with keys donot exist in obj.
        """
        if obj is None:
            raise ValueError("obj can not be null.")
        result = dict()
        for key, value in self.properties.items():
            if hasattr(obj, key):
                attr = getattr(obj, key)
                t = type(attr)
                if t is bin:
                    v = bin(value)
                elif t is bool:
                    v = bool(value)
                elif t is float:
                    v = float(value)
                elif t is hex:
                    v = hex(value)
                elif t is int:
                    v = int(value)
                elif t is oct:
                    v = oct(value)
                else:
                    v = value
                setattr(obj, key, v)
            else:
                result[key] = value
        return obj
