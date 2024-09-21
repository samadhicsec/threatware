

# The pstr class extends the str class to allow str objects to have properties.
# The goal is to be able to use pstr objects instead of str objects when converting a threat model

def ensure_pstr(method):
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        if isinstance(result, str) and not isinstance(result, pstr):
            result = pstr(result)
            if isinstance(self, pstr):
                result.properties = self.properties.copy()
        return result
    return wrapper

class pstr(str):

    _str_value = ""

    def __new__(cls, value, **kwargs):
        obj = super().__new__(cls, value)
        obj.properties = kwargs.get('properties', {})
        return obj

    def __init__(self, value, **kwargs):
        super().__init__()
        if type(value) == pstr:
            self._str_value = value._str_value
        else:
            self._str_value = value

    def to_str(self):
        # Return an instance of the superclass (str)
        return self._str_value
        #return super(pstr, self).__new__(str, self)

# List of str methods to decorate
str_methods = [
    'capitalize', 'casefold', 'center', 'encode', 'expandtabs', 'format', 'format_map',
    'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'partition', 'replace', 'rfind',
    'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'strip',
    'swapcase', 'title', 'translate', 'upper', 'zfill', '__add__', '__contains__',
    '__eq__', '__ge__', '__getitem__', '__getnewargs__', '__gt__', '__hash__', '__iter__',
    '__le__', '__len__', '__lt__', '__mod__', '__mul__', '__ne__', '__repr__', '__rmod__',
    '__rmul__', '__str__'
]

# Decorate the methods
for method_name in str_methods:
    if hasattr(str, method_name):
        method = getattr(str, method_name)
        decorated_method = ensure_pstr(method)
        setattr(pstr, method_name, decorated_method)

# # Example usage
# s = pstr("hello", properties={"key1": "value1"})
# print(type(s.upper()))  # Output: <class '__main__.pstr'>
# print(s.upper().properties)  # Output: {'key1': 'value1'}
# print(type(s.replace("h", "j")))  # Output: <class '__main__.pstr'>
# print(s.replace("h", "j").properties)  # Output: {'key1': 'value1'}