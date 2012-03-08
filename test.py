import doctest
import trafaret
from trafaret import utils, extras

doctest.testmod(m=trafaret)
doctest.testmod(m=extras)
doctest.testmod(m=utils)
