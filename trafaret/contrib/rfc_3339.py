from dateutil.parser import parse
from datetime import datetime
from .. import Trafaret, str_types


class DateTime(Trafaret):
    """ Class for support parsing date im RFC3339 formats
        via dateutil.parse helper
    """
    convertable = str_types + (datetime,)
    value_type = datetime

    def __init__(self, allow_blank=False):
        self.allow_blank = allow_blank

    def __repr__(self):
        return "<Date(blank)>" if self.allow_blank else "<Date>"

    def check_and_return(self, value):
        if isinstance(value, datetime):
            return value
        try:
            return parse(value)
        except ValueError as e:
            self._failure(e.message)
