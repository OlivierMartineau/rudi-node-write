from time import time

from rudi_node_write.utils.date import now

SHOULD_LOG = True


def log(*args):
    if SHOULD_LOG:
        if len(args) < 2:
            print(f'D {now()}')
        elif len(args) == 2:
            print(f'{args[0]} {now()} [{args[1]}] <')
        elif len(args) == 3:
            print(f'{args[0]} {now()} [{args[1]}] {args[2]}')
        else:
            try:
                print(f'{args[0]} {now()} [{args[1]}] {args[2]}:', *args[3:])
            except UnicodeDecodeError:
                print(f'{args[0]} {now()} [{args[1]}] {args[2]}:', str(*args[3:]))


def log_e(*args):
    log('E', *args)


def log_w(*args):
    log('W', *args)


def log_d(*args):
    log('D', *args)


def log_d_if(should_print: bool, *args):
    if should_print:
        log_d(*args)


def decorator_timer(some_function):
    def _wrap(*args, **kwargs):
        multiplier = 1
        begin = time()
        result = None
        for count in range(multiplier):
            result = some_function(*args, **kwargs)
        duration = (time() - begin) / multiplier
        return result, duration

    return _wrap


def log_assert(cond: bool, ok_tag: str = 'OK', ko_tag: str = '!! KO !!'):
    return ok_tag if cond else ko_tag


if __name__ == '__main__':
    log_d()
    log_d('Test log')
    log_d('Log', 'Test')
    log_d('Log', 'Main', 'test')
