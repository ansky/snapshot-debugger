# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" The main Snapshot Debugger CLI startup code.

This module provides the main function, which sets up the CLI commands, parses
the command line arguments and runs the specified command.
"""

import argparse
import sys

from cli_services import CliServices
import cli_common_arguments
from exceptions import SilentlyExitError
from delete_snapshots_command import DeleteSnapshotsCommand
from get_snapshot_command import GetSnapshotCommand
from init_command import InitCommand
from list_debuggees_command import ListDebuggeesCommand
from list_snapshots_command import ListSnapshotsCommand
from set_snapshot_command import SetSnapshotCommand


def main():
  cli_commands = [
      DeleteSnapshotsCommand(),
      GetSnapshotCommand(),
      InitCommand(),
      ListSnapshotsCommand(),
      ListDebuggeesCommand(),
      SetSnapshotCommand()
  ]

  args_parser = argparse.ArgumentParser()
  common_parsers = cli_common_arguments.CommonArgumentParsers()
  required_parsers = cli_common_arguments.RequiredArgumentParsers().parsers

  args_subparsers = args_parser.add_subparsers()

  for cmd in cli_commands:
    cmd.register(
        args_subparsers,
        required_parsers=required_parsers,
        common_parsers=common_parsers)

  args = args_parser.parse_args()

  if 'func' not in args:
    print(
        'Missing required argument, please specify --help for more information',
        file=sys.stderr)

    raise SilentlyExitError

  cli_services = CliServices(args)

  # This will run the appropriate command.
  args.func(args=args, cli_services=cli_services)


if __name__ == '__main__':
  try:
    main()
  except SilentlyExitError:
    sys.exit(1)
