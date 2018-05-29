from __future__ import print_function

import trafaret as t
import datetime

date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))

task = t.Dict({
    'key': t.String(),
    t.Key('timestamp', optional=True): date,
})

try:
    print(task.check({'key': 'foo', 'timestamp': {'year': 2012, 'month': 1, 'day': 12}}))
except t.DataError as e:
    print(e)
