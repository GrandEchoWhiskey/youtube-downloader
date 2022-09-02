from configparser import NoOptionError
import sys

SHORT_JUST = 10
LONG_JUST = 15
USAGE_NOTE = 'Usage: python3 options.py [options]'
HELP_NOTE = 'Help: Type "python3 options.py -h" to get help.'

# -------------------------------------------------------------------------
# Exceptions
# -------------------------------------------------------------------------

class NoTranslationError(Exception): pass
class ArgumentsError(Exception): pass

# -------------------------------------------------------------------------
# Start Option
# -------------------------------------------------------------------------

class _option:

    def __init__(self, shortname:str, longname:str, func=()) -> None:
        self.__short:str = shortname
        self.__long:str = longname
        self.__func = func

    def __eq__(self, other):
        return self.char == other.char and \
            self.string == other.string and \
                self.func == other.func

    def __ne__(self, other):
        return not self.__eq__(other)

    def __get__(self, obj=None, objtype=None) -> dict:
        return {
            "long": self.string,
            "short": self.char,
            "function": self.func
        }

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
        if self.func != ():
            arg_str = ' '.join(list(map(lambda x: x.replace(' ', '-'), self.func.__annotations__.values())))
        short_str = f"-{self.char} {arg_str}"
        long_str = f"--{self.string} {arg_str}"

        return f"{short_str.ljust(SHORT_JUST, ' ')} | {long_str.ljust(LONG_JUST, ' ')} | {help_str}"

    @property
    def string(self) -> str:
        return self.__long

    @property
    def char(self) -> str:
        return self.__short

    @property
    def func(self):
        return self.__func

    @property
    def num_args_min(self):
        return len([x for x in self.func.__annotations__.values() if x[0] != '[' and x[-1] != ']'])

    @property
    def num_args_max(self):
        return len(self.func.__annotations__.values())

# -------------------------------------------------------------------------
# End Option
# Start Translator
# -------------------------------------------------------------------------

class _translator:

    def __init__(self):
        self.__options = []
        self.__fncargs = {}

    def add(self, option):
        self.__options.append(option)

    def __len__(self):
        return len(self.__options)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self.__options):
            self.n += 1
            return self.__options[self.n-1]
        raise StopIteration

    def find_char(self, char):
        for option in self.__options:
            if option.__get__()['short'] == char:
                return option
        return None

    def find_str(self, string):
        for option in self.__options:
            if option.__get__()['long'] == string:
                return option
        return None

    def find_fnc(self, func):
        for option in self.__options:
            if option.__get__()['function'] == func:
                return option
        return None

    def translate(self):
        key = None
        for arg in sys.argv:

            if arg.startswith('--'):
                if opt := self.find_str(arg[2:]):
                    key = opt.__get__()['long']
                    self.__fncargs[key] = []
                    continue

            if arg.startswith('-'):
                if opt := self.find_char(arg[1:]):
                    key = opt.__get__()['long']
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
            func = self.find_str(key).__get__()["function"]
            try:
                func(*args)
            except TypeError as e:
                if str(e).split(' ')[0] == func.__name__ + '()':
                    raise ArgumentsError(f"--{key} {' '.join([x for i, x in enumerate(str(e).split(' ')) if i != 0])}")
                else:
                    raise e                          

    @property
    def options(self):
        return self.__options

# -------------------------------------------------------------------------
# End Trnaslator
# -------------------------------------------------------------------------

_t = _translator()

def add(short, long, func=()):
    _t.add(_option(short, long, func))

def exec():
    try:
        _t.translate()
        _t.run()
    except SystemExit as e:
        sys.exit(e)
    except (NoTranslationError, ArgumentsError) as e:
        sys.exit(f"{e}\n{HELP_NOTE}")
    except Exception as e:
        raise e

def _show_help():
    """
    HELP: Show syntax for usage of this app.
    """
    res = USAGE_NOTE
    res += '\nOPTIONS:'
    for tr in _t:
        res += '\n' + str(tr)
    sys.exit(res)

add('h', 'help', _show_help)
