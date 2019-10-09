import trafaret as t


def check_context(value, context=None):
    if value != context:
        return t.DataError('have not context there')
    return value


CONTEXT_TRAFARET = (t.String() | t.Int()) & t.Any & check_context


class TestContext:
    def test_context(self):
        assert CONTEXT_TRAFARET(123, context=123) == 123

    def test_dict_context(self):
        trafaret = t.Dict({
            t.Key('b'): CONTEXT_TRAFARET,
        })
        assert trafaret({'b': 123}, context=123) == {'b': 123}

    def test_list(self):
        trafaret = t.List(CONTEXT_TRAFARET)
        assert trafaret([123], context=123) == [123]

    def test_tuple(self):
        trafaret = t.Tuple(CONTEXT_TRAFARET)
        assert trafaret([123], context=123) == (123,)

    def test_mapping(self):
        trafaret = t.Mapping(CONTEXT_TRAFARET, CONTEXT_TRAFARET)
        assert trafaret({123: 123}, context=123) == {123: 123}

    def test_forward(self):
        trafaret = t.Forward()
        trafaret << t.List(CONTEXT_TRAFARET)
        assert trafaret([123], context=123) == [123]
