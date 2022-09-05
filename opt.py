from collections import OrderedDict
import sys
import inspect
from types import FunctionType



# -------------------------------------------------------------------------

# Start Defines

# -------------------------------------------------------------------------

SHORT_JUST = 10
LONG_JUST = 15
USAGE_NOTE = 'Usage: python3 options.py [options]'
HELP_NOTE = 'Help: Type "python3 options.py -h" to get help.'

# -------------------------------------------------------------------------

# End Defines

# -------------------------------------------------------------------------



# -------------------------------------------------------------------------

# Start Global Variables

# -------------------------------------------------------------------------

_options = []

# -------------------------------------------------------------------------

# End Global Variables

# -------------------------------------------------------------------------



# -------------------------------------------------------------------------

# Start Exceptions

# -------------------------------------------------------------------------

class NoTranslationError(ValueError): pass
class ParamError(TypeError): pass

# -------------------------------------------------------------------------

# End Exceptions

# -------------------------------------------------------------------------



# -------------------------------------------------------------------------

# Start option class

# -------------------------------------------------------------------------

class _option:

    def __init__(self, short:str, long:str, func:FunctionType) -> None:
        self._short:str = short
        self._long:str = long
        self._func:FunctionType = func
        self._params: OrderedDict = self._get_params()

    @property
    def short(self) -> str: return self._short

    @property
    def long(self) -> str: return self._long

    @property
    def func(self) -> FunctionType: return self._func

    @property
    def params(self) -> OrderedDict: return self._params.copy()

    @property
    def min_params(self) -> int:
        return len([p for p in self.params.values() \
            if p.default == p.empty and p.kind != p.VAR_POSITIONAL])

    @property
    def max_params(self) -> int:
        ctr = 0
        for p in self.params.values():
            if p.kind == p.VAR_POSITIONAL:
                return -1
            ctr += 1
        return ctr

    def __eq__(self, other) -> bool:
        return self.short == other.short and \
            self.long == other.long and \
                self.func == other.func

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        help_str = self.func.__doc__.replace('\t', '').split('\n')
        for hs in help_str:
            while hs.startswith(' '):
                hs = hs[1:]
            if hs.startswith('HELP: '):
                help_str = hs[6:]
                break
        if type(help_str) != str:
            help_str = 'No description.'

        arg_str = ''
        for param in self.params.values():
            if param.kind != param.POSITIONAL_OR_KEYWORD:
                arg_str += ' [*args]'
                break
            if param.default == param.empty:
                arg_str += f' {param.name}'
                continue
            if param.default != param.empty:
                arg_str += f' [{param.name}]'
                continue

        short_str = f"-{self.short}{arg_str}"
        long_str = f"--{self.long}{arg_str}"

        return f"{short_str.ljust(SHORT_JUST, ' ')} | {long_str.ljust(LONG_JUST, ' ')} | {help_str}"

    def _get_params(self) -> OrderedDict:
        used_args = False
        sig = inspect.signature(self.func)
        for param in sig.parameters.values():
            if param.kind == param.POSITIONAL_OR_KEYWORD and not used_args:
                continue
            if param.kind == param.VAR_POSITIONAL and not used_args:
                continue
            raise ParamError
        return sig.parameters.copy()

# -------------------------------------------------------------------------

# End option class

# -------------------------------------------------------------------------



# -------------------------------------------------------------------------

# Start sysargs class

# -------------------------------------------------------------------------

class _sysargs:

    def __init__(self):
        self.__fncargs = {}

    def __getitem__(self, name):
        return self.__fncargs[name]

    def __iter__(self):
        return iter(self.__fncargs)

    def keys(self):
        return self.__fncargs.keys()

    def items(self):
        return self.__fncargs.items()

    def values(self):
        return self.__fncargs.values()

    def find_short(self, short):
        for o in _options:
            if o.short == short:
                return o
        return None

    def find_long(self, long):
        for o in _options:
            if o.long == long:
                return o
        return None

    def translate(self):
        key = None
        for arg in sys.argv:

            if arg.startswith('--'):
                if opt := self.find_long(arg[2:]):
                    key = opt.long
                    self.__fncargs[key] = []
                    continue

            if arg.startswith('-'):
                if opt := self.find_short(arg[1:]):
                    key = opt.long
                    self.__fncargs[key] = []
                    continue

                raise NoTranslationError(f'No option named: {arg}')

            if key in self.__fncargs.keys():
                if len(self.__fncargs[key]) == 0:
                    self.__fncargs[key] = [arg]
                    continue

                if len(self.__fncargs[key]) > 0:
                    self.__fncargs[key].append(arg)
                    continue

    def run(self):
        for key in self.__fncargs:
            args = self.__fncargs[key]
            func = self.find_long(key).func
            try:
                func(*args)
            except TypeError as e:
                if str(e).split(' ')[0] == func.__name__ + '()':
                    raise ParamError(f"--{key} {' '.join([x for i, x in enumerate(str(e).split(' ')) if i != 0])}")
                raise e

_sa = _sysargs()

# -------------------------------------------------------------------------

# End sysargs class

# -------------------------------------------------------------------------



# -------------------------------------------------------------------------

# Start option decorator

# -------------------------------------------------------------------------

def option(short, long):

    if type(short) != str or type(long) != str:
        raise ValueError

    def decorator(func):

        _options.append(_option(short, long, func))

        def wrapper(*args):
            return func(*args)

        return wrapper

    return decorator

# -------------------------------------------------------------------------

# End option decorator

# -------------------------------------------------------------------------

def start():
    try:
        _sa.translate()
        _sa.run()

    # Exit
    except SystemExit as e:
        sys.exit(e)

    # Catch NoTranslationError and ParamError to exit with message
    except (NoTranslationError, ParamError) as e:
        sys.exit(f"{e}\n{HELP_NOTE}")

    # Pass Any other Exception
    except Exception as e:
        raise e

@option('h', 'help')
def show_help(a='2', *args):
    """
    HELP: Show syntax for usage of this app.
    """
    res = USAGE_NOTE
    res += '\nOPTIONS:'
    for o in _options:
        res += '\n' + str(o)
    sys.exit(res)

start()