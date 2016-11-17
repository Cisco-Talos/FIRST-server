#-------------------------------------------------------------------------------
#
#   FIRST DB Module for completing operations with the MongoDB backend
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
#   -   flask
#   -   mongoengine
#   -   werkzeug
#
#-------------------------------------------------------------------------------

#   Python Modules
import re
import math
import json
import hashlib
import datetime
import ConfigParser
from hashlib import md5

#   Third Party Modules
import bson
from mongoengine import Q
from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned

#   FIRST Modules
from first.dbs import AbstractDB
from first.models import User, Metadata, Function, Sample, Engine


class FIRSTDB(AbstractDB):
    _name = 'first_db'
    standards = {   'intel16', 'intel32', 'intel64', 'arm32', 'arm64', 'mips',
                    'ppc', 'sparc', 'sysz'}

    #
    #   Functions called by FIRST Framework
    #--------------------------------------------------------------------------
    def __init__(self, config):
        '''
        Constructor.

        @param conf: ConfigParser.RawConfigParser
        '''
        self._is_installed = True
        '''
        section = 'mongodb_settings'

        if (not config.has_section(section)
            or not config.has_option(section, 'db')):
            raise FirstDBError('DB settings not available', skip=True)

            if section.upper() not in app.config:
                app.config[section.upper()] = {}

            app.config[section.upper()]['db'] = conf.get(section, 'db')
            self.db.init_app(app)
        '''

    def get_architectures(self):
        standards = FIRSTDB.standards.copy()
        standards.update(Function.objects().distinct(field='architecture'))
        return list(standards)

    def get_sample(self, md5_hash, crc32, create=False):
        try:
            #   Get Sample from DB
            return Sample.objects.get(md5=md5_hash, crc32=crc32)

        except DoesNotExist:
            if not create:
                return None

            #   Create Sample for DB
            sample = Sample(md5=md5_hash, crc32=crc32)
            sample.last_seen = datetime.datetime.now()
            sample.save()
            return sample

    def sample_seen_by_user(self, sample, user):
        if (not isinstance(sample, Sample)) or (not isinstance(user, User)):
            return None

        if user not in sample.seen_by:
            sample.seen_by.append(user)
            sample.save()

    def checkin(self, user, md5_hash, crc32, sha1_hash=None, sha256_hash=None):
        '''
        TODO:

        @returns String error message on Failure
                 None
        '''
        if not isinstance(user, User):
            return False

        #   Validate data
        if ((not re.match('^[a-f\d]{32}$', md5_hash))
            or (sha1_hash and not re.match('^[a-f\d]{40}$', sha1_hash))
            or (sha256_hash and not re.match('^[a-f\d]{64}$', sha256_hash))):
            return False

        sample = self.get_sample(md5_hash, crc32, True)
        if not sample:
            return False

        sample.last_seen = datetime.datetime.now()
        if user not in sample.seen_by:
            sample.seen_by.append(user)

        if None != sha1_hash:
            sample.sha1 = sha1_hash

        if None != sha256_hash:
            sample.sha256 = sha256_hash

        sample.save()
        return True

    def get_function(self, opcodes, architecture, apis, create=False, **kwargs):
        function = None

        try:
            function = Function.objects.get(sha256=hashlib.sha256(opcodes).hexdigest(),
                                            opcodes=bson.Binary(opcodes),
                                            architecture=architecture,
                                            apis=apis)
        except DoesNotExist:
            #   Create function and add it to sample
            function = Function(sha256=hashlib.sha256(opcodes).hexdigest(),
                                opcodes=bson.Binary(opcodes),
                                architecture=architecture,
                                apis=apis)
            function.save()

        return function

    def get_all_functions(self):
        try:
            return Function.objects.all()

        except:
            return []

    def find_function(self, _id=None, opcodes=None, apis=None, architecture=None, h_sha256=None):
        try:
            #   User function ID
            if None != _id:
                return Function.objects(id=bson.objectid.ObjectId(_id)).get()

            #   User opcodes and apis
            elif None not in [opcodes, apis]:
                return Function.objects(opcodes=opcodes, apis=apis).get()

            #   Use hash, architecture
            elif None not in [architecture, h_sha256]:
                return Function.objects(sha256=h_sha256, architecture=architecture).get()

            else:
                return None

        except DoesNotExist:
            return None

    def add_function_to_sample(self, sample, function):
        if (not isinstance(sample, Sample)) or (not isinstance(function, Function)):
            return False

        if function not in sample.functions:
            sample.functions.append(function)
            sample.save()

        return True

    def add_metadata_to_function(self, user, function, name, prototype, comment, **kwargs):
        if (not isinstance(function, Function)) or (not isinstance(user, User)):
            return None

        #   Check to see if user already has metadata associated with the sample
        metadata = None
        for m in function.metadata:
            if user == m.user:
                if m.has_changed(name, prototype, comment):
                    m.name = [name] + m.name
                    m.prototype = [prototype] + m.prototype
                    m.comment = [comment] + m.comment
                    m.committed = [datetime.datetime.now()] + m.committed

                metadata = m
                break

        if not metadata:
            metadata = Metadata(user=user, name=[name],
                                prototype=[prototype],
                                comment=[comment],
                                committed=[datetime.datetime.now()])
            function.metadata.append(metadata)

        function.save()
        return str(metadata.id)

    def get_metadata_list(self, metadata):
        results = []
        user_metadata, engine_metadata = self.separate_metadata(metadata)

        metadata_ids = map(bson.objectid.ObjectId, user_metadata)
        mongo_filter = Q(metadata__id=metadata_ids[0])
        for mid in metadata_ids[1:]:
            mongo_filter |= Q(metadata__id=mid)

        matches = Function.objects.filter(mongo_filter).only('metadata')
        for function in matches:
            for metadata in function.metadata:
                if metadata.id in metadata_ids:
                    data = metadata.dump()
                    data['id'] = str(metadata.id)
                    results.append(data)

                    #   Remove id from list to shorten list
                    del metadata_ids[metadata_ids.index(metadata.id)]

        for _id in engine_metadata:
            engines = Engine.object(id=_id)
            if (not engines) or (len(engines) > 1):
                continue

            data = {'id' : _id, 'engine' : engine.name,
                    'description' : engine.description}
            results.append(data)

        return results

    def delete_metadata(self, user, metadata_id):
        if not isinstance(user, User):
            return False

        user_metadata, engine_metadata = self.separate_metadata([metadata_id])
        if not user_metadata:
            return False

        #   User must be the creator of the metadata to delete it
        metadata_id = bson.objectid.ObjectId(user_metadata[0])
        try:
            Function.objects(metadata__user=user, metadata__id=metadata_id).update_one(pull__metadata__id=metadata_id)
            return True
        except DoesNotExist:
            return False

    def created(self, user, page, max_metadata=20):
        offset = (page - 1) * max_metadata
        results = []
        pages = 0

        if (offset < 0) or (not isinstance(user, User)):
            return (results, pages)

        try:
            matches = Function.objects(metadata__user=user).only('metadata')
            total = Function.objects(metadata__user=user).count() + 0.0
            pages = int(math.ceil(total / max_metadata))
            if page > pages:
                return (results, pages)

            matches = matches.skip(offset).limit(max_metadata)

        except ValueError:
            return (results, pages)

        for function in matches:
            for metadata in function.metadata:
                if user == metadata.user:
                    temp = metadata.dump()
                    temp['id'] = FIRSTDB.make_id(metadata.id, 0)
                    results.append(temp)

                    #   Bail out of inner loop early since a user can only
                    #   create one metadata entry per function
                    break

        return (results, pages)

    @staticmethod
    def make_id(_id, flags):
        return '{:1x}{}'.format(flags & 0xF, _id)

    def separate_metadata(self, metadata):
        #   Get metadata created by users only, MSB should not be set
        user_metadata = []
        engine_metadata = []
        for x in metadata:
            if len(x) == 24:
                user_metadata.append(x)
            elif (len(x) == 25) and (((int(x[0], 16) >> 3) & 1) == 0):
                user_metadata.append(x[1:])
            elif (len(x) == 25) and (((int(x[0], 16) >> 3) & 1) == 1):
                engine_metadata.append(x[1:])

        return (user_metadata, engine_metadata)

    def metadata_history(self, metadata):
        results = {}
        user_metadata, engine_metadata = self.separate_metadata(metadata)
        e_comment = ('Generated by Engine: {0.name}\n{0.description}\n\n'
                    'Developer: {0.developer.user_handle}')

        if len(user_metadata) > 0:
            metadata_ids = map(bson.objectid.ObjectId, user_metadata)
            mongo_filter = Q(metadata__id=metadata_ids[0])
            for mid in metadata_ids[1:]:
                mongo_filter |= Q(metadata__id=mid)

            matches = Function.objects.filter(mongo_filter).only('metadata')
            for function in matches:
                for metadata in function.metadata:
                    if metadata.id in metadata_ids:
                        data = metadata.dump(True)
                        _id = FIRSTDB.make_id(metadata.id, 0)
                        results[_id] = {'creator' : data['creator'],
                                        'history' : data['history']}
                        #   Remove id from list to shorten list
                        del metadata_ids[metadata_ids.index(metadata.id)]

        #   Provide information for engine created metadata...
        for engine_id in engine_metadata:
            engine = self.get_engine(engine_id)
            if not engine:
                continue
            data = {'creator' : engine.name,
                    'history' : [{'committed' : '',
                                'name' : 'N/A',
                                'prototype' : 'N/A',
                                'comment' : e_comment.format(engine)}]}
            results[FIRSTDB.make_id(engine_id, 8)] = data

        return results

    def applied(self, sample, user, _id, is_engine=False):
        '''
        @returns Boolean. True if added to the applied list
                            False if not added to the applied list
        '''
        if (not isinstance(user, User)) or (not isinstance(sample, Sample)):
            return False

        key = [str(sample.id), str(user.id)]
        if  is_engine:
            engine_id = bson.objectid.ObjectId(_id)
            engine = Engine.objects(id=engine_id,
                                    applied__contains=key)

            #   Check if user has already applied the signature
            if len(engine):
                return True

            try:
                engine = Engine.objects(id=engine_id).get()
            except DoesNotExist:
                #   Engine does not exist
                return False

            engine.applied.append(key)
            engine.save()

        else:
            metadata_id = bson.objectid.ObjectId(_id)
            functions = Function.objects(metadata__id=metadata_id,
                                        metadata__applied__contains=key)

            #   Check if user has already applied the signature
            if len(functions):
                return True

            try:
                function = Function.objects(metadata__id=metadata_id).get()
            except DoesNotExist:
                #   Metadata does not exist
                return False

            #   Get metadata
            for metadata in function.metadata:
                if metadata.id == metadata_id:
                    metadata.applied.append(key)
                    break

            function.save()

        return True

    def unapplied(self, sample, user, _id, is_engine=False):
        '''
        @returns Boolean. True if not in metadata's applied list
                            False if still in the applied list
        '''
        if (not isinstance(sample, Sample)) or (not isinstance(user, User)):
            return False

        key = [str(sample.id), str(user.id)]
        if is_engine:
            engine_id = bson.objectid.ObjectId(_id)
            engine = Engine.objects(id=engine_id,
                                    applied__contains=key)

            #   Check if user has already applied the signature
            if not len(engine):
                return True

            try:
                engine = Engine.objects(id=engine_id).get()
            except DoesNotExist:
                #   Engine does not exist
                return False

            engine.applied.remove(key)
            engine.save()

        else:
            metadata_id = bson.objectid.ObjectId(_id)
            functions = Function.objects(metadata__id=metadata_id,
                                        metadata__applied__contains=key)

            #   Check if user does not have it applied already
            if not len(functions):
                return True

            try:
                function = functions.get()
            except DoesNotExist:
                #   Metadata does not exist
                return True

            #   Get metadata
            for metadata in function.metadata:
                if metadata.id == metadata_id:
                    metadata.applied.remove(key)
                    break

            function.save()

        return True

    def engines(self, active=True):
        return Engine.objects(active=bool(active))

    def get_engine(self, engine_id):
        engines = Engine.objects(id = engine_id)
        if not engines:
            return None

        return engines[0]
