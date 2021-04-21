import contextlib
import copy
import time
import functools
from typing import List, Callable, Union
import inspect
import sys
from functools import wraps

try:
    from contextlib import ContextDecorator
except ImportError:
    raise ImportError('cannot import contextmanager from contextlib. '
                      f'Current python version: {sys.version_info}. Requires version >= 3.2')


# class TimeComputer(ContextDecorator):
#     """
#     Class for running experiments for computing the average time taken
#     to perform computation over a series of N runs. Example:
#
#     time_elapsed_ms = []
#     for i in range(100):
#         with TimeComputer(time_elapsed_ms) as tc:
#             # Run experiment here
#             items = list(range(100000))
#      print(f"Avg time elapsed: {TimeComputer.compute_avg_time(time_elapsed_ms, unit=TimeComputer.Units.MS)}")
#     """
#
#     # TODO: See if there is a better way of doing things
#     class Units:
#         MS = 'milliseconds'
#         NS = 'nanoseconds'
#
#     def __init__(self,
#                  accumulated_time: Union[None, List] = None,
#                  log_interval: int = 1,
#                  log_callback: Callable = print) -> None:
#         self._accumulated_time = accumulated_time
#         self.log_interval = log_interval
#         self.log_callback = log_callback
#
#         # Determines how to handle computation
#         # based on accumulated_time input
#         # since list and floats are computed differently
#         self._handle_computation = None
#
#         self.run_count = 0
#         self._init()
#
#     def __enter__(self) -> None:
#         self.run_count += 1
#         print(f"Run count: {self.run_count}")
#         self.start_time = time.time()
#
#     def _init(self) -> None:
#         self._validate()
#         if isinstance(self._accumulated_time, list):
#             self._handle_computation = self._append_to_list
#         else:
#             self._accumulated_time = 0
#             self._handle_computation = self._compute_int
#
#     def _compute_int(self, time_elapsed: float) -> None:
#         self._accumulated_time += time_elapsed
#
#     def _append_to_list(self, time_elapsed: float) -> None:
#         self._accumulated_time.append(time_elapsed)
#
#     def _validate(self):
#         if not isinstance(self._accumulated_time, list) and self._accumulated_time is not None:
#             # Case: passed in decorator as follows: @TimeComputer
#             if isinstance(self._accumulated_time, Callable):
#                 self._accumulated_time = 0
#                 # Call function once to handle case when
#                 # decorated as @TimeComputer
#                 print(f"MOOOOOO")
#             else:
#                 raise TypeError(f"Accumulated_time must be a list or None. "
#                                 f"Passed in type: {type(self._accumulated_time)}")
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         time_elapsed = time.time() - self.start_time
#         self._handle_computation(time_elapsed)
#         if self.run_count % self.log_interval == 0:
#             self.log_callback(self._accumulated_time, self.run_count)
#
#     def __call__(self, func):
#         self.wrapped_func = func
#
#         @wraps(func)
#         def inner(*args, **kwargs):
#             print("Inner: yeeeeeeee --> ")
#             with self:
#                 return func(*args, **kwargs)
#
#         return inner
#
#     @staticmethod
#     def compute_avg_time(time_list: List, unit: str = None) -> float:
#         avg_time = sum(time_list) / len(time_list)
#         if unit == TimeComputer.Units.MS:
#             avg_time *= 1000
#         return avg_time


class TraceDecorator:
    def __init__(self, func: Callable, verbose: bool = False):
        self.func = func
        self.verbose = verbose
        self.default_index = 0
        self.argspecs = inspect.getfullargspec(func)

    def __call__(self, *args, **kwargs):
        ...
        # use self.param1
        result = self.func(*args, **kwargs)
        # use self.param2
        return result

    def get_default_values(self, *args, **kwargs):
        args_repr = [repr(a) for a in args]  # 1
        default_index = 0
        function_input_str = "Debug: calling --> " + self.func.__name__ + '('
        for i, test in enumerate(args):
            if i < len(args):
                function_input_str += args_repr[i]
            elif i >= len(args) and test not in kwargs:
                function_input_str += f"{test}={self.argspecs.defaults[default_index]}"
                default_index += 1
            else:
                function_input_str += f"{test}={kwargs[test]}"
            # Add commas and space
            function_input_str += ','
            function_input_str += ' '

        # remove trailing ', '
        function_input_str = function_input_str[:-2]
        function_input_str += ')'
        return function_input_str


# make TimeComputer callable via using a function_like
# wrapper
# time_compute = TimeComputer

def write_file(file_name):
    def write(contents_to_write):
        with open(file_name, 'a') as log_file:
            if isinstance(contents_to_write, list):
                log_file.writelines(contents_to_write)
            else:
                log_file.write(contents_to_write)
    return write


def trace(silent: bool = True, path: str = None):
    """
    :param silent: Silently accumulates statistics regarding the
    wrapped function called during the
    :param path: If specified, the log will be stored in the specified file.
    """

    def inner_function(func):
        count = {}
        # Get arguments
        argspecs = inspect.getfullargspec(func)
        function_args = inspect.signature(func)

        # State variables
        count[func] = 0

        # Function that is used to write to certain file
        write_function = write_file(path) if path else print

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            function_name = func.__name__

            # Update state variables
            count[func] += 1

            args_repr = [repr(a) for a in args]  # 1
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
            default_index = 0
            warning_str = ''
            function_input_str = f"Debug: {function_name}("
            i = 0
            for test in argspecs.args:
                if i < len(args):
                    value = args_repr[i]
                elif i >= len(args) and test not in kwargs:
                    value = argspecs.defaults[default_index]
                    default_index += 1
                else:
                    value = kwargs[test]

                function_input_str += f"{test}={value}"
                function_input_str += ','
                function_input_str += ' '
                i += 1

            # remove trailing ', ' --> Handle edge case where function accepts zero arguments
            function_input_str = function_input_str[:-2] if i > 0 else function_input_str
            function_input_str += f') called {count[func]} times.'
            write_function(function_input_str)

            # Get signature of current function
            # TODO: refactor this function as soon as you can ...
            signature = ", ".join(args_repr + kwargs_repr)
            write_function(f"Calling {function_name}({signature})")

            deep_cpy_args = copy.deepcopy(args)
            deep_cpy_kwargs = copy.deepcopy(kwargs)
            value = func(*args, **kwargs)


            # Check if function input has been changed ...
            if deep_cpy_args != args:
                write_function("args has been modified")

            if deep_cpy_kwargs != kwargs:
                write_function("kwargs has been modified")

            write_function(f"{func.__name__!r} returned {value!r}")  # 4

            return value

        # print(argspecs)
        # for i in range(args_len):
        #     try
        #
        # input_log = f"Tracing {func.__name__}{function_args}. " \
        #             f"Called with following values: {func.__name__}, {args} -- {kwargs}"
        # if file is None:
        #     print(input_log)
        # output = func(*args, **kwargs)
        # return output
        return wrapper

    return inner_function


def log_num(time_elapsed, run_count: int):
    print(f"Time elapsed {time_elapsed:.3f} ms, "
          f"Run count: {run_count}, Avg: {(time_elapsed / run_count):.3f} ms")


@trace(silent=True)
def hi(name, teemo, num=20, crazy=''):
    teemo = "captain teeto on duteeeee"
    crazy.append(5)
    print(f"Hi, {name}, {teemo},{num}, {crazy}")


# @TimeComputer(log_interval=5, log_callback=log_num)
# @time_compute(log_callback=log_num)
# @time_compute
def create_long_list(n: int = 1000000):
    return list(range(n))


def yee(func):
    print(f"Outer ")

    @wraps(func)
    def inner(*args, **kwargs):
        output = func(*args, **kwargs)
        print(f"Returning output: {output}")
        return output
    return inner


@trace(silent=True, path="yee.txt")
@yee
def do_something(name):
    print(f"Blah blah blah ... {name}")


if __name__ == "__main__":
    large_ass_num = 10000000
    do_something("yee ...")
    do_something("yee ...")

    # for i in range(10):
    #     test_list = create_long_list(large_ass_num)
    hi("yee", "Captain teemo on duty", crazy=[1, 2, 3, 4])


