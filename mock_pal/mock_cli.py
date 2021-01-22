#! /usr/bin/env python3
# Copyright (c) 2020 HAW Hamburg
#
# This file is subject to the terms and conditions of the MIT License. See the
# file LICENSE in the top level directory for more details.
# SPDX-License-Identifier:    MIT
"""Mock cli to a mock device.

Usage:
    mock_cli.py [-h]
                  [--loglevel LOGLEVEL]
                  [--logmodules LOGMODULES [LOGMODULES ...]]
                  [--port PORT]
                  [--mm_path MM_PATH]

    optional arguments:
        -h, --help            show this help message and exit
        --loglevel LOGLEVEL   Python logger log level, defaults to INFO.

        --logmodules LOGMODULES [LOGMODULES ...]
                                Modules to enable logging.

        --port PORT, -p PORT  Serial device name, defaults to None.
        --mm_path MM_PATH     Path to memory map, defaults to None.

"""
import logging
import argparse
from mock_pal.mock_dev import MockDev, VirtualPortRunner
from mock_pal.mock_dev import log_level_module_control
from mock_pal.mock_if import MockIf
from mm_pal import MmCmd, serial_connect_wizard, write_history_file


class MockCli(MmCmd):
    """Command loop for the mock interface."""

    prompt = "MOCK: "

    def __init__(self, **kwargs):
        """Mock cli command loop wrapper.

        Args:
            **kwargs:
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if 'dev_driver' in kwargs:
            super().__init__(kwargs['dev_driver'])
            return
        port = kwargs.get('port', None)
        if port is None:
            super().__init__(serial_connect_wizard(MockIf, **kwargs))
        else:
            super().__init__(MockIf(**kwargs))
        self.logger.debug("__init__(%r)", kwargs)

    def do_special_cmd(self, arg):
        """Do nothing but show how to use special commands.

        Usage:
            special_cmd
        """
        try:
            resp = self.dev_driver.special_cmd()
            print(resp)
        except (TypeError, ValueError, SyntaxError) as exc:
            print(exc)
            print("args", arg)


def main():
    """Run MockCli command loop."""
    parser = argparse.ArgumentParser()

    # pylint: disable=duplicate-code
    parser.add_argument('--loglevel', default='INFO',
                        help='Python logger log level, defaults to INFO.')
    parser.add_argument('--logmodules', nargs='+', default=None,
                        help='Modules to enable logging.')
    parser.add_argument('--port', '-p', default=None,
                        help='Serial device name, defaults to None.')
    parser.add_argument('--mm_path', default=None,
                        help='Path to memory map, defaults to None.')
    parser.add_argument('--sim', default=False, action='store_true',
                        help='Simulate device, defaults to False.')
    pargs = parser.parse_args()
    log_level_module_control(pargs)

    vpr = None
    mdev = None
    port = pargs.port

    if pargs.sim:
        vpr = VirtualPortRunner()
        mdev = MockDev(port=vpr.mock_port)
        mdev.start_thread_loop(func=mdev.run_app_json)
        port = vpr.ext_port
    try:
        MockCli(port=port, mm_path=pargs.mm_path).cmdloop()
    except KeyboardInterrupt:
        write_history_file()
        print("")
    finally:
        if pargs.sim:
            mdev.end_thread_loop()


if __name__ == '__main__':
    main()
