class BufferedReader (object):
    '''Provides peek() and pushback() methods for a Python file object.'''

    def __init__(self, fd, bufsize=4096):
        self.held = ''
        self.eof = False
        self.fd = fd

        self.bufsize = bufsize

    def read(self, length):
        '''Return no more than length bytes of data to the caller.'''

        assert length > 0

        while len(self.held) < length and not self.eof:
            chunk = self.fd.read(self.bufsize)
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
        return bytes

    def seek(self, *args, **kwargs):
        '''Calls self.fd seek(...) after invalidating the read buffer.'''
        self.held = ''
        self.eof = False
        return self.fd.seek(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.fd, k)

