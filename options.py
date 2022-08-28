from sys import argv, exit as leave

SHORT_JUST = 10
LONG_JUST = 15
HELP_NOTE = ''

__translation: list = []
__arguments:dict = {}

class __option:
    def __init__(self, shortname:str, longname:str, func=None, args:str='') -> None:
        self.__short:str = shortname
        self.__long:str = longname
        self.__func = func
        self.__args = args

    def __str__(self) -> str:
        fnc_name = self.func.__doc__ if self.func.__doc__ else 'No description.'
        return f"-{f'{self.char} {self.__args}'.ljust(SHORT_JUST, ' ')} | --{f'{self.name} {self.__args}'.ljust(LONG_JUST, ' ')} | {fnc_name}"

    @property
    def name(self) -> str:
        return self.__long

    @property
    def char(self) -> str:
        return self.__short

    @property
    def func(self):
        return self.__func

    def __get__(self) -> dict:
        return {
            "long": self.name,
            "short": self.char,
            "function": self.func
        }


def add(short, long, func=None, args=''):
    __translation.append(__option(short, long, func, args))


def exec():
    key = None
    for arg in argv:
        if arg.startswith('-'):
            tmp = arg[1:]
            found = False
            for tr in __translation:
            
                if tmp.startswith('-'):
                    if tmp[1:] == tr.__get__()["long"]:
                        found = True
                elif tmp == tr.__get__()["short"]:
                    found = True
            
                if found:
                    key = tr.__get__()["long"]
                    __arguments[key] = []
                    break
            
            if found:
                continue

            raise ValueError
        
        if key in __arguments.keys():
            
            if len(__arguments[key]) == 0:
                __arguments[key] = [arg]
                continue

            if len(__arguments[key]) > 0:
                __arguments[key].append(arg)
                continue

    __run()

def __run():
    for key in __arguments.keys():
        args = __arguments[key]
        for tr in __translation:
            if tr.__get__()["long"] == key:
                if tr.__get__()["function"]:
                    tr.__get__()["function"](*args)

def __show_help(*args):
    """Show syntax for usage of this app."""
    print(HELP_NOTE)
    print('OPTIONS:')
    for tr in __translation:
        print(str(tr))
    leave(0)


add('h', 'help', __show_help)
