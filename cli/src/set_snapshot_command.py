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
"""This module contains the support for the set_snapshot command.

The set_snapshot command is used to create a snapshot on a debug target
(Debuggee).
"""

import breakpoint_utils
import command_utils
import format_utils

from exceptions import SilentlyExitError

DESCRIPTION = """
Creates a snapshot on a debug target (Debuggee).  Snapshots allow you to capture
stack traces and local variables from your running service without interfering
with normal operations.

When any instance of the target executes the snapshot location, the
optional condition expression is evaluated. If the result is true (or if
there is no condition), the instance captures the current thread state and
reports it back to Cloud Debugger. Once any instance captures a snapshot,
the snapshot is marked as completed, and it will not be captured again.

It is also possible to inspect snapshot results with the "describe_snapshots"
command.
"""

LOCATION_HELP = """
Specify the location to take a snapshot. Locations are of the form FILE:LINE,
where FILE is the file name, or the file name preceded by enough path components
to differentiate it from other files with the same name. If the file name isn't
unique in the debuggee, the behavior is unspecified.
"""

CONDITION_HELP = """
Specify a condition to restrict when the snapshot is taken. When the snapshot
location is executed, the condition will be evaluated, and the snapshot is
generated if the condition is true.
"""

EXPRESSION_HELP = """
Specify an expression to evaluate when the snapshot is taken. You may specify
--expression multiple times.
"""

CREATE_SUCCESS_MESSAGE = ('Successfully created snapshot with id: '
                          '{breakpoint_id}')

CREATE_FAILED_MESSAGE = ('An unexpected error occurred while trying to set '
                         'the  snapshot.')


class SetSnapshotCommand:
  """This class implements the set_snapshot command.

  The register() method is called by the CLI startup code to install the
  set_snapshot command information, and the cmd() function will be invoked if
  the set_snapshot command was specified by the user.
  """

  def __init__(self):
    pass

  def register(self, args_subparsers, required_parsers, common_parsers):
    parent_parsers = [
        common_parsers.database_url, common_parsers.format,
        common_parsers.debuggee_id
    ]
    parent_parsers += required_parsers
    parser = args_subparsers.add_parser(
        'set_snapshot', description=DESCRIPTION, parents=parent_parsers)
    parser.set_defaults(func=self.cmd)
    parser.add_argument('location', help=LOCATION_HELP)
    parser.add_argument('--condition', help=CONDITION_HELP)
    parser.add_argument('--expression', action='append', help=EXPRESSION_HELP)
    self.args_parser = parser

  def cmd(self, args, cli_services):
    user_output = cli_services.user_output
    firebase_rtdb_service = cli_services.get_firebase_rtdb_service()

    command_utils.validate_debuggee_id(user_output, firebase_rtdb_service,
                                       args.debuggee_id)
    location = breakpoint_utils.parse_and_validate_location(args.location)

    if location is None:
      self.args_parser.error(breakpoint_utils.LOCATION_ERROR_MSG)
      return

    snapshot_data = {'location': location, 'userEmail': cli_services.account}

    # This is a magic Server Value, createTime will get set to the time since
    # UNIX epoch, in milliseconds.
    # https://firebase.google.com/docs/reference/rest/database#section-server-values
    snapshot_data['createTimeUnixMsec'] = {'.sv': 'timestamp'}

    if args.condition:
      snapshot_data['condition'] = args.condition

    if args.expression:
      snapshot_data['expressions'] = args.expression

    breakpoint_id = breakpoint_utils.get_new_breakpoint_id(
        user_output, firebase_rtdb_service, args.debuggee_id)

    if breakpoint_id is None:
      return

    snapshot_data['id'] = breakpoint_id
    path = f'breakpoints/{args.debuggee_id}/active/{breakpoint_id}'
    bp = firebase_rtdb_service.set(path, data=snapshot_data)
    bp = breakpoint_utils.normalize_breakpoint(bp)

    if bp is None:
      user_output.error(CREATE_FAILED_MESSAGE)
      raise SilentlyExitError

    if args.format in ('json', 'pretty-json'):
      format_utils.print_json(
          user_output, bp, pretty=(args.format == 'pretty-json'))
    else:
      user_output.normal(
          CREATE_SUCCESS_MESSAGE.format(breakpoint_id=breakpoint_id))
