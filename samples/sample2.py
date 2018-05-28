from __future__ import print_function

import datetime
from time import gmtime
import trafaret as t


### Sample simple validation
print(t.Int().check(3))
print(t.Float().check(2.3))


### Sample complex validation
print(t.Dict({'name': t.String}).check({'name': 'Jeff'}))


### Sample simple conversion
print(t.Int().check('3'))
print(t.Int().check(3.0))
print(t.Float().check('2.3'))


### Sample UNIX time to datetime conversion
def from_ts(ts):
    return  datetime.datetime(*gmtime(ts)[:5])
print((t.Int() >> from_ts).check(1234234234))


### Sample dict to datetime conversion
date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))

task = t.Dict({
    'key': t.String(),
    t.Key('timestamp', optional=True): date,
})

print(task.check({'key': 'foo', 'timestamp': {'year': 2012, 'month': 1, 'day': 12}}))


### Dict keys conversion
c = t.Dict({t.Key('userNameJava') >> 'name': t.String})
print(c.check({'userNameJava': 'Adam'}))


### Dict key conversion + fold
from trafaret.utils import fold
c = t.Dict({t.Key('uNJ') >> 'user__name': t.String}) >> fold
print(c.check({'uNJ': 'Adam'}))


### Regex String
c = t.String(regex=r'name=(\w+)') >> (lambda m: m.groups()[0])
print(c.check('name=Jeff'))
