# -*- coding: utf-8 -*-
import unittest
import trafaret as t
from trafaret.contrib.object_id import ObjectId, MongoId
from trafaret import extract_error

class TestMongoIdTrafaret(unittest.TestCase):

    def test_mongo_id(self):
        c = MongoId()
        self.assertIsInstance(repr(c), str)
        self.assertEqual(c.check("5583f69d690b2d70a4afdfae"),
                         ObjectId('5583f69d690b2d70a4afdfae'))
        res = extract_error(c, 'just_id')
        self.assertEqual(res, "'just_id' is not a valid ObjectId, it must be"
                              " a 12-byte input or a 24-character hex string")

        res = extract_error(c, None)
        self.assertEqual(res, "blank value is not allowed")

    def test_mongo_id_blank(self):
        c = MongoId(allow_blank=True)
        self.assertEqual(c.check("5583f69d690b2d70a4afdfae"),
                         ObjectId('5583f69d690b2d70a4afdfae'))
        res = extract_error(c, 'just_id')
        self.assertEqual(res, "'just_id' is not a valid ObjectId, it must be"
                              " a 12-byte input or a 24-character hex string")

        self.assertIsInstance(c.check(None), ObjectId)


    def test_bad_id(self):
        c = MongoId(allow_blank=True)
        res = extract_error(c, 123)
        self.assertEqual(res, "value is not ObjectId")

        self.assertIsInstance(c.check(None), ObjectId)
