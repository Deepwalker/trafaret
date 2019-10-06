Errors
======

DataError
.........

Exception class that is used in the library. Exception hold errors in error
attribute. For simple checkers it will be just a string. For nested structures
it will be dict instance.

``DataError`` instance has four important properties:

    - `error` - error message describing what happened
    - `code` - error code (this code you can use for replace an error message)
    - `value` - raw value
    - `trafaret` - checker instance which raised an error


``DataError`` instance has two methods for represent full information about errors

    - `as_dict` - the simple representation of errors as dictionary
    - `to_struct` - more information than in `as_dict`.
      Here we can see code of error and other helpful information.

.. code-block:: python

    login_validator = t.Dict({'username': t.String(max_length=10), 'email': t.Email}) 

    try:
        login_validator.check({'username': 'So loooong name', 'email': 'misha'})
    except t.DataError as e:
        print(e.as_dict())
        print(e.to_struct())
    
    # {
    #    'username': 'String is longer than 10 characters',
    #    'email': 'value is not a valid email address'
    # }

    # {
    #    'code': 'some_elements_did_not_match',
    #    'nested': {
    #        'username': {
    #            'code': 'long_string',
    #            'message': 'String is longer than 10 characters'
    #        },
    #        'email': {
    #            'code': 'is_not_valid_email',
    #            'message': 'value is not a valid email address'
    #        }
    #    }
    # }


Also, as_dict and to_struct have optional parameter ``value`` that set to False
as default. If set it to ``True`` trafaret will show bad value in error message.


Create custom error renderer
............................
