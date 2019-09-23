from trafaret.utils import fold, split, unfold


class TestUtils:
    def test_split(self):
        data = 'leads[delete][0][id]'
        split_data = split(data, ('[]', '[', ']'))
        assert split_data == ['leads', 'delete', '0', 'id']

    def test_fold(self):
        data = {'leads[delete][0][id]': '42', 'account[subdomain]': 'murmurzet'}
        folded = fold(data, delimeter=('[', ']'))
        assert folded == {
            'leads': {
                'delete': [
                    {'id': '42'}
                ]
            },
            'account': {
                'subdomain': 'murmurzet'
            }
        }

    def test_fold_underscored(self):
        assert fold({'a__a': 4}) == {'a': {'a': 4}}
        assert fold({'a__a': 4, 'a__b': 5}) == {'a': {'a': 4, 'b': 5}}
        assert fold({'a__1': 2, 'a__0': 1, 'a__2': 3}) == {'a': [1, 2, 3]}
        assert fold({'form__a__b': 5, 'form__a__a': 4}, 'form') == {'a': {'a': 4, 'b': 5}}
        assert fold({'form__a__b': 5, 'form__a__a__0': 4, 'form__a__a__1': 7}, 'form') == {'a': {'a': [4, 7], 'b': 5}}
        assert fold({'form__1__b': 5, 'form__0__a__0': 4, 'form__0__a__1': 7}, 'form') == [{'a': [4, 7]}, {'b': 5}]

    def test_unfold(self):
        assert unfold({'a': 4, 'b': 5}) == {'a': 4, 'b': 5}
        assert unfold({'a': [1, 2, 3]}) == {'a__0': 1, 'a__1': 2, 'a__2': 3}
        assert unfold({'a': {'a': 4, 'b': 5}}) == {'a__a': 4, 'a__b': 5}
        assert unfold({'a': {'a': 4, 'b': 5}}, 'form') == {'form__a__a': 4, 'form__a__b': 5}
