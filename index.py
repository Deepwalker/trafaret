from aiohttp import web

import trafaret as t
from trafaret.keys import subdict


def author_validation(data):
	"""Test that first author exist in list of all authors."""
	if data['first_author'] not in data['authors']:
		raise t.DataError('first_author must exist in authors')


authors = subdict(
    'authors',
    t.Key('bookFirstAuthor', to_name='first_author', trafaret=t.String(max_length=10)),
    t.Key('bookAuthors', to_name='authors', trafaret=t.List(t.String(max_length=10))),
    trafaret=author_validation,
)

create_book_chacker = t.Dict({
   t.Key('bookTitle', to_name='title'): t.String,
   t.Key('bookPageCount', to_name='pages'): t.Int,
   t.Key('bookDescription', to_name='description'): t.String(min_length=20),
   t.Key('bookPrice', to_name='price', default=100): t.Int >= 100,
   t.Key('bookIsFree', optional=True, to_name='is_free'): t.Bool,
}) + t.Dict(authors)


update_user_chacker = create_book_chacker + {"id": t.Int}


users = {}


from functools import wraps

def with_error(fn):
    """
    This is decorator for wrapping web handlers which need to represent
    errors connected with validation if they exist.
    """

    @wraps(fn)
    async def inner(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except t.DataError as e:
            return web.json_response({
                'errors': e.as_dict()
            })

    return inner


def prepare_data_for_create_book(data):
    valid_data = create_book_chacker.check(data)

    # do something else
    ...

    return valid_data

def prepare_data_for_update_book(data):
    valid_data = update_user_chacker.check(data)

    # do something else
    ...

    return valid_data


@with_error
async def create_book(req):
	raw_data = await req.json()
	data = prepare_data_for_create_book(raw_data)

	# do something
	...

	return web.json_response({"created": True})


@with_error
async def update_book(req):
	raw_data = await req.json()
	data = prepare_data_for_update_book(raw_data) 

	# do something
	...

	return web.json_response({"updated": True})


app = web.Application()

app.add_routes([
	web.post('/', create_book),
	web.put('/', update_book)
])

web.run_app(app, port=9000)
