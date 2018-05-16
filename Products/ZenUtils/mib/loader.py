import ast
import os
from functools import wraps

__all__ = ("MIBLoader",)


def coroutine(func):
    """Decorator for initializing a generator as a coroutine.
    """
    @wraps(func)
    def start(*args, **kw):
        coro = func(*args, **kw)
        coro.next()
        return coro
    return start


@coroutine
def broadcast(targets):
    """Send inputs to all targets.
    """
    while True:
        item = (yield)
        for target in targets:
            target.send(item)


@coroutine
def split_into_defs(target):
    """Accepts a complete (or partial) smidump Python string, breaks it
    up into strings containing a single MIB definition, and send them to
    the target.
    """
    while True:
        dump = (yield)
        for mibdef in dump.definitions:
            target.send(mibdef)


@coroutine
def split_into_files(target):
    """Accepts a complete (or partial) smidump Python string, breaks it
    up into strings containing a one or more MIB definitions but all read
    from the same MIB file, and send them to the target.
    """
    while True:
        dump = (yield)
        for filename, mibdefs in dump.files:
            target.send((filename + ".py", mibdefs))


@coroutine
def file_writer(path):
    """Accepts a tuple of a filename and a string containing the contents
    of the file.  The content is saved to a file named by filename.
    """
    while True:
        filename, contents = (yield)
        pathname = os.path.join(path, filename)
        with open(pathname, 'w') as fd:
            fd.write(contents)
            fd.flush()


@coroutine
def transform(expr, target):
    """Use the expr to convert the input and send the result to the target.
    """
    while True:
        item = (yield)
        if not isinstance(item, (list, tuple)):
            item = [item]
        item = expr(*item)
        target.send(item)


@coroutine
def eval_python_literal(target):
    """Accepts a string containing a Python literal expression and compiles
    it into the corresponding object.  The result is forwarded to the target.
    """
    while True:
        definition = (yield)
        mib = ast.literal_eval(definition)
        target.send(mib)


@coroutine
def add_mib(manager, organizer):
    """Accepts Python dict that represents the data for a MIB module and
    adds it to the DMD.
    """
    while True:
        mib = (yield)
        manager.add(mib, organizer)


class MIBLoader(object):
    """Load the output from smidump into the DMD.

    Optionally saves the output to files.
    """

    def __init__(self, manager, organizer, savepath=None):
        """
        """
        self._mgr = manager

        # Build the loader pipeline.  It's as if it were separate
        # Unix commands piped together, i.e.
        #
        # $ cat dump | split_into_defs \
        #            | eval_python_literal \
        #            | add_mib organizer
        #
        loader = split_into_defs(
            eval_python_literal(
                add_mib(manager, organizer)
            )
        )

        if savepath:
            # A save path is specified so prefix a save pipeline to the
            # load pipeline.  There isn't a Unix pipe equivalent because
            # 'broadcast' creates multiple pipelines which isn't possible
            # on the command line.
            loader = split_into_files(
                # Broadcast pushes the output of split_info_files to each
                # of its arguments.
                broadcast(
                    # Save each file into the 'savepath' directory.
                    file_writer(savepath),
                    # split_into_files output is a tuple of two elements,
                    # however, only the second element is needed for the
                    # loader, so use 'transform' to send only the second
                    # element of the tuple to its target.
                    transform(lambda x, y: y, loader)
                )
            )
        self._pipeline = loader

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._pipeline.close()

    def load(self, dump):
        self._pipeline.send(dump)

    def close(self):
        self._pipeline.close()
