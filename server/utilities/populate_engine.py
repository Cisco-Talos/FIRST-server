#-------------------------------------------------------------------------------
#
#   Sends all function data to engine for it to be processed by engine
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
#   Requirements
#   ------------
#   Flask's mongoengine (https://pypi.python.org/pypi/flask-mongoengine/)
#
#-------------------------------------------------------------------------------

#   Python Modules
from argparse import ArgumentParser

#   FIRST Modules
from first_core import EngineManager, DBManager

def main():
    global total, completed, operation_complete

    parser = ArgumentParser(description='Populate engine\'s metadata.')
    parser.add_argument('engines', metavar='E', type=str, nargs='+',
                       help='an engine name to populate')

    args = parser.parse_args()

    db = DBManager.first_db
    if not db:
        print '[Error] Unable to connect to FIRST DB, exiting...'
        return

    #   Get all engines the user entered
    all_engines = EngineManager.get_engines()
    engines = []
    for engine_name in args.engines:
        if engine_name not in all_engines:
            print '[Error] Engine "{}" is not installed'
            continue

        engines.append(all_engines[engine_name])

    if not engines:
        print 'No engines to populate, exiting...'
        return

    print 'Starting to populate engines:\n-\t{}'.format('\n-\t'.join([e.name for e in engines]))
    functions = db.get_all_functions()
    total = len(functions)

    msg = ' [Status] {0:.2f}% Completed ({1} out of {2})'
    errors = []
    i = 0.0
    for function in functions:
        details = function.dump()
        del details['metadata']

        for engine in engines:
            try:
                engine.add(details)

            except Exception as e:
                msg = '[Error] Engine "{}": {}'.format(engine.name, e)
                errors.append(msg)
                print msg

        i += 1
        if 0 == (i % 25):
            print msg.format((i / total) * 100, int(i), total)

    #   Wait for thread to end
    print 'Populating engines complete, exiting...'
    if errors:
        print 'The below errors occured:\n{}'.format('\n'.join(errors))

if __name__ == '__main__':
    main()
