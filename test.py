import doctest
import trafaret
from trafaret import utils, extras, visitor

doctest.testmod(m=trafaret)
doctest.testmod(m=extras)
doctest.testmod(m=utils)
doctest.testmod(m=visitor)
