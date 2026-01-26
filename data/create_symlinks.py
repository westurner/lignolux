#!/usr/bin/env python3
"""
create_chat_symlinks
"""



import logging
import subprocess
import sys
import unittest
from pathlib import Path

try:
    import pytest
except ImportError:
    #raise
    class pytest:
        class mark:
            def parametrize(self, *args, **kwargs):
                return [args, kwargs]


__version__ = "0.0.1"


def build_config():
    source_chats = Path('./chats/')
    overlays = {}
    overlays['all'] = Path('chatoverlay') / 'all'
    config = dict(
        source_chats=source_chats,
        overlays=overlays,
        do_print_files=True,
        do_create_overlay_symlinks=True)
    return config


def create_chat_symlinks(source_chats_path, overlays,
                         do_print_files=True,
                         do_create_overlay_symlinks=True) -> None:
    """create chat symlinks

    Arguments:
        conf (str): ...

    Keyword Arguments:
        conf (str): ...

    Returns:
        str: ...

    Yields:
        str: ...

    Raises:
        Exception: ...
    """

    files_glob = source_chats_path.glob('* .md')
    files = list(files_glob)
    # print(files)
    assert len(files), ('files is empty', files)

    overlay_path = overlays['all']

    if do_print_files:
        for f in files:
            pth = Path(f)
            print(pth.name)

    if do_create_overlay_symlinks:

        for f in files:
            pth = Path(f)
            cmd = ('ln', '-s', Path('..') / '..' / pth, overlay_path / pth.name)
            print(cmd)
            subprocess.call(cmd)




class Test_create_chat_symlinks(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_chat_symlinks(self):
        pass

    def tearDown(self):
        pass


#def test_create_chat_symlinks():
@pytest.mark.parametrize('conf', [
    #build_config(),
])
def test_create_chat_symlinks(conf):
    pass


def test_main():
    """test the main(sys.argv) CLI function"""
    pass


@pytest.mark.parametrize('argv', [
    None,
    [],

])
def test_main(argv):
    """test the main(sys.argv) CLI function"""
    output = main(argv)
    pass


def main(argv:list[str]|None=None):
    """
    create_chat_symlinks main() function

    Keyword Arguments:
        argv (list): commandline arguments (e.g. sys.argv[1:])
    Returns:
        int:
    """
    import argparse

    prs = argparse.ArgumentParser(
        usage="%(prog)s [-h][-v] : args")

    prs.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',)
    prs.add_argument(
        '-q', '--quiet',
        dest='quiet',
        action='store_true',)
    prs.add_argument(
        '-t', '--test',
        dest='run_tests',
        action='store_true',)
    prs.add_argument(
        '--version',
        dest='version',
        action='store_true')



    argv = list(argv) if argv else []
    (opts, args) = prs.parse_known_args(args=argv)
    loglevel = logging.INFO
    if opts.verbose:
        loglevel = logging.DEBUG
    elif opts.quiet:
        loglevel = logging.ERROR
    logging.basicConfig(level=loglevel)
    log = logging.getLogger('main')
    log.debug('argv: %r', argv)
    log.debug('opts: %r', opts)
    log.debug('args: %r', args)

    if opts.version:
        print(__version__)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        return unittest.main()

        # import subprocess
        # return subprocess.call(['pytest', '-v', '-l'] + args + [__file__])

    EX_OK = 0

    conf = build_config()
    output = create_chat_symlinks(conf['source_chats'], conf['overlays'])
    print(output)

    return EX_OK


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv[1:]))
