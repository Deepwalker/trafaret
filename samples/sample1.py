import contract as c
import datetime

date_tuple = c.Dict(year=c.Int, month=c.Int, day=c.Int) >> (lambda d: datetime.datetime(**d))

task = c.Dict({
    'key': c.String(),
    c.Key('timestamp', optional=True): date_tuple,
})

try:
    print task.check({'key': 'foo', 'timestamp': {'year': 2012, 'month': 1, 'day': 12}})
except c.TrafaretValidationError as e:
    print e
