# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

import attr

from subiquitycore.context import with_context

from subiquity.controller import SubiquityTuiController
from subiquity.ui.views import IdentityView, IdentityHostnameView

log = logging.getLogger('subiquity.controllers.identity')

AUTOINSTALL_SCHEMA = {
    'type': 'object',
    'properties': {
        'realname': {'type': 'string'},
        'username': {'type': 'string'},
        'hostname': {'type': 'string'},
        'password': {'type': 'string'},
        },
    'required': ['username', 'hostname', 'password'],
    'additionalProperties': False,
    }

class IdentityController(SubiquityTuiController):

    autoinstall_key = model_name = "identity"
    autoinstall_schema = AUTOINSTALL_SCHEMA

    def load_autoinstall_data(self, data):
        if data is not None:
            self.model.add_user(data)

    @with_context()
    async def apply_autoinstall_config(self, context=None):
        if not self.model.user:
            if 'user-data' not in self.app.autoinstall_config:
                raise Exception("no identity data provided")

    def start_ui(self):
        self.ui.set_body(IdentityView(self.model, self))
        if all(elem in self.answers for elem in ['realname', 'username',
                                                 'password']):
            d = {
                'realname': self.answers['realname'],
                'username': self.answers['username'],
                'password': self.answers['password'],
                }
            self.done(d)

    def cancel(self):
        self.app.prev_screen()

    def done(self, user_spec):
        safe_spec = user_spec.copy()
        safe_spec['password'] = '<REDACTED>'
        log.debug(
            "IdentityController.done next_screen user_spec=%s",
            safe_spec)
        self.model.add_user(user_spec)
        self.configured()
        self.app.next_screen()

    def make_autoinstall(self):
        if self.model.user is None:
            return {}
        r = attr.asdict(self.model.user)
        return r


class IdentityHostnameController(SubiquityTuiController):

    # Hostname was split out from identity, to maintain backwards
    # compabilility, this controller continues to use identity's autoinstall
    # key.
    autoinstall_key = "identity"
    model_name = "identityhostname"
    autoinstall_schema = AUTOINSTALL_SCHEMA

    def interactive(self):
        if not self.app.autoinstall_config:
            return True
        i_sections = self.app.autoinstall_config.get(
            'interactive-sections', [])
        # Use model_name instead of autoinstall_key when checking for
        # interactive-sections specification.
        return '*' in i_sections or self.model_name in i_sections

    def load_autoinstall_data(self, data):
        if data is not None:
            self.model.add_hostname(data)

    @with_context()
    async def apply_autoinstall_config(self, context=None):
        if not self.model.hostname:
            if 'user-data' not in self.app.autoinstall_config:
                raise Exception("no identity hostname data provided")

    def start_ui(self):
        self.ui.set_body(IdentityHostnameView(self.model, self))
        if 'hostname' in self.answers:
            self.done({'hostname':  self.answers['hostname']})

    def cancel(self):
        self.app.prev_screen()

    def done(self, spec):
        log.debug(
            "IdentityHostnameController.done next_screen spec=%s",
            spec)
        self.model.add_hostname(spec)
        self.configured()
        self.app.next_screen()

    def make_autoinstall(self):
        return {'hostname':  self.model.hostname}
