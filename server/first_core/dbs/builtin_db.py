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
#   -   werkzeug
#
#-------------------------------------------------------------------------------

#   Python Modules
import re
import math
import json
import hashlib
import configparser 
from hashlib import md5

#   Third Party Modules
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

#   FIRST Modules
from first_core.dbs import AbstractDB
from first_core.util import make_id, parse_id, separate_metadata, \
                            is_engine_metadata
from first_core.models import User, Sample, \
                                Engine, \
                                Metadata, MetadataDetails, AppliedMetadata, \
                                Function, FunctionApis


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

        @param conf: configparser.RawConfigParser
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
        field = 'architecture'
        architectures = Function.objects.values(field).distinct()

        standards = FIRSTDB.standards.copy()
        standards.update({x[field] for x in architectures})
        return list(standards)

    def get_sample(self, md5_hash, crc32, create=False):
        try:
            #   Get Sample from DB
            return Sample.objects.get(md5=md5_hash, crc32=crc32)

        except ObjectDoesNotExist:
            if not create:
                return None

            #   Create Sample for DB
            sample = Sample(md5=md5_hash, crc32=crc32)
            sample.last_seen = timezone.now()
            sample.save()
            return sample

        except MultipleObjectsReturned:
            #   TODO: log occurance
            raise

    def sample_seen_by_user(self, sample, user):
        if (not isinstance(sample, Sample)) or (not isinstance(user, User)):
            return None

        if not Sample.objects.filter(pk=sample.id, seen_by=user).count():
            sample.seen_by.add(user)

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

        sample.last_seen = timezone.now()
        if not Sample.objects.filter(pk=sample.id, seen_by=user).count():
            sample.seen_by.add(user)

        if None != sha1_hash:
            sample.sha1 = sha1_hash

        if None != sha256_hash:
            sample.sha256 = sha256_hash

        sample.save()
        return True

    def get_function_metadata(self, _id):
        '''Get the metadata associated with the provided Function ID

        Args:
            _id (:obj:`int`): ID from Function model

        Returns:
            QuerySet.
        '''
        return Metadata.objects.filter(function__pk=_id)

    def get_function(self, opcodes, architecture, apis, create=False, **kwargs):
        sha256_hash = hashlib.sha256(opcodes).hexdigest()
        function = None

        try:
            function = Function.objects.get(sha256=sha256_hash,
                                            opcodes=opcodes,
                                            architecture=architecture) #,
                                            #apis__api=apis)
        except ObjectDoesNotExist:
            if create:
                #   Create function and add it to sample
                function = Function.objects.create( sha256=sha256_hash,
                                                    opcodes=opcodes,
                                                    architecture=architecture)

                apis_ = [FunctionApis.objects.get_or_create(x)[0] for x in apis]
                for api in apis_:
                    function.apis.add(api)

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
                return Function.objects.get(pk=_id)

            #   User opcodes and apis
            elif None not in [opcodes, apis]:
                return Function.objects.get(opcodes=opcodes, apis=apis)

            #   Use hash, architecture
            elif None not in [architecture, h_sha256]:
                return Function.objects.get(sha256=h_sha256,
                                            architecture=architecture)

            else:
                return None

        except ObjectDoesNotExist:
            return None

        except MultipleObjectsReturned:
            #   TODO: Log
            raise

    def add_function_to_sample(self, sample, function):
        if (not isinstance(sample, Sample)) or (not isinstance(function, Function)):
            return False

        if not Sample.objects.filter(pk=sample.id, functions=function).count():
            sample.functions.add(function)

        return True

    def add_metadata_to_function(self, user, function, name, prototype, comment, **kwargs):
        if (not isinstance(function, Function)) or (not isinstance(user, User)):
            return None

        #   Check to see if user already has metadata associated with the sample
        metadata = None
        if Function.objects.filter(pk=function.id, metadata__user=user).count():
            #   Metadata already exists
            metadata = Metadata.objects.get(function=function, user=user)
        else:
            metadata = Metadata.objects.create(user=user)
            function.metadata.add(metadata)

        if metadata.has_changed(name, prototype, comment):
            md = MetadataDetails.objects.create(name=name,
                                                prototype=prototype,
                                                comment=comment)
            metadata.details.add(md)

        return metadata.id

    def get_metadata_list(self, metadata):
        results = []
        metadata_ids, engine_metadata = separate_metadata(metadata)

        for _id, metadata in Metadata.objects.in_bulk(metadata_ids).items():
            data = metadata.dump()
            data['id'] = make_id(0, metadata=metadata.id)
            results.append(data)

        for flag, _id, metadata_id in engine_metadata:
            engines = Engine.objects.get(pk=_id)
            # TODO: Send metadata_id to engine for more info
            if (not engines) or (len(engines) > 1):
                continue

            data = {'id' : make_id(flag, metadata_id, _id),
                    'engine' : engine.name,
                    'description' : engine.description}
            results.append(data)

        return results

    def delete_metadata(self, user, metadata_id):
        if not isinstance(user, User):
            return False

        user_metadata, engine_metadata = separate_metadata([metadata_id])
        if not user_metadata:
            return False

        #   User must be the creator of the metadata to delete it
        metadata_id = user_metadata[0]
        try:
            metadata = Metadata.objects.get(pk=metadata_id, user=user)
            metadata.delete()
            return True

        except ObjectDoesNotExist:
            return False

    def created(self, user, page, max_metadata=20):
        pages = 0
        results = []

        if (page < 1) or (not isinstance(user, User)):
            return (results, pages)

        p = Paginator(Metadata.objects.filter(user=user), max_metadata)
        pages = p.num_pages

        if page >  pages:
            return (results, pages)

        for metadata in p.page(page):
            temp = metadata.dump()
            temp['id'] = make_id(0, metadata=metadata.id)
            results.append(temp)

        return (results, pages)

    def metadata_history(self, metadata):
        results = {}
        metadata_ids, engine_metadata = separate_metadata(metadata)
        e_comment = ('Generated by Engine: {0.name}\n{0.description}\n\n'
                    'Developer: {0.developer.user_handle}')

        for _id, metadata in Metadata.objects.in_bulk(metadata_ids).items():
            data = metadata.dump(True)
            result_key = make_id(0, metadata=_id)
            results[result_key] = { 'creator' : data['creator'],
                                    'history' : data['history']}

        #   Provide information for engine created metadata...
        for flag, engine_id, _id in engine_metadata:
            engine = self.get_engine(engine_id)
            if not engine:
                continue
            data = {'creator' : engine.name,
                    'history' : [{'committed' : '',
                                'name' : 'N/A',
                                'prototype' : 'N/A',
                                'comment' : e_comment.format(engine)}]}
            result_key = make_id(flag, engine=engine_id, metadata=_id)
            results[result_key] = data

        return results

    def applied(self, sample, user, _id):
        '''
        @returns Boolean. True if added to the applied list
                            False if not added to the applied list
        '''
        if (not isinstance(user, User)) or (not isinstance(sample, Sample)):
            return False

        flag, engine_data, metadata_id = parse_id(_id)
        if  is_engine_metadata(_id):
            pass
            #   TODO: add this capability back again
            #engine_id = _id
            #engine = Engine.objects(id=engine_id,
            #                        applied__contains=key)

            ##   Check if user has already applied the signature
            #if len(engine):
            #    return True

            #try:
            #    engine = Engine.objects(id=engine_id).get()
            #except ObjectDoesNotExist:
            #    #   Engine does not exist
            #    return False

            #engine.applied.append(key)
            #engine.save()

        else:
            try:
                #   Ensure Metadata exists
                metadata = Metadata.objects.get(pk=metadata_id)
            except ObjectDoesNotExist:
                #   Metadata does not exist
                return False

            r = AppliedMetadata.objects.get_or_create(  user=user,
                                                        sample=sample,
                                                        metadata=metadata)

        return True

    def unapplied(self, sample, user, _id):
        '''
        @returns Boolean. True if not in metadata's applied list
                            False if still in the applied list
        '''
        if (not isinstance(sample, Sample)) or (not isinstance(user, User)):
            return False

        flag, engine_data, metadata_id = parse_id(_id)
        if  is_engine_metadata(_id):
            pass
            #   TODO: add this capability back again
            #engine_id = _id
            #engine = Engine.objects(id=engine_id,
            #                        applied__contains=key)

            ##   Check if user has already applied the signature
            #if not len(engine):
            #    return True

            #try:
            #    engine = Engine.objects(id=engine_id).get()
            #except ObjectDoesNotExist:
            #    #   Engine does not exist
            #    return False

            #engine.applied.remove(key)
            #engine.save()

        else:
            try:
                #   Ensure Metadata exists
                metadata = Metadata.objects.get(pk=metadata_id)
            except ObjectDoesNotExist:
                #   Metadata does not exist
                return False

            try:
                data = AppliedMetadata.objects.get( user=user,
                                                    sample=sample,
                                                    metadata=metadata)
                data.delete()
                return True

            except ObjectDoesNotExist:
                return True


        return False

    def engines(self, active=True):
        return Engine.objects.filter(active=bool(active))

    def get_engine(self, engine_id):
        engines = Engine.objects.filter(pk=engine_id)
        if not engines.count():
            return None

        return engines.first()
