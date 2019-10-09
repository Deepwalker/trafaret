# -*- coding: utf-8 -*-
from trafaret.contrib.object_id import ObjectId, MongoId
from trafaret import extract_error


class TestMongoIdTrafaret:
    def test_mongo_id(self):
        c = MongoId()
        assert isinstance(repr(c), str)
        assert c.check("5583f69d690b2d70a4afdfae") == ObjectId('5583f69d690b2d70a4afdfae')
        res = extract_error(c, 'just_id')
        assert res == "'just_id' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"
        res = extract_error(c, None)
        assert res == "blank value is not allowed"

    def test_mongo_id_blank(self):
        c = MongoId(allow_blank=True)
        assert c.check("5583f69d690b2d70a4afdfae") == ObjectId('5583f69d690b2d70a4afdfae')
        res = extract_error(c, 'just_id')
        assert res == "'just_id' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"
        assert isinstance(c.check(None), ObjectId)

    def test_bad_id(self):
        c = MongoId(allow_blank=True)
        res = extract_error(c, 123)
        assert res == "value is not ObjectId"
        assert isinstance(c.check(None), ObjectId)
