import os
import sys

import struct

class Container(dict):
    def __init__ (self, struct, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.__struct__ = struct

    def pack(self):
        return self.__struct__.pack(self)

class Struct (object):
    def __init__ (self, *fields, **kwargs):
        self.fields = fields
        self.factory = kwargs.get('factory', Container)

    def unpack(self, fd):
        values = self.factory(self)

        for f in self.fields:
            val = f.unpack(fd)
            print 'Unpacked %s = %s' % (f.name, repr(val))
            values[f.name] = val

        return values

    def pack(self, values):
        bytes = []

        for f in self.fields:
            val = values.get(f.name, getattr(f, 'default', None))
            print 'Packing %s = %s' % (f.name, repr(val))
            bytes.append(f.pack(val))

        return ''.join(bytes)

class Alias(object):
    def __init__ (self, struct, name, default=None):
        self.name = name
        self.struct = struct

        if default is None:
            default = {}

        self.default = default

    def __getattr__ (self, k):
        return getattr(self.struct, k)

class Array (object):
    def __init__ (self, name, format, default=None):
        self.name = name
        self.struct = struct.Struct(format)

        if default is None:
            default = (0,) * self.size()

        self.default = default

    def unpack(self, fd):
        bytes = fd.read(self.size())
        data = self.struct.unpack(bytes)
        return data

    def pack(self, data):
        bytes = self.struct.pack(*data)
        return bytes

    def size(self):
        return self.struct.size


class Field (Array):
    def __init__(self, name, format, default=0):
        super(Field, self).__init__(name, format, default=default)

    def unpack(self, fd):
        return super(Field, self).unpack(fd)[0]

    def pack(self, data):
        return super(Field, self).pack((data,))

class Constant (Field):

    def __init__(self, name, format, value, **kwargs):
        super(Constant, self).__init__(name, format, **kwargs)
        self.value = value

    def pack(self, data):
        bytes = self.struct.pack(self.value)
        return bytes

    def unpack(self, fd):
        data = super(Constant, self).unpack(fd)
        if data != self.value:
            raise ValueError('constant %s expected %s, got %s' %
                    (self.name, repr(self.value), repr(data)))
        return data

