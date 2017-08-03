import unittest
import trafaret as t
from trafaret.lib import py3


if py3:
    import asyncio


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
            async def check_int(value):
                return value
            trafaret = t.Int & int & check_int
            res = self.loop.run_until_complete(trafaret.async_check('5'))
            self.assertEqual(res, 5)

