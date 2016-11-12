#-------------------------------------------------------------------------------
#
#   FIRST Engine Abstract Class and Exception Class
#   Author: Angel M. Villegas (anvilleg@cisco.com)
#   Last Modified: May 2016
#
#   Requirements
#   ------------
#   - BSON
#
#-------------------------------------------------------------------------------

#   Python Modules
import re
import sys

#   First Modules
from first.error import FIRSTError
from first.dbs import FIRSTDBManager
from first.engines.results import Result

#   Third Party Modules
from bson.objectid import ObjectId


#   Class for FirstEngine related exceptions
class FIRSTEngineError(FIRSTError):
    _type_name = 'EngineError'
    __skip = False

    def __init__(self, message, skip=False):
        super(FIRSTEngineError, self).__init__(message)
        self.__skip = skip

    @property
    def skip(self):
        return self.__skip

class AbstractEngine(object):
    #   Required Class varaibles
    #   Minimally classes extending this one should fill set these variables
    #   to prevent overloading property functions name, decription and the
    #   constructor
    #   _name: Max length 16 characters
    #   _description: Max length 128 characters
    #--------------------------------------------------------------------------
    _name = 'AbstractEngine'
    _description = ('This is the abstract class for all FIRST Engine '
                    'implementations')
    _required_db_names = []

    _is_operational = False
    _dbs = {}

    #   Require Properties
    #   Should be overloaded if implementation uses different class variables
    #--------------------------------------------------------------------------
    @property
    def is_operational(self):
        return self._is_operational

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    #   Required Methods
    #   At the very least the _add and _scan functions have to be implemented
    #   If additional steps are needed to install or uninstall engine then
    #   _install and _uninstall should be implemented
    #--------------------------------------------------------------------------
    def __init__(self, dbs, engine_id, rank):
        self.id = engine_id
        self.rank = rank

        for db_name in self._required_db_names:
            db = dbs.get(db_name)

            #   If a required db is not installed then exit
            if not db:
                return

            self._dbs[db.name] = db

        self._is_operational = True

    def add(self, function):
        required_keys = {'id', 'apis', 'opcodes', 'architecture', 'sha256'}
        if ((dict != type(function))
            or not required_keys.issubset(function.keys())):
            print 'Data provided is not the correct type or required keys not provided'
            return

        self._add(function)

    def scan(self, opcodes, architecture, apis):
        '''Returns a list of Result objects'''
        results = self._scan(opcodes, architecture, apis)

        if isinstance(results, Result):
            return [results]

        if ((not results) or (type(results) != list)
            or (False in [isinstance(x, Result) for x in results])):
            return []

        return results

    def install(self):
        try:
            self._install()
        except FIRSTEngineError as e:
            if e.message == 'Not Implemented':
                return

            raise e

    def uninstall(self):
        try:
            self._uninstall()
        except FIRSTEngineError as e:
            if e.message == 'Not Implemented':
                return

            raise e

    def _add(self, function):
        '''Returns nothing'''
        raise FIRSTEngineError('Not Implemented')

    def _scan(self, opcodes, architecture, apis):
        '''Returns List of function IDs'''
        raise FIRSTEngineError('Not Implemented')

    def _install(self):
        '''Additional functionality required for installing the Engine [Optional]'''
        raise FIRSTEngineError('Not Implemented')

    def _uninstall(self):
        '''Additional functionality for uninstalling the Engine [Optional]'''
        raise FIRSTEngineError('Not Implemented')



class FIRSTEngineManager(object):
    __db_manager = None

    def __init__(self, db_manager):
        '''
        Constructor. Should locally save db associated with the DB used by
        this class.

        @param dbs: Dictionary of DBs associated with FIRST
                    {db_id : <DB_instance>}
        '''
        if not isinstance(db_manager, FIRSTDBManager):
            db_manager = None

        self.__db_manager = db_manager

    @property
    def _engines(self):
        #   Force reload to get any changes
        db = self.__db_manager.first_db
        active_engines = db.engines()

        #   Dynamically (re)load engines
        engines = []
        for e in active_engines:
            if e.path in sys.modules:
                reload(sys.modules[e.path])
            else:
                __import__(e.path)

            module = sys.modules[e.path]

            #   Skip module if the class name not located or is not a class
            if not hasattr(module, e.obj_name):
                continue
            obj = getattr(module, e.obj_name)
            if type(obj) != type:
                continue

            try:
                e = obj(self.__db_manager, str(e.id), e.rank)
                if not isinstance(e, AbstractEngine):
                    print '[EM] {} is not an AbstractEngine'.format(e)
                    continue

                if e.is_operational:
                    engines.append(e)

            except FIRSTEngineError as e:
                print e

        if not engines:
            print '[EM] Error: No engines could be loaded'

        return engines

    def get_engines(self):
        '''
        @returns Dictionary.
                        { <engine_name> : engine_obj }
        '''
        return {e.name : e for e in self._engines}

    def add(self, function):
        '''
        Generates way to identify the function received. If a way can be
        generated then a unique identifier for the metadata and the db is
        returned as a tuple.

        @param function: Dictionary. Data from the Function model
                                (keys: id, apis, opcodes, architecture, sha256)

        '''
        required_keys = {'id', 'apis', 'opcodes', 'architecture', 'sha256'}
        if (dict != type(function)) or not required_keys.issubset(function.keys()):
            print 'Data provided is not the correct type or required keys not provided'
            return None

        #   Send function details to each registered engine
        errors = {}
        for engine in self._engines:
            try:
                engine.add(function)

            except Exception as e:
                errors[engine.name] = e

        return errors

    def scan(self, user, opcodes, architecture, apis):
        '''
        Uses opcodes and/or info to find matches in db.

        @param      opcodes: String (binary data). All opcodes associated with the function
        @param architecture: String
        @param         apis: List of Strings

        @returns Tuple of (<engine_info:dictionary>, <metadata:list of dictionaries>

                    (   {'<engine_name>' : '<engine_description>', ...},
                        [{  'id' : <metadata_id>,
                            'similarity' : <percentage:0.0 - 100.0>},
                            'engine' : [<engine_name>, ...]
                            'name' : String,
                            'prototype' : String,
                            'comment' : String,
                            'rank' : Integer,
                            'creator' : <handle>,
                         ...
                        ]
                    )

                 Empty list if no signature can be made (Engine decided to skip) or nothing found
                 String error message on Failure
        '''
        db = self.__db_manager.first_db
        if not db:
            return None

        engine_results = {}
        engines = self._engines

        for i in xrange(len(engines)):
            engine = engines[i]
            try:
                results = engine.scan(opcodes, architecture, apis)
                if results:
                    engine_results[i] = results

            except Exception as e:
                print e

        results = {}
        for i, hits in engine_results.iteritems():
            engine = engines[i]

            for result in hits:
                if not isinstance(result, Result):
                    continue

                if result.id not in results:
                    results[result.id] = result

                results[result.id].add_engine(engine)
                if results[result.id].similarity < result.similarity:
                    results[result.id].similarity = result.similarity

        #   Order functions
        cmp_func = lambda x,y: cmp(y.similarity, x.similarity)
        ordered_functions = sorted(results.values(), cmp_func)

        #   Create Metadata list
        #   TODO: Narrow results to top 20 hits, use similarity and metadata rank
        #    to get more likely matches.
        #   - Factor in Engine's ranking
        #   Reduce results down

        #   Get Metadata associated with each result
        metadata_hits = []
        engine_info = {}
        for result in ordered_functions:
            engine_info.update(result.engine_info)

            function_hits = [x for x in result.get_metadata(db)]
            function_hits.sort(key=lambda x: (-x['similarity'], -x['rank']))

            #   Add top 10 results per function to metadata_hits
            metadata_hits += function_hits[:10]


        metadata_hits.sort(key=lambda x: (-x['similarity'], -x['rank']))
        return (engine_info, metadata_hits[:30])
