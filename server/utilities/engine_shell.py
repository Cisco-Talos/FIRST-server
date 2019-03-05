#! /usr/bin/python
#-------------------------------------------------------------------------------
#
#   Utility Shell to manage Engine related operations
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
import os
import sys
from cmd import Cmd
from pprint import pprint
from argparse import ArgumentParser

#   Add app package to sys path
sys.path.append(os.path.abspath('..'))

#   FIRST Modules
import first.wsgi
import first.settings
from first_core.engines import AbstractEngine
from first_core.disassembly import Disassembly
from first_core import DBManager, EngineManager
from first_core.models import Engine, User, Function

#   Third Party Modules
from django.core.paginator import Paginator

class EngineCmd(Cmd):

    def __init__(self):
        Cmd.__init__(self)
        self.prompt = 'FIRST>> '

    def emptyline(self):
        '''Prevent the resubmission of the last command'''
        return

    def default(self, line):
        print('"{}" is unknown command'.format(line))

    def preloop(self):
        print ( '\n\n'
                '+========================================================+\n'
                '|                 FIRST Engine Shell Menu                |\n'
                '+========================================================+\n'
                '| list     | List all engines currently installed        |\n'
                '| info     | Get info on an engine                       |\n'
                '| install  | Installs engine                             |\n'
                '| delete   | Removes engine record but not other DB data |\n'
                '| enable   | Enable engine (Engine will be enabled)      |\n'
                '| populate | Sending all functions to engine             |\n'
                '| disable  | Disable engine (Engine will be disabled)    |\n'
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
        exec(line)

class RootCmd(EngineCmd):
    def do_list(self, line):
        print('list - List all engines installed')
        if line in ['help', '?']:
            print('Usage: list \n')
            return

        print('Engines currently installed\n')
        if Engine.objects.count() == 0:
            print('No engines are currently installed')
            return

        for engine in Engine.objects.all():
            name = engine.name
            description = engine.description
            print('+{}+{}+'.format('-' * 18, '-' * 50))
            for i in range(0, len(description), 48):
                print('| {0:16} | {1:48} |'.format(name, description[i:i+48]))
                name = ''

        print('+{}+{}+'.format('-' * 18, '-' * 50))

    def do_info(self, line):
        print('info - Displays details about an installed Engine')
        if line in ['', 'help', '?']:
            print('Usage: info <engine name>')
            return

        engine = self._get_db_engine_obj(line)
        if not engine:
            return

        d = engine.description
        d = [d[i:i+53] for i in range(0, len(d), 53)]
        d = ' |\n|             | '.join(['{:53}'.format(x) for x in d])
        print(('+' + '-'*69 + '+\n'
               '| Name        | {0.name:53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Description | {1:53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Developer   | {0.developer.email:53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Path        | {0.path:53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Class Name  | {0.obj_name:53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Rank        | {0.rank:<53} |\n'
               '+' + '-'*13 + '+' + '-'*55 + '\n'
               '| Active      | {0.active:<53} |\n'
               '+' + '-'*69 + '+\n').format(engine, d))

    def do_install(self, line):
        print('install  - Installs engine\n')

        try:
            path, obj_name, email = line.split(' ')
            developer = User.objects.get(email=email)

            __import__(path)
            module = sys.modules[path]

            #   Skip module if the class name not located or is not a class
            if not hasattr(module, obj_name):
                print('[Error] Unable to get {} from {}, exiting...'.format(obj_name, path))
                return

            obj = getattr(module, obj_name)
            if type(obj) != type:
                print('[Error] {} is not the right type, exiting...'.format(obj_name))
                return

            e = obj(DBManager, -1, -1)
            if not isinstance(e, AbstractEngine):
                print('[Error] {} is not an AbstractEngine, exiting...'.format(obj_name))
                return

            e.install()
            engine = Engine.objects.create( name=e.name,
                                            description=e.description,
                                            path=path,
                                            obj_name=obj_name,
                                            developer=developer, active=True)
            print('Engine added to FIRST')
            return

        except ValueError as e:
            print(e)

        except ImportError as e:
            print(e)

        print ( 'Usage: \n'
                'install <pythonic path> <class name> <developer email>\n'
                '\n'
                'Example of pythonic path: app.first.engines.exact_match\n')

    def do_delete(self, line):
        print('delete - Delete engine\n')
        if line in ['', 'help', '?']:
            print('Usage: delete <engine name>')
            return

        engine, e = self._get_engine_by_name(line)
        if (not engine) or (not e):
            return

        e.uninstall()
        engine.delete()

    def do_enable(self, line):
        print('enable - Enable engine \n')
        if line in ['', 'help', '?']:
            print('Usage: enable <engine name>')
            return

        engine = self._get_db_engine_obj(line)
        if not engine:
            return

        engine.active = True
        engine.save()
        print('Engine "{}" enabled'.format(line))

    def do_disable(self, line):
        print('disable - Disable engine \n')
        if line in ['', 'help', '?']:
            print('Usage: disable <engine name>')
            return

        engine = self._get_db_engine_obj(line)
        if not engine:
            return

        engine.active = False
        engine.save()
        print('Engine "{}" disabled'.format(line))

    def do_populate(self, line):
        print('populate - Populate engine by sending all functions to engine\n')
        if line in ['', 'help', '?']:
            print ( 'Usage: populate <engine name> ...\n\n'
                    'More than one engine name can be provided, separate with '
                    'a space\n')
            return

        global total, completed, operation_complete
        populate_engines = line.split(' ')

        db = DBManager.first_db
        if not db:
            print('[Error] Unable to connect to FIRST DB, exiting...')
            return

        #   Get all engines the user entered
        all_engines = EngineManager.get_engines()
        engines = []
        for engine_name in populate_engines:
            if engine_name not in all_engines:
                print('[Error] Engine "{}" is not installed'.format(engine_name))
                continue

            engines.append(all_engines[engine_name])

        if not engines:
            print('No engines to populate, exiting...')
            return

        print('Starting to populate engines:\n-\t{}'.format('\n-\t'.join([e.name for e in engines])))
        functions = db.get_all_functions().order_by('pk')
        total = functions.count()

        msg = ' [Status] {0:.2f}% Completed ({1} out of {2})\r'
        errors = []
        i = 0.0

        offset = 0
        limit = 500
        paginator = Paginator(functions, 100)
        for j in paginator.page_range:
            functions = paginator.page(j)

            for function in functions:
                details = function.dump(True)

                dis = Disassembly(details['architecture'], details['opcodes'])
                if dis:
                    details['disassembly'] = dis

                for engine in engines:
                    try:
                        engine.add(details)

                    except Exception as e:
                        msg = '[Error] Engine "{}": {}'.format(engine.name, e)
                        errors.append(msg)
                        print(msg)

                i += 1
                if 0 == (i % 50):
                    sys.stdout.write(msg.format((i / total) * 100, int(i), total)),
                    sys.stdout.flush()

        sys.stdout.write('\n')
        sys.stdout.flush()
        print('Populating engines complete, exiting...')
        if errors:
            print('The below errors occured:\n{}'.format('\n  '.join(errors)))

    def _get_db_engine_obj(self, name):
        engine = Engine.objects.filter(name=name)
        if not engine:
            print('Unable to locate Engine "{}"'.format(name))
            return

        if len(engine) > 1:
            print('More than one engine "{}" exists'.format(name))
            for e in engine:
                print(' - {}: {}'.format(e.name, e.description))

            return

        return engine.get()

    def _get_engine_by_name(self, name):
        empty_result = (None, None)

        try:
            engine = self._get_db_engine_obj(name)
            if not engine:
                return empty_result

            __import__(engine.path)
            module = sys.modules[engine.path]

            #   Skip module if the class name not located or is not a class
            if not hasattr(module, engine.obj_name):
                print('[Error] Unable to get {0.obj_name} from {0.path}, exiting...'.format(engine))
                return empty_result

            obj = getattr(module, engine.obj_name)
            if type(obj) != type:
                print('[Error] {} is not the right type, exiting...'.format(engine.obj_name))
                return empty_result

            e = obj(DBManager, -1, -1)
            if not isinstance(e, AbstractEngine):
                print('[Error] {} is not an AbstractEngine, exiting...'.format(engine.obj_name))
                return empty_result

        except ValueError as e:
            print(e)

        except ImportError as e:
            print(e)

        return (engine, e)


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
