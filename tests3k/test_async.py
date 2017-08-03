import asyncio
import unittest
import trafaret as t
from trafaret.lib import py3


async def check_int(value):
    return value


class TestContext(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def test_async_check(self):
        trafaret = t.Int & int
        res = self.loop.run_until_complete(trafaret.async_check('5'))
        self.assertEqual(res, 5)

    def test_async_call(self):
        trafaret = t.Int & int & check_int
        res = self.loop.run_until_complete(trafaret.async_check('5'))
        self.assertEqual(res, 5)

    def test_dict(self):
        trafaret = t.Dict({
            t.Key('b'): t.Int & check_int,
        })
        res = self.loop.run_until_complete(trafaret.async_check({'b': '5'}))
        self.assertEqual(res, {'b': 5})

    def test_list(self):
        trafaret = t.List(t.Int & check_int)
        res = self.loop.run_until_complete(trafaret.async_check(['5']))
        self.assertEqual(res, [5])

    def test_tuple(self):
        trafaret = t.Tuple(t.Null, t.Int & check_int)
        res = self.loop.run_until_complete(trafaret.async_check([None, '5']))
        self.assertEqual(res, (None, 5))

    def test_mapping(self):
        trafaret = t.Mapping(t.String, t.Int & check_int)
        res = self.loop.run_until_complete(trafaret.async_check({'a': '5'}))
        self.assertEqual(res, {'a': 5})

    def test_forward(self):
        trafaret = t.Forward()
        trafaret << t.List(t.Int & check_int)
        res = self.loop.run_until_complete(trafaret.async_check(['5']))
        self.assertEqual(res, [5])
