import os
import sys

class EndOfData (Exception):
    '''Raised when we run out of data to parse.  This does not
    necessarily mean we have reached EOF.'''
    pass

