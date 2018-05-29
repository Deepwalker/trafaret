"""
So, you have some structure from wild. Say this will be some JSON over API.
But you cant change this JSON structure.
"""
sample_data = {
        'userNameFirst': 'Adam',
        'userNameSecond': 'Smith',
        'userPassword': 'supersecretpassword',
        'userEmail': 'adam@smith.math.edu',
        'userRoles': 'teacher, worker, admin',
    }
"""
And you will not save this structure like this, actually you want something
like this
"""
import hashlib

desired_data = {
        'name': 'Adam',
        'second_name': 'Smith',
        'password': hashlib.md5('supersecretpassword'.encode()).hexdigest(),
        'email': 'adam@smith.math.edu',
        'roles': ['teacher', 'worker', 'admin'],
    }

"""
Ok, so you need to convert it somehow. You will write it simple
"""

new_data = {
        'name': sample_data['userNameFirst'],
        'second_name': sample_data['userNameSecond'],
        'password': hashlib.md5(sample_data['userPassword'].encode()).hexdigest(),
        'email': sample_data['userEmail'],
        'roles': [s.strip() for s in sample_data['userRoles'].split(',')]
    }
assert new_data == desired_data, 'Uh oh'


"""
And then you will figure out that you can get much more fields
and decide to optimize your solution with DRY in mind
"""

FIELDS = {
        'userNameFirst': 'name',
        'userNameSecond': 'second_name',
        'userEmail': 'email',
    }
new_data = dict((n2, sample_data[n1]) for n1, n2 in FIELDS.items())
new_data['roles'] = [s.strip() for s in sample_data['userRoles'].split(',')]
new_data['password'] = hashlib.md5(sample_data['userPassword'].encode()).hexdigest()

assert new_data == desired_data, 'Uh oh'


"""
Not so bad, if you have many fields it will save your time. But now you get
new information - 'userEmail' is optional field.
And specification added field 'userTitle', that must be 'bachelor' if not provided'.
Lets solve it!
"""
desired_data['title'] = 'Bachelor' # Update our test to new reality
from collections import namedtuple

Field = namedtuple('Field', 'name optional default')

FIELDS = {
        'userNameFirst': 'name',
        'userNameSecond': 'second_name',
        'userEmail': ('email', '__optional'),
        'userTitle': ('title', 'Bachelor'),
    }

new_data = {}
for old, new in FIELDS.items():
    if isinstance(new, tuple):
        new, default = new
    if old not in sample_data:
        if default == '__optional':
            continue
        new_data[new] = default
    else:
        new_data[new] = sample_data[old]

new_data['roles'] = [s.strip() for s in sample_data['userRoles'].split(',')]
new_data['password'] = hashlib.md5(sample_data['userPassword'].encode()).hexdigest()

assert new_data == desired_data, 'Uh oh'


"""
Hm, ok, so much code, uh oh. I think first variant were more straightforward.
"""
new_data = {
        'name': sample_data['userNameFirst'],
        'second_name': sample_data['userNameSecond'],
        'password': hashlib.md5(sample_data['userPassword'].encode()).hexdigest(),
        'roles': [s.strip() for s in sample_data['userRoles'].split(',')]
    }
if 'userEmail' in sample_data:
    new_data['email'] = sample_data['userEmail']
new_data['title'] = sample_data.get('userTitle', 'Bachelor')

assert new_data == desired_data, 'Uh oh'


"""
Good old code without complicate smell, good, yeah.
But what if you will have more fields? I mean much more, and what will you do?
Dont panic, I have answer, look below.
"""
import trafaret as t

hash_md5 = lambda d: hashlib.md5(d.encode()).hexdigest()
comma_to_list = lambda d: [s.strip() for s in d.split(',')]

converter = t.Dict({
    t.Key('userNameFirst') >> 'name': t.String,
    t.Key('userNameSecond') >> 'second_name': t.String,
    t.Key('userPassword') >> 'password': hash_md5,
    t.Key('userEmail', optional=True, to_name='email'): t.String,
    t.Key('userTitle', default='Bachelor', to_name='title'): t.String,
    t.Key('userRoles', to_name='roles'): comma_to_list,
})

assert converter.check(sample_data) == desired_data
