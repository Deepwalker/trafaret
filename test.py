import sys
import doctest
import trafaret
from trafaret import utils, extras, visitor

tests = (
    doctest.testmod(m=trafaret),
    doctest.testmod(m=extras),
    doctest.testmod(m=utils),
    doctest.testmod(m=visitor),
)


def sum_failed(tests_failed, test_results):
    return tests_failed + test_results.failed

failed = reduce(sum_failed, tests, 0)
if failed:
    print('%s tests failed' % failed)
    sys.exit(1)

