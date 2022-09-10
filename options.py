from collections import OrderedDict
from types import FunctionType
import inspect
import sys

SHORT_JUST = 20
LONG_JUST = 30
USAGE_NOTE = 'Usage: python3 options.py [options]'
HELP_NOTE = 'Help: Type "python3 options.py -h" to get help.'

SHOW_HELPNOTE_AFTER_ERROR = True

VAR_OPT_DEF_DESC = 'Variable option'
FNC_OPT_DEF_DESC = 'Run function'
BOOL_OPT_DEF_DESC = 'Boolean option'

HELP_STR_REC = 'HELP: '

class NoTranslationError(ValueError): pass
class ParamError(TypeError): pass
class OptionNameInUse(ValueError): pass
class NoKeyError(ValueError): pass

class option_set(set):
    def add(self, __element):
        error_str = 'This option name is already in use!'
        if not issubclass(type(__element), _root_option): raise ValueError
        if __element.long in list(map(lambda x: x.long, self)):
            raise OptionNameInUse(f'{error_str} ({__element.long})')
        if __element.short in list(map(lambda x: x.short, self)):
            raise OptionNameInUse(f'{error_str} ({__element.short})')
        super().add(__element)

_opt_set = option_set()

class var:
    def __init__(self, value, placeholder=None, vtype=None, optional=False, aterisk=False):
        if aterisk and vtype not in [list, None]:
            raise ValueError('Aterisk option is only for list types.')
        if aterisk: vtype=list
        if not aterisk and vtype in [list, set, tuple, dict]:
            raise ValueError('Cannot use list, set, tuple or dict items.')
        if vtype != None and type(value) != vtype:
            raise ValueError('Value does not match the type.')
        self.__name = placeholder
        self.__val = value
        self.__vtype = vtype
        self.__aterisk = aterisk
        self.__optional = optional or aterisk
    def set(self, value):
        if self.__vtype != None and type(value) != self.__vtype:
            raise ValueError('Value does not match the type.')
        self.__val = value
    def get(self): return self.__val
    def __str__(self): return str(self.__val)
    @property
    def optional(self): return self.__optional
    @property
    def aterisk(self): return self.__aterisk
    @property
    def name(self): return self.__name
    @property
    def vtype(self): return self.__vtype

class _root_option:
    def __init__(self, short:str, long:str, min_params:int, \
        max_params:int, str_params:str, description:str) -> None:
        self.__short:str = short
        self.__long:str = long
        self.__max = max_params
        self.__min = min_params
        self.__str = str_params
        self.__description = description

    @property
    def short(self) -> str: return self.__short

    @property
    def long(self) -> str: return self.__long

    def __eq__(self, other) -> bool:
        return self.short == other.short and self.long == other.long

    def __ne__(self, other) -> bool: return not(self==other)

    def __hash__(self) -> int: return hash((self.short, self.long))

    def __str__(self) -> str:
        short_str = f"-{self.short}{self.param_str}"
        long_str = f"--{self.long}{self.param_str}"
        return f"{short_str.ljust(SHORT_JUST, ' ')[:SHORT_JUST]} | " + \
            f"{long_str.ljust(LONG_JUST, ' ')[:LONG_JUST]} | {self.description}"

    @property
    def min_params(self) -> int: return self.__min

    @property
    def max_params(self) -> int: return self.__max

    @property
    def param_str(self) -> str: return self.__str

    @property
    def description(self) -> str: return self.__description

class bool_option(_root_option):
    def __init__(self, short:str, long:str, var_ptr:var, description:str=BOOL_OPT_DEF_DESC) -> None:
        if var_ptr.vtype not in [bool, None]: raise ValueError
        self.__var_ptr = var_ptr
        super().__init__(short, long, 0, 0, '', description)
        _opt_set.add(self)

    @property
    def var_ptr(self) -> var: return self.__var_ptr

class func_option(_root_option):

    def __init__(self, short:str, long:str, func:FunctionType, description:str=None) -> None:
        self.__func:FunctionType = func
        self.__params: OrderedDict = self._params
        min_params = self._min_params
        max_params = self._max_params
        str_params = self._param_str
        description = description if description else self._description
        super().__init__(short, long, min_params, max_params, str_params, description)
        _opt_set.add(self)

    @property
    def func(self) -> FunctionType: return self.__func

    @property
    def params(self) -> OrderedDict: return self.__params.copy()

    @property
    def _min_params(self) -> int:
        return len([p for p in self.params.values() \
            if p.default == p.empty and p.kind != p.VAR_POSITIONAL])

    @property
    def _max_params(self) -> int:
        if len(self.params) == 0: return 0
        last = list(self.params.values())[-1]
        if last.kind == last.VAR_POSITIONAL: return -1
        return len(self.params.values())

    @property
    def _description(self) -> str:
        if not self.func.__doc__:
            return FNC_OPT_DEF_DESC
        doc_list = self.func.__doc__.replace('\t', '').split('\n')
        for line in doc_list:
            while line.startswith(' '): line = line[1:]
            if line.startswith(HELP_STR_REC): return line[6:]
        return FNC_OPT_DEF_DESC

    @property
    def _param_str(self) -> str:
        result:str = ''
        for param in self.params.values():
            if param.kind != param.POSITIONAL_OR_KEYWORD: result += f' [*{param.name}]'
            elif param.default == param.empty: result += f' {param.name}'
            elif param.default != param.empty: result += f' [{param.name}]'
        return result

    @property
    def _params(self) -> OrderedDict:
        sig = inspect.signature(self.func)
        for param in sig.parameters.values():
            if param.kind not in [param.POSITIONAL_OR_KEYWORD, param.VAR_POSITIONAL]:
                raise ParamError('Cannot use keyword function variables.')
        return sig.parameters.copy()

class var_option(_root_option):
    def __init__(self, short:str, long:str, *args, description:str=VAR_OPT_DEF_DESC) -> None:
        if len(args) != len(set(args)) or not len(args): raise ValueError
        for arg in args:
            if type(arg) != var: raise ValueError('Can only use var objects.')
        self.__args = args
        minmax = self._minmax
        super().__init__(short, long, minmax[0], minmax[1], self._str_params, description)
        _opt_set.add(self)

    @property
    def args(self): return self.__args

    def __iter__(self): return iter(self.__args)

    def __next__(self): return next(self.__args)

    def __getitem__(self, item): return self.__args[item]
    
    def __len__(self): return len(self.__args)

    @property
    def _minmax(self) -> tuple:
        used_optional = False; optional = 0; required = 0
        for i, arg in enumerate(self):
            if arg.aterisk:
                if i == len(self)-1: return (required, -1)
                raise ValueError('Cant put aterisk in the middle of args')
            if arg.optional: used_optional = True; optional += 1; continue
            if not arg.optional and used_optional: raise ValueError('Cant use required args after optional.')
            required += 1
        return (required, required+optional)

    @property
    def _str_params(self) -> str:
        result = ''
        for i, arg in enumerate(self):
            name = arg.name
            if not name: name = 'arg'+str(i)
            if arg.aterisk: result += f' [*{name}]'
            elif arg.optional: result += f' [{name}]'
            else: result += f' {name}'
        return result

def option(short, long):

    if type(short) != str or type(long) != str or \
        short == '' or long == '':
        raise ValueError('Option long and short must be valid nonrepetive strings')

    def decorator(func):

        func_option(short, long, func)

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

    def translate(self) -> None:
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

    def _check_var_option(self, key, args) -> bool:
        if type(key) == var_option:
            if not key.max_params == -1 and \
                len(args) > key.max_params:
                raise ParamError(f'--{key.long} takes {key.max_params} positional ' + \
                    f'{"arguments" if key.max_params > 1 else "argument"} but ' + \
                        f'{len(args)} {"was" if len(args) < 2 else "were"} given') 
            if len(args) < key.min_params: raise ParamError(f'--{key.long} missing {key.min_params-len(args)} ' + \
                f'positional {"arguments" if key.min_params-len(args) > 1 else "argument"}')
            return True
        return False
    
    def _set_var_opt_values(self, key, args) -> None:
        for i, arg in enumerate(args):
            if not key[i].aterisk:
                if key[i].vtype != None:
                    try: key[i].set(key[i].vtype(arg)); continue
                    except: raise ParamError(f'Unable to convert {i+1} param of --{key.long} into {key[i].vtype.__name__}')
                key[i].set(arg)
                continue
            if key[i].aterisk:
                key[i].set(args[i:])
                break

    def _check_bool_option(self, key) -> bool:
        if type(key) == bool_option:
            if type(key.var_ptr) != var: raise ValueError
            if key.var_ptr.vtype not in [bool, None]: raise ValueError
            return True
        return False

    def _set_bool_opt_value(self, key) -> None:
        key.var_ptr.set(True)

    def run(self) -> None:
        for key, args in self.items():

            if self._check_var_option(key, args):
                self._set_var_opt_values(key, args)

            if self._check_bool_option(key):
                self._set_bool_opt_value(key)

            if type(key) == func_option:
                func = key.func
                try:
                    func(*args)
                except TypeError as e:
                    if str(e).split(' ')[0] == func.__name__ + '()':
                        raise ParamError(f"--{key.long} " + \
                            ' '.join([x for i, x in enumerate(str(e).split(' ')) if i != 0]))
                    raise e

def exec() -> None:
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

a = var(10, 'x=10', int, optional=True)
b = var(10, 'y=10', int, optional=True)
var_option('a', 'alpha', a, b)

c = var(False)
bool_option('c', 'charlie', c)

def x():
    print('hi')
func_option('b', 'bravo', x)

exec()
print(a.get()*b.get(), c)