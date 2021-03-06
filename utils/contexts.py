from __future__ import print_function
import sys
import os
import time
import warnings
import tempfile
import shutil
from contextlib import contextmanager


@contextmanager
def log_out(stdout=sys.stdout, stderr=sys.stderr):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout
    sys.stderr = stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@contextmanager
def silence():
    devnull = open(os.devnull, "w")
    with log_out(stdout=devnull, stderr=devnull):
        try:
            yield
        finally:
            devnull.close()


@contextmanager
def timeit(function):
    start_time = time.time()
    try:
        yield
    finally:
        time_used = time.time() - start_time
        function(time_used)


@contextmanager
def suppress_warnings(warning_classes):
    with warnings.catch_warnings(record=True) as warn_list:
        yield
    for w in warn_list:
        if not issubclass(w.category, warning_classes):
            print("{file:s}:{line:d}: {clas:s}: {message:s}".format(
                file=w.filename,
                line=w.lineno,
                clas=w._category_name,
                message=w.message.message,
            ),
                file=sys.stderr
            )


@contextmanager
def temporary_dir():
    try:
        dir_path = tempfile.mkdtemp()
        yield dir_path
    finally:
        shutil.rmtree(dir_path)


@contextmanager
def temporary_file_path(content="", suffix="", prefix="", text=True):
    """ Returns path to temporary file with content. """
    fd, file_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=text)
    os.close(fd)  # close file descriptor
    if content:
        with open(file_path, "w") as f:
            f.write(content)
    try:
        yield file_path
    finally:
        os.remove(file_path)


@contextmanager
def suppress_exception(exception):
    try:
        yield
    except exception:
        pass
