import os

def selfdir():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(cwd)

def workdir():
    return os.getenv("WORKDIR")

TMPDIR = os.path.join(selfdir(), 'tmp')
