import pytest
import trafaret as t


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def check_int(value):
    return value


async def check_int_context(value, context=None):
    if context is not None and value > context:
        return t.DataError('too big')
    return value


async def test_async_check():
    trafaret = t.Int & int
    res = await trafaret.async_check('5')
    assert res == 5


async def test_async_and():
    trafaret = t.ToInt & check_int_context
    await trafaret.async_check(3)  # will not fail
    # not int
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check('blablabla')
    assert res.value.as_dict() == 'value can\'t be converted to int'

    # test context
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check(10, context=5)
    assert res.value.as_dict() == 'too big'


async def test_async_or():
    trafaret = t.ToInt | t.Null
    res = await trafaret.async_check(None)
    assert res is None
    res = await trafaret.async_check('5')
    assert res == 5
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check('blablabla')
    assert res.value.as_dict() == {
        0: 'value can\'t be converted to int',
        1: 'value should be None',
    }

async def test_async_call():
    trafaret = t.ToInt & int & check_int
    res = await (trafaret.async_check('5'))
    assert res == 5


async def test_dict():
    trafaret = t.Dict({
        t.Key('b'): t.ToInt & check_int,
    })
    res = await trafaret.async_check({'b': '5'})
    assert res == {'b': 5}
    # bad value
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({'b': 'qwe'})
    assert res.value.as_dict() == {'b': "value can't be converted to int"}
    # is not a dict
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check(None)
    assert res.value.as_dict() == "value is not a dict"
    # missed key
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({})
    assert res.value.as_dict() == {'b': 'is required'}


async def test_sync_key():
    def simple_key(value):
        yield 'simple', 'simple data', []

    trafaret = t.Dict(simple_key)
    res = await trafaret.async_check({})
    assert res == {'simple': 'simple data'}

    def bad_key(value):
        yield 'simple', t.DataError('bad key here'), []

    trafaret = t.Dict(bad_key)
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({})
    assert res.value.as_dict() == {'simple': 'bad key here'}


async def test_dict_extra_and_ignore():
    trafaret = t.Dict(
        t.Key('a', to_name='A', trafaret=t.String),
        allow_extra=['one_extra'],
        allow_extra_trafaret=t.String,
        ignore_extra=['one_ignore'],
    )
    res = await (trafaret.async_check({'a': 's', 'one_extra': 's', 'one_ignore': 's'}))
    assert res == {'A': 's', 'one_extra': 's'}

    # extra key that is not declared in extra not in ignore
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({'a': 's', 'bad_extra': 's'})
    assert res.value.as_dict() == {'bad_extra': 'bad_extra is not allowed key'}

    # extra key that was shadowed
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({'a': 's', 'A': 's'})
    assert res.value.as_dict() == {'A': 'A key was shadowed'}

    # extra key with failed check
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({'a': 's', 'one_extra': 5})
    assert res.value.as_dict() == {'one_extra': 'value is not a string'}

    # shadowing with allow_extra='*'
    trafaret = trafaret.allow_extra('*')
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check({'a': 's', 'A': 's'})
    assert res.value.as_dict() == {'A': 'A key was shadowed'}


async def test_key_with_callable_default():
    trafaret = t.Dict(
        t.Key('a', default=lambda: 123, trafaret=t.ToInt),
    )
    res = await trafaret.async_check({})
    assert res == {'a': 123}


async def test_list():
    trafaret = t.List(t.ToInt & check_int)
    res = await (trafaret.async_check(['5']))
    assert res == [5]
    with pytest.raises(t.DataError) as res:
        await trafaret.async_check(['5qwe'])
    assert res.value.as_dict() == {0: "value can't be converted to int"}


async def test_tuple():
    trafaret = t.Tuple(t.Null, t.ToInt & check_int)
    res = await (trafaret.async_check([None, '5']))
    assert res == (None, 5)
    with pytest.raises(t.DataError) as res:
        await (trafaret.async_check((None, '5qwe')))
    assert res.value.as_dict() == {1: "value can't be converted to int"}


async def test_mapping():
    trafaret = t.Mapping(t.String, t.ToInt & check_int)
    res = await (trafaret.async_check({'a': '5'}))
    assert res == {'a': 5}
    # bad key
    with pytest.raises(t.DataError) as res:
        await (trafaret.async_check({None: '5'}))
    assert res.value.as_dict() == {None: {"key": "value is not a string"}}
    # bad value
    with pytest.raises(t.DataError) as res:
        await (trafaret.async_check({'b': 'qwe'}))
    assert res.value.as_dict() == {'b': {"value": "value can't be converted to int"}}
    # is not a dict
    with pytest.raises(t.DataError) as res:
        await (trafaret.async_check(None))
    assert res.value.as_dict() == "value is not a dict"


async def test_forward():
    trafaret = t.Forward()
    trafaret << t.List(t.ToInt & check_int)
    res = await (trafaret.async_check(['5']))
    assert res == [5]


async def test_not_set_forward():
    trafaret = t.Forward()
    with pytest.raises(t.DataError) as res:
        await (trafaret.async_check(None))
    assert res.value.as_dict() == "trafaret not set yet"
