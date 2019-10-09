Web use
=======

Introduction
............

Let's see a simple way to use ``trafaret`` for handle endpoints of rest api in
``aiohttp``.
We'll create a simple rest api for create / update books. The first thing which
we need to do it's describe our schemes of input data in trafaret format.

When we work with form in the web we receive all data in a string format. So
when you want to send a boolean type or list of integers you send some like this.

.. code-block:: python

    "True" # True 
    "1, 2, 3" # [1, 2, 3]

Trafaret designed for solve these problems.

.. code-block:: python

    import trafaret as t

    def comma_to_list(text):
        """Convert string with words separated by comma to list."""
        return [
            s.strip() for s in text.split(',')
        ]

    create_book_chacker = t.Dict({
       'title': t.String,
       'authors': comma_to_list,
       'sold': t.StrBool,
    })


So, when you recive data from form it's not problem for you, because ``StrBool``
and  ``comma_to_list`` prepare data for you in correct format.

.. code-block:: python

    create_book_chacker.check({"title": 'Glue', 'authors': 'Welsh,', 'sold': 'True'}) 
    # {'title': 'Glue', 'authors': ['Welsh', ''], 'sold': True}

But if you receive data as ``json`` it's not very useful for you, because you
can receive data in correct format from the client.

The second problem which trafaret solved it's a `camel/snake case war`.
People why write in python prefe use `snake_case` unlike people why write in `ES`
and use `CamelCase`. Trafaret give an approach for rename key of dictionary for
solve this problem.

.. code-block:: python

    t.Dict({t.Key('userNameFirst') >> 'first_name': t.String}) 

    # or

    t.Dict({t.Key('userNameFirst', to_name='first_name'): t.String}) 

Schemes
.......

So, now we are ready to write our schemes with `trafaret`. We can put this to
the ``utils.py``.

.. code-block:: python

    import trafaret as t

    create_book_chacker = t.Dict({
       t.Key('bookTitle', to_name='title'): t.String,
       t.Key('bookPageCount', to_name='pages'): t.Int,
       t.Key('bookDescription', to_name='description'): t.String(min_length=20),
       t.Key('bookPrice', to_name='price', default=100): t.Int >= 100,
       t.Key('bookIsFree', optional=True, to_name='is_free'): t.Bool,
       t.Key('bookFirstAuthor', to_name='first_author'): t.String(max_length=10),
       t.Key('bookAuthors', to_name='authors'): t.List(t.String(max_length=10)),
    })


    update_user_chacker = create_book_chacker + {"id": t.Int}


Here we created a two schemes. For validate data which need to create a book
and for update. This two schemes differing only by ``id`` field.

After that we can use this checkers for validation data in our web handlers. But
for allocation all logic which connected with trafaret let's create
functions which do it.


.. code-block:: python

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

Handlers
........

Let's use these function in our handlers.

.. code-block:: python

    from aiohttp import web


    # handlers

    async def create_book(req):
        """Hadler for create book"""
        raw_data = await req.json()
        data = prepare_data_for_create_book(raw_data)

        # do something
        ...

        return web.json_response({"created": True})


    async def update_book(req):
        """Handler for update book by id"""
        raw_data = await req.json()
        data = prepare_data_for_update_book(raw_data)

        # do something
        ...

        return web.json_response({"updated": True})


    # setup an application

    app = web.Application()
    app.add_routes([
        web.post('/', create_book),
        web.put('/', update_book)
    ])

    web.run_app(app, port=8000)


After that we can send request to the our server.

.. code-block:: python

    import requests as r 


    data = {
        "bookTitle": "Glue",
        "bookPageCount": 436,
        "bookDescription": "Glue tells the stories of four Scottish boys over four decades...",
        "bookPrice": 423,
        "bookFirstAuthor": "Welsh",
        "bookAuthors": ["Welsh"]
    }
    r.post("http://0.0.0.0:8000/", json=data).text

    # '{"created": true}'

Errors
......

We made validation for input data but also we want eazy show errors  if we have
problem with it.

If input data is not valid then `trafaret` after call check method raise error
(``t.DataError``) connected with that. Let's see easy way to handle all errors
connected with ``trafater``.


.. code-block:: python

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
                    'errors': e.as_dict(value=True)
                })
        
        return inner
    
After that we need to wrap all our handlers.

.. code-block:: python

    @with_error
    async def create_book(req):
        """Hadler for create book""""
        ...

    @with_error
    async def update_book(req):
        """Handler for update book by id"""
        ...

That is it. Now, we receive pretty error messages when our input data is not
valid.

.. code-block:: python

    import requests as r 


    data = {
        "bookTitle": "Glue",
        "bookPageCount": 436,
        "bookDescription": "Glue tells the stories of four Scottish boys over four decades...",
        "bookPrice": 423,
        "bookFirstAuthor": "Welsh",
        "bookAuthors": ["Welsh"]
    }
    r.put("http://0.0.0.0:8000/", json=data).text

    # '{"errors": {"id": "is required"}}'
