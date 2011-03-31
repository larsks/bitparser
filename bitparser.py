import os
import sys
import struct

class EndOfData (Exception):
    '''Raised when we run out of data to parse.  This does not
    necessarily mean we have reached EOF.'''
    pass

class BufferedReader (object):
    '''Provides peek() and pushback() methods for a Python file object.'''

    def __init__(self, fd, bufsize=4096):
        self._read = fd.read
        self.held = ''
        self.eof = False
        self.bufsize=bufsize

    def read(self, length):
        '''Return no more than length bytes of data to the caller.'''

        assert length > 0

        while len(self.held) < length and not self.eof:
            chunk = self._read(self.bufsize)
            if chunk:
                self.held += chunk
            else:
                self.eof = True

        if len(self.held) > length:
            self.held, result = (self.held[length :],
                    self.held[: length])
        else:
            self.held, result = '', self.held

        return result

    def pushback(self, bytes):
        '''Push bytes back onto the buffer to be returned by a 
        subsequent read() operation.'''

        self.held = bytes + self.held

    def peek(self, length=1):
        '''Return the next length bytes in the buffer.  These bytes will 
        be returned by a subsequent read() operation.'''

        bytes = self.read(length)
        self.pushback(bytes)
        return data

class Container(dict):
    def __init__ (self, struct, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.__struct__ = struct

    def pack(self):
        '''Return the binary representation of this object.'''

        return self.__struct__.pack(self)

    def write(self, fd):
        '''Write the binary representation of this object to
        a file.'''

        fd.write(self.pack())

class Struct (object):
    def __init__ (self, *fields, **kwargs):
        self.fields = fields
        self.factory = kwargs.get('factory', Container)

    def size(self):
        '''Returns the minimum size of a Struct.  Variable length
        fields (e.g., CStrings) or repeating elements may result in
        a size larger than the number returned by this method.'''

        return sum(f.size() for f in self.fields)

    def unpack(self, fd):
        '''Convert a binary stream into structured data.'''

        values = self.factory(self)

        data = fd.read(self.size())
        fd.pushback(data)

        if len(data) < self.size():
            raise EndOfData()

        for f in self.fields:
            val = f.unpack(fd)
            print 'Unpacked %s = %s' % (f.name, repr(val))
            values[f.name] = val

        return values

    def pack(self, values):
        '''Convert structured data into a binary stream.'''

        bytes = []

        for f in self.fields:
            val = values.get(f.name, getattr(f, 'default', None))
            print 'Packing %s = %s' % (f.name, repr(val))
            bytes.append(f.pack(val))

        return ''.join(bytes)

class Alias(object):
    '''Embed an anonymous Struct inside another struct by given it a name
    and default value.'''

    def __init__ (self, struct, name, default=None):
        self.name = name
        self.struct = struct

        if default is None:
            default = {}

        self.default = default

    def __getattr__ (self, k):
        return getattr(self.struct, k)

class Array (object):
    '''A fixed-length, multiple-value field.'''

    def __init__ (self, name, format, default=None):
        self.name = name
        self.struct = struct.Struct(format)

        if default is None:
            default = (0,) * self.size()

        self.default = default

    def read(self, fd, size):
        bytes = fd.read(size)
        if bytes == '':
            raise EndOfData()
        return bytes

    def unpack(self, fd):
        bytes = self.read(fd, self.size())
        data = self.struct.unpack(bytes)
        return data

    def pack(self, data):
        bytes = self.struct.pack(*data)
        return bytes

    def size(self):
        return self.struct.size


class Field (Array):
    '''A fixed-length, single-value field.'''

    def __init__(self, name, format, default=0):
        super(Field, self).__init__(name, format, default=default)

    def unpack(self, fd):
        return super(Field, self).unpack(fd)[0]

    def pack(self, data):
        return super(Field, self).pack((data,))

class Constant (Field):
    '''A constant value.  The consant value will always be written
    out regardless of the value passed to pack().  The unpack() method will
    raise ValueError if the value read from the stream does not match the
    constant value.'''

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

class CString (Field):
    '''A NUL (or other character) delimited variable-length field.'''
    
    def __init__ (self, name, delim='\x00', default='', **kwargs):
        super(CString, self).__init__(name, '', default=default,
                **kwargs)
        self.delim = delim

    def pack(self, data):
        return '%s%s' % (data, self.delim)

    def unpack(self, fd):
        bytes = []

        while True:
            b = self.read(fd, 1)
            if b == self.delim:
                break
            bytes.append(b)

        return ''.join(bytes)

    def size(self):
        return 0

class BitField (Field):
    '''Treat an integer field as a list of boolean values.'''

    def __init__(self, name, format, fields, **kwargs):
        super(Field, self).__init__(name, format, **kwargs)
        self.fields = fields

    def unpack(self, fd):
        data = super(Field, self).unpack(fd)[0]
        values = {}

        for i,f in enumerate(self.fields):
            if f is None:
                continue
            mask = 1 << i
            values[f] = bool(data & mask)

        return values

    def pack(self, values):
        data = 0
        for i,f in enumerate(self.fields):
            if f is None:
                continue
            if values[f]:
                data = data | (1<<i)

        return super(Field, self).pack((data,))

