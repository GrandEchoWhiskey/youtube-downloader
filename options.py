from collections import OrderedDict
from types import FunctionType
import sys
import inspect

# Defs
SHORT_JUST = 20
LONG_JUST = 30
USAGE_NOTE = 'Usage: python3 options.py [options]'
HELP_NOTE = 'Help: Type "python3 options.py -h" to get help.'

SHOW_HELPNOTE_AFTER_ERROR = True

# Exceptions
class NoTranslationError(ValueError): pass
class ParamError(TypeError): pass
class OptionNameInUse(ValueError): pass
class NoKeyError(ValueError): pass

class var():
    def __init__(self, value):
        self.__val = value
    def get(self): return self.__val
    def set(self, value):
        self.__val = value
    def __str__(self):
        return str(self.__val)

# Parent root class
class _root_option:
    def __init__(self, short:str, long:str) -> None:
        self.__short:str = short
        self.__long:str = long

    @property
    def short(self) -> str: return self.__short

    @property
    def long(self) -> str: return self.__long

    def __eq__(self, other) -> bool:
        return self.short == other.short and self.long == other.long

    def __ne__(self, other) -> bool: return not(self==other)

    def __hash__(self) -> int: return hash((self.short, self.long))

    def __str__(self): pass

# Bool variable setter class
class bool_option(_root_option):

    def __init__(self, short:str, long:str, variable:list, description:str) -> None:
        self.__var = variable
        self.__description = description
        super().__init__(short, long)

    @property
    def var(self): return self.__var

    @var.setter
    def var(self, new):
        self.__var.clear()
        self.__var.extend(new)

    @property
    def description(self): return self.__description

    def __str__(self) -> str:
        short_str = f"-{self.short}"
        long_str = f"--{self.long}"
        return f"{short_str.ljust(SHORT_JUST, ' ')[:SHORT_JUST]} | " + \
            f"{long_str.ljust(LONG_JUST, ' ')[:LONG_JUST]} | {self.description}"

# Variable setter class
class var_option(bool_option):

    def __init__(self, short:str, long:str, variable:list, description:str) -> None:
        super().__init__(short, long, variable, description)

    @property
    def name(self):
        for fi in reversed(inspect.stack()):
            names = [var_name for var_name, var_val in fi.frame.f_locals.items() \
                if var_val is self.var]
            if len(names) > 0:
                return names[0]

    def __str__(self) -> str:
        short_str = f"-{self.short} [*{self.name}]"
        long_str = f"--{self.long} [*{self.name}]"
        return f"{short_str.ljust(SHORT_JUST, ' ')[:SHORT_JUST]} | " + \
            f"{long_str.ljust(LONG_JUST, ' ')[:LONG_JUST]} | {self.description}"


# Function runner class
class func_option(_root_option):

    def __init__(self, short:str, long:str, func:FunctionType) -> None:
        self.__func:FunctionType = func
        self.__params: OrderedDict = self._get_params()
        super().__init__(short, long)

    @property
    def func(self) -> FunctionType: return self.__func

    @property
    def params(self) -> OrderedDict: return self.__params.copy()

    @property
    def min_params(self) -> int:
        return len([p for p in self.params.values() \
            if p.default == p.empty and p.kind != p.VAR_POSITIONAL])

    @property
    def max_params(self) -> int:
        last = self.params.values()[-1]
        if last.kind == last.VAR_POSITIONAL:
            return -1
        return len(self.params.values())

    @property
    def doc_str(self) -> str:
        doc_list = self.func.__doc__.replace('\t', '').split('\n')
        for line in doc_list:
            while line.startswith(' '): line = line[1:]
            if line.startswith('HELP: '): return line[6:]
        return 'No description.'

    @property
    def param_str(self) -> str:
        result:str = ''
        for param in self.params.values():
            if param.kind != param.POSITIONAL_OR_KEYWORD: result += f' [*{param.name}]'
            elif param.default == param.empty: result += f' {param.name}'
            elif param.default != param.empty: result += f' [{param.name}]'
        return result

    def __str__(self) -> str:
        short_str = f"-{self.short}{self.param_str}"
        long_str = f"--{self.long}{self.param_str}"
        return f"{short_str.ljust(SHORT_JUST, ' ')[:SHORT_JUST]} | " + \
            f"{long_str.ljust(LONG_JUST, ' ')[:LONG_JUST]} | {self.doc_str}"

    def _get_params(self) -> OrderedDict:
        sig = inspect.signature(self.func)
        for param in sig.parameters.values():
            if param.kind not in [param.POSITIONAL_OR_KEYWORD, param.VAR_POSITIONAL]:
                raise ParamError
        return sig.parameters.copy()

# Option set override add method to raise error if option in use
class option_set(set):
    def add(self, __element):
        error_str = 'This option name is already in use!'
        if not issubclass(type(__element), _root_option): raise ValueError
        if __element.long in list(map(lambda x: x.long, self)):
            raise OptionNameInUse(f'{error_str} ({__element.long})')
        if __element.short in list(map(lambda x: x.short, self)):
            raise OptionNameInUse(f'{error_str} ({__element.short})')
        super().add(__element)

# Global
_opt_set = option_set()


# Add new variable
def add_var(short:str, long:str, list_ptr:list, description:str='Set Variable'):
    _opt_set.add(var_option(short, long, list_ptr, description))

# Add new bool
def add_bool(short:str, long:str, list_ptr:list, description:str='Set Bool'):
    list_ptr.clear()
    list_ptr.append(False)
    _opt_set.add(bool_option(short, long, list_ptr, description))

# Option function decorator
def option(short, long):

    if type(short) != str or type(long) != str: raise ValueError
    if short == '' or long == '': raise ValueError

    def decorator(func):

        _opt_set.add(func_option(short, long, func))

        def wrapper(*args): return func(*args)

        return wrapper

    return decorator

class _sys_arg_translator(OrderedDict):

    def get_short(self, short):
        for o in _opt_set:
            if o.short == short: return o
        return None
    
    def get_long(self, long):
        for o in _opt_set:
            if o.long == long: return o
        return None

    def translate(self):
        key = None
        for arg in sys.argv[1:]:

            if arg.startswith('--'):
                if opt := self.get_long(arg[2:]):
                    key = opt; self[key] = []; continue

            if arg.startswith('-'):
                if opt := self.get_short(arg[1:]):
                    key = opt; self[key] = []; continue
                
                raise NoTranslationError(f'No option named: {arg}')
            
            if key in self.keys():
                self[key].append(arg); continue

            raise NoKeyError(f'No option before value: {arg}')

    def run(self):
        for key in self.keys():
            args = self[key]

            if type(key) == var_option:
                key.var = args

            if type(key) == bool_option:
                if args != []:
                    raise ParamError(f'--{key.long} does not accept any params.')
                key.var = [True]

            if type(key) == func_option:
                func = key.func
                try:
                    func(*args)
                except TypeError as e:
                    if str(e).split(' ')[0] == func.__name__ + '()':
                        raise ParamError(f"--{key.long} " + \
                            ' '.join([x for i, x in enumerate(str(e).split(' ')) if i != 0]))
                    raise e

def exec():
    try:
        params = _sys_arg_translator()
        params.translate()
        params.run()

    except SystemExit as e:
        sys.exit(e)

    except (NoTranslationError, ParamError, NoKeyError) as e:
        sys.exit(f"{e}" + \
            (f"\n{HELP_NOTE}" if SHOW_HELPNOTE_AFTER_ERROR else ''))

@option('h', 'help')
def show_help():
    """
    HELP: Show syntax for usage of this app.
    """
    res = USAGE_NOTE
    res += '\nOPTIONS:'
    for o in sorted(_opt_set, key=lambda x: x.short):
        res += '\n' + str(o)
    sys.exit(res)
