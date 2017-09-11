#! /usr/bin/python
#-------------------------------------------------------------------------------
#
#   Utility Shell to manage User related operations
#   Copyright (C) 2016  Angel M. Villegas
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#-------------------------------------------------------------------------------
#   Python Modules
import re
import os
import sys
from cmd import Cmd
from uuid import uuid4
from pprint import pprint
from argparse import ArgumentParser

#   Add app package to sys path
sys.path.append(os.path.abspath('..'))

#   FIRST Modules
import first.wsgi
import first.settings
from first_core.disassembly import Disassembly
from first_core.models import User

#   Third Party Modules
from django.core.paginator import Paginator

class UserCmd(Cmd):

    def __init__(self):
        Cmd.__init__(self)
        self.prompt = 'FIRST>> '

    def emptyline(self):
        '''Prevent the resubmission of the last command'''
        return

    def default(self, line):
        print '"{}" is unknown command'.format(line)

    def preloop(self):
        print ( '\n\n'
                '+========================================================+\n'
                '|                  FIRST User Shell Menu                 |\n'
                '+========================================================+\n'
                '| list     | List all users currently installed          |\n'
                '| info     | Get info on an user                         |\n'
                '| adduser  | Registers a user manually                   |\n'
                '| enable   | Enable user                                 |\n'
                '| disable  | Disable user account                        |\n'
                '+--------------------------------------------------------+\n')

    def postcmd(self, stop, line):
        if not stop:
            self.preloop()
        return stop

    def do_back(self, line):
        '''Step out of current shell'''
        return 1

    def do_exit(self, line):
        '''Exit shell'''
        sys.exit(0)

    def do_quit(self, line):
        '''Exit shell'''
        sys.exit(0)

    def do_shell(self, line):
        '''Run line in python'''
        exec line

class RootCmd(UserCmd):
    def do_list(self, line):
        print 'list - List all registered users'
        if line in ['help', '?']:
            print 'Usage: list \n'
            return

        print 'Registered Users\n'
        if User.objects.count() == 0:
            print 'No users are registered'
            return

        header = (  '+{}+{}+\n'.format('-' * 39, '-' * 10) +
                    '| {0:^37} | {1:^8} |\n'.format('User Handle', 'Active') +
                    '+{}+{}+'.format('-' * 39, '-' * 10))
        i = 0
        for user in User.objects.all():
            handle = user.user_handle
            if (i % 15) == 0:
                print header
            print '| {0:37} | {1:^8} |'.format(handle, user.active)
            i += 1

        print '+{}+{}+'.format('-' * 39, '-' * 10)

    def do_adduser(self, line):
        print 'info - Manually add user to FIRST'
        if line in ['', 'help', '?']:
            print 'Usage: adduser <user handle> <user email>'
            return

        line = line.split(' ')
        if len(line) !=2:
            print 'The correct arguments were not provided.'
            return

        #   Verify handle provided is valid
        handle, num = self._expand_user_handle(line[0])
        if None in [handle, num]:
            return

        if not re.match(r'^[a-zA-Z\d\._]+@[a-zA-Z\d\.\-_]+(?:\.[a-zA-Z]{2,4})+$', line[1]):
            print 'Invalid email provided.'
            return

        email = line[1]
        user = self._get_db_user_obj(line[0])
        if user:
            print 'User {} already exists'.format(line[0])
            return

        user = User(email=email, handle=handle, number=num, api_key=uuid4())
        user.name = raw_input('Enter user name: ')
        user.save()

        print 'User {0.user_handle} created (api key: {0.api_key})'.format(user)


    def do_info(self, line):
        print 'info - Displays details about a registered User'
        if line in ['', 'help', '?']:
            print 'Usage: info <user handle>'
            return

        user = self._get_db_user_obj(line)
        if not user:
            return

        print ('+' + '-'*65 + '+\n'
               '| Name    | {0.name:53} |\n'
               '+' + '-'*9 + '+' + '-'*55 + '\n'
               '| Email   | {0.email:53} |\n'
               '+' + '-'*9 + '+' + '-'*55 + '\n'
               '| Handle  | {0.user_handle:53} |\n'
               '+' + '-'*9 + '+' + '-'*55 + '\n'
               '| Created | {1:53} |\n'
               '+' + '-'*9 + '+' + '-'*55 + '\n'
               '| Active  | {0.active:53} |\n'
               '+' + '-'*65 + '+\n').format(user, str(user.created))

    def do_enable(self, line):
        print 'enable - Enable user \n'
        if line in ['', 'help', '?']:
            print 'Usage: enable <user handle>'
            return

        user = self._get_db_user_obj(line)
        if not user:
            return

        user.active = True
        user.save()
        print 'User "{}" enabled'.format(line)

    def do_disable(self, line):
        print 'disable - Disable user \n'
        if line in ['', 'help', '?']:
            print 'Usage: disable <user handle>'
            return

        user = self._get_db_user_obj(line)
        if not user:
            return

        user.active = False
        user.save()
        print 'User "{}" disabled'.format(line)

    def _expand_user_handle(self, user_handle):
        matches = re.match('^([^#]+)#(\d{4})$', user_handle)
        if not matches:
            print 'The provided handle is invalid'
            return (None, None)

        handle, num = matches.groups()
        return (handle, int(num))


    def _get_db_user_obj(self, line):
        handle, num = self._expand_user_handle(line)
        if None in [handle, num]:
            return

        user = User.objects.filter(handle=handle, number=int(num))
        if not user:
            print 'Unable to locate User handle "{}"'.format(line)
            return

        return user.get()


if __name__ == '__main__':
    shell = RootCmd()
    if len(sys.argv) > 1:
        shell.onecmd(' '.join(sys.argv[1:]))
        sys.exit(0)

    while 1:
        try:
            shell.cmdloop()
        except Exception as err:
            pprint(err)
