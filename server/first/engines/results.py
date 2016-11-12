#-------------------------------------------------------------------------------
#
#   FIRST Result Abstract Class
#   Author: Angel M. Villegas (anvilleg@cisco.com)
#   Last Modified: August 2016
#
#-------------------------------------------------------------------------------

class Result(object):
    '''Abstract class to encapsulate results returned from Engines'''
    required = {'id', 'creator', 'name', 'prototype', 'comment', 'rank'}

    def __init__(self, obj_id, similarity, **kwargs):
        '''
        Main constructor, all inheriting classes should implement a class method
        _init. Method _init will be passed **kwargs and the method will have
        access to values set in this constructor.
        '''
        self._id = obj_id
        self._similarity = similarity
        self._init(**kwargs)
        self._engines = set()

    def get_metadata(self, db):
        '''Returns a generator containing metadata to be used'''
        while True:
            data = self._get_metadata(db)

            if ((type(data) != dict) or (None in data.values())
                or (not Result.required.issubset(data.keys()))):
                return

            data['similarity'] = self.similarity
            data['engines'] = self.engines
            yield data

    def _init(self, **kwargs):
        '''
        All extending classes should implement this function unless
        no constructor is needed
        '''
        pass

    def _get_metadata(self, db):
        '''
        All extending classes should implement this function.
        This function should return one result at a time since it
        feeds into a generator.
        '''
        raise Exception('Implement')

    @property
    def similarity(self):
        return self._similarity

    @similarity.setter
    def similarity(self, similarity):
        self._similarity = similarity

    @property
    def engines(self):
        return [e.name for e in self._engines]

    @property
    def engine_info(self):
        return {e.name : e.description for e in self._engines}

    def add_engine(self, engine):
        self._engines.add(engine)

    @property
    def id(self):
        return self._id

    def __eq__(self, other):
        if not isinstance(other, Result):
            return False

        return self.id == other.id


#
#   Inheriting Class Implementations
#-------------------------------------
class FunctionResult(Result):
    '''
    This Result class is crafted for general engines that want to return
    a list of functions to the EngineManager

    ID values are 25 hex character string. For metadata created by users,
    not engines, the most significant bit is not set.
    '''
    def _get_metadata(self, db):
        if not hasattr(self, '_metadata'):
            func = db.find_function(_id=self.id)
            if not func:
                return None

            self._metadata = func.metadata
            self._metadata.sort(key=lambda x: x.rank)

        data = None
        if len(self._metadata) > 0:
            metadata = self._metadata.pop()
            data = metadata.dump()
            data['id'] = '0{}'.format(metadata.id)

        return data


class EngineResult(Result):
    '''
    This Result class is crafted for engines that want to return fixed data.
    Make sure the data variable passed to the constructor is a dictionary
    with all the required key values that are expected by EngineManager.

    ID values are 25 hex character string. For metadata created by engines,
    not users, the most significant bit is set.
    '''
    def _init(self, **kwargs):
        self._data = None
        if 'data' in kwargs:
            self._data = kwargs['data']
            self._data['id'] = '8{}'.format(self.id)

    def _get_metadata(self, db):
        data = self._data
        if data:
            self._data = None

        return data
