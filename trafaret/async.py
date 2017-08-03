import inspect
from collections import Mapping as AbcMapping
from .dataerror import DataError
from .lib import (
    call_with_context_if_support,
    _empty,
)


class TrafaretAsyncMixin:
    async def async_check(self, value, context=None):
        if hasattr(self, 'async_transform'):
            return (await self.async_transform(value, context=context))
        return self.check(value, context=context)


class OrAsyncMixin:
    async def async_transform(self, value, context=None):
        errors = []
        for trafaret in self.trafarets:
            try:
                return (await trafaret.async_check(value, context=context))
            except DataError as e:
                errors.append(e)
        raise DataError(dict(enumerate(errors)), trafaret=self)


class AndAsyncMixin:
    async def async_transform(self, value, context=None):
        res = await self.trafaret.async_check(value, context=context)
        if isinstance(res, DataError):
            raise DataError
        res = await self.other.async_check(res, context=context)
        if isinstance(res, DataError):
            raise res
        return res


class ListAsyncMixin:
    async def async_transform(self, value, context=None):
        self.check_common(value)
        lst = []
        errors = {}
        for index, item in enumerate(value):
            try:
                lst.append(await self.trafaret.async_check(item, context=context))
            except DataError as err:
                errors[index] = err
        if errors:
            raise DataError(error=errors, trafaret=self)
        return lst


class TupleAsyncMixin:
    async def async_transform(self, value, context=None):
        self.check_common(value)
        result = []
        errors = {}
        for idx, (item, trafaret) in enumerate(zip(value, self.trafarets)):
            try:
                result.append(await trafaret.async_check(item, context=context))
            except DataError as err:
                errors[idx] = err
        if errors:
            self._failure(errors, value=value)
        return tuple(result)


class MappingAsyncMixin:
    async def async_transform(self, mapping, context=None):
        if not isinstance(mapping, AbcMapping):
            self._failure("value is not a dict", value=mapping)
        checked_mapping = {}
        errors = {}
        for key, value in mapping.items():
            pair_errors = {}
            try:
                checked_key = await self.key.async_check(key, context=context)
            except DataError as err:
                pair_errors['key'] = err
            try:
                checked_value = await self.value.async_check(value, context=context)
            except DataError as err:
                pair_errors['value'] = err
            if pair_errors:
                errors[key] = DataError(error=pair_errors)
            else:
                checked_mapping[checked_key] = checked_value
        if errors:
            raise DataError(error=errors, trafaret=self)
        return checked_mapping


class CallAsyncMixin:
    async def async_transform(self, value, context=None):
        if not inspect.iscoroutinefunction(self.fn):
            return self.transform(value, context=context)
        if self.supports_context:
            res = await self.fn(value, context=context)
        else:
            res = await self.fn(value)
        if isinstance(res, DataError):
            raise res
        else:
            return res


class ForwardAsyncMixin:
    async def async_transform(self, value, context=None):
        if self.trafaret is None:
            self._failure('trafaret not set yet', value=value)
        return (await self.trafaret.async_check(value, context=context))


class DictAsyncMixin:
    async def async_transform(self, value, context=None):
        if not isinstance(value, AbcMapping):
            self._failure("value is not a dict", value=value)
        collect = {}
        errors = {}
        touched_names = []
        for key in self.keys:
            if not callable(key) and not hasattr(key, 'async_call'):
                raise ValueError('Non callable Keys are not supported')
            key_run = call_with_context_if_support(
                getattr(key, 'async_call', key),
                value,
                context=context,
            )
            if inspect.isasyncgen(key_run):
                async for k, v, names in key_run:
                    if isinstance(v, DataError):
                        errors[k] = v
                    else:
                        collect[k] = v
                    touched_names.extend(names)
            else:
                for k, v, names in key_run:
                    if isinstance(v, DataError):
                        errors[k] = v
                    else:
                        collect[k] = v
                    touched_names.extend(names)

        if not self.ignore_any:
            for key in value:
                if key in touched_names:
                    continue
                if key in self.ignore:
                    continue
                if not self.allow_any and key not in self.extras:
                    errors[key] = DataError("%s is not allowed key" % key)
                elif key in collect:
                    errors[key] = DataError("%s key was shadowed" % key)
                else:
                    try:
                        collect[key] = await self.extras_trafaret.async_check(value[key])
                    except DataError as de:
                        errors[key] = de
        if errors:
            raise DataError(error=errors, trafaret=self)
        return collect


class KeyAsyncMixin:
    async def async_call(self, data, context=None):
        if self.name in data or self.default is not _empty:
            if callable(self.default):
                default = self.default()
            else:
                default = self.default
            try:
                value = await self.trafaret.async_check(self.get_data(data, default), context=context)
            except DataError as data_error:
                value = data_error
            yield (
                self.get_name(),
                value,
                (self.name,)
            )
            return

        if not self.optional:
            yield self.name, DataError(error='is required'), (self.name,)
