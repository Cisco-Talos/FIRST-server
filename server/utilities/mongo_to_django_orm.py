#! /usr/bin/python
#-------------------------------------------------------------------------------
#
#   FIRST MongoDB to Django ORM Conversion Script
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
#   mongoengine (https://pypi.python.org/pypi/mongoengine/)
#
#
#-------------------------------------------------------------------------------

#   Python Modules
import os
import sys
import time
import datetime
from getpass import getpass
from argparse import ArgumentParser

#   DEBUG
from pprint import pprint
import gc

#   FIRST Modules
import first_core.models as ORM

#   Third Party Modules
from bson import Binary
from bson.objectid import ObjectId
import mongoengine
from mongoengine import Document, StringField, UUIDField, \
                        DateTimeField, LongField, ReferenceField, \
                        BinaryField, ListField, BooleanField, ObjectIdField, \
                        IntField, EmbeddedDocument, EmbeddedDocumentListField
from django.core.paginator import Paginator, EmptyPage

def info():
    print 'INFO: {} {}'.format(len(gc.get_objects()), sum([sys.getsizeof(o) for o in gc.get_objects()]))

def migrate_users():
    for u in User.objects.all():
        user, created = ORM.User.objects.get_or_create(**u.dump())

def migrate_engines():
    for e in Engine.objects.all():
        engine = e.dump()
        engine['developer'] = ORM.User.objects.get(email=e.developer.email)
        engine = ORM.Engine.objects.create(**engine)

def migrate_samples():
    paginator = Paginator(Sample.objects.all(), 100)
    for s in Sample.objects.all().exclude('functions').select_related():
        sample, created = ORM.Sample.objects.get_or_create(**s.dump())
        for u in s.seen_by:
            sample.seen_by.add(ORM.User.objects.get(email=u.email))

def migrate_functions(skip, limit):
    i = 0
    for f in Function.objects.skip(skip).limit(limit).select_related(3):
        function, created = ORM.Function.objects.get_or_create(**f.dump())
        #   Convert Functions
        if created:
            #   Add APIs to function
            migrate_apis(function, f)

            #   Add to samples
            for s in Sample.objects.only('md5', 'crc32').filter(functions=f.id):
                ORM.Sample.objects.get(md5=s.md5, crc32=s.crc32).functions.add(function)
                #sample = ORM.Sample.objects.get(md5=s.md5, crc32=s.crc32)
                #sample.functions.add(function)

            #   Add metadata assocaited with the function
            migrate_metadata(function, f)

        i += 1
        if 0 == (i % 1000):
            print '---{}---'.format(i)
            info()
            gc.collect()
            info()

def _mf():
    for i in xrange(0, Function.objects.count(), 1000):
        print '--{}'.format(i)
        migrate_functions(i, 1000)

        if i % 20000 == 0:
            info()
            gc.collect()
            info()

def migrate_apis(function, f):
    for a in f.apis:
        api, _ = ORM.FunctionApis.objects.get_or_create(api=a)
        function.apis.add(api)

    gc.collect()

def migrate_metadata(function, f):
    print 'Metadata: {} - {}'.format(f.sha256, len(f.metadata))
    for m in f.metadata:
        creator = ORM.User.objects.get(email=m.user.email)
        metadata = ORM.Metadata.objects.create(user=creator)
        function.metadata.add(metadata)

        #   Convert Metadata Details
        for d in m.details():
            details = ORM.MetadataDetails.objects.create(**d)
            metadata.details.add(details)

        #   Convert Metadata Applied
        for s_id, u_id in m.applied:
            s_ = Sample.objects.only('md5', 'crc32').get(pk=s_id)
            u = User.objects.only('email').get(pk=u_id)
            sample_ = ORM.Sample.objects.get(md5=s_.md5, crc32=s_.crc32)
            user_ = ORM.User.objects.get(email=u.email)
            ORM.AppliedMetadata.objects.create(metadata=metadata,
                                                user=user_,
                                                sample=sample_)

def main(args):
    pass_prompt = 'Enter MongoDB password for {}: '.format(args.user)
    mongoengine.connect(args.mongo_db,
                        host=args.mongo_host,
                        port=args.mongo_port,
                        user=args.mongo_user,
                        password=getpass(pass_prompt))
    #   Convert User
    print ' +  Adding Users'
    start = time.time()
    migrate_users()
    print '[+] Users Added ({} s)'.format(time.time() - start)

    #   Convert Engine
    print ' +  Adding Engines'
    start = time.time()
    migrate_engines()
    print '[+] Adding Engines ({} s)'.format(time.time() - start)

    #   Convert Samples
    print ' +  Adding Samples'
    start = time.time()
    migrate_samples()
    print '[+] Adding Samples ({} s)'.format(time.time() - start)

    #   Convert Functions and their Metadata
    print ' +  Adding Functions & Metadata'
    start = time.time()
    _mf()
    print '[+] Adding Functions & Metadata ({} s)'.format(time.time() - start)




#-------------------------------------------------------------------------------
#   MongoDB Models
#   FIRST v0.0.1
#-------------------------------------------------------------------------------
class User(Document):
    name = StringField(max_length=128, required=True)
    email = StringField(max_length=254, unique=True)
    handle = StringField(max_length=32, required=True)
    number = IntField(required=True)
    api_key = UUIDField(required=True, unique=True)
    created = DateTimeField(default=datetime.datetime.utcnow, required=True)
    rank = LongField(default=0)
    active = BooleanField(default=True)

    service = StringField(max_length=16, required=True)
    auth_data = StringField(max_length=4096, required=True)

    meta = {
        'indexes' : [('handle', 'number'), 'api_key', 'email']
    }

    def dump(self):
        return {'name' : self.name,
                'email' : self.email,
                'handle' : self.handle,
                'number' : self.number,
                'api_key' : self.api_key,
                'created' : self.created,
                'rank' : self.rank,
                'active' : self.active}


class Engine(Document):
    name = StringField(max_length=16, required=True, unique=True)
    description = StringField(max_length=128, required=True)
    path = StringField(max_length=256, required=True)
    obj_name = StringField(max_length=32, required=True)
    applied = ListField(default=list)
    developer = ReferenceField(User)
    active = BooleanField(default=False)

    meta = {
        'indexes' : ['name']
    }

    def dump(self):
        return {'name' : self.name,
                'description' : self.description,
                'path' : self.path,
                'obj_name' : self.obj_name,
                'developer' : self.developer,
                'active' : self.active}


class Metadata(EmbeddedDocument):
    id = ObjectIdField(required=True, default=lambda: ObjectId())
    user = ReferenceField(User)
    name = ListField(StringField(max_length=128), default=list)
    prototype = ListField(StringField(max_length=256), default=list)
    comment = ListField(StringField(max_length=512), default=list)
    committed = ListField(DateTimeField(), default=list)
    applied = ListField(default=list)

    meta = {
        'indexes' : ['user']
    }

    def details(self):
        return [{'committed' : self.committed[i],
                'name' : self.name[i],
                'prototype' : self.prototype[i],
                'comment' : self.comment[i]} for i in xrange(len(self.name))]

#   Use bson.Binary to insert binary data
class Function(Document):
    sha256 = StringField(max_length=64)
    opcodes = BinaryField()
    apis = ListField(StringField(max_length=128), default=list)
    metadata = EmbeddedDocumentListField(Metadata, default=list)
    architecture = StringField(max_length=64, required=True)

    meta = {
        'indexes' : []
    }

    def dump(self):
        return {'opcodes' : Binary(self.opcodes),
                'architecture' : self.architecture,
                'sha256' : self.sha256}


class Sample(Document):
    md5 = StringField(max_length=32, required=True)
    crc32 = IntField(required=True)
    sha1 = StringField(max_length=40)
    sha256 = StringField(max_length=64)
    seen_by = ListField(ReferenceField(User), default=list)
    functions = ListField(ReferenceField(Function), default=list)
    last_seen = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'indexes' : [('md5', 'crc32')]
    }

    def dump(self):
        data = {'md5' : self.md5, 'crc32' : self.crc32}

        if hasattr(self, 'sha1'):
            data['sha1'] = self.sha1

        if hasattr(self, 'sha256'):
            data['sha256'] = self.sha256

        return data

if __name__ == '__main__':
    parser = ArgumentParser(('FIRST Mongo to Django ORM Conversion Script\n'
        'This script should be used to convert FIRST v0.0.1 to FIRST v0.1.0\n'
    ))

    #   Arguments
    parser.add_argument('--mongo-host', '--host', help='The MongoDB host')
    parser.add_argument('--mongo-port', '-p', help='The MongoDB port', type=int)
    parser.add_argument('--mongo-user', '-u', help='The MongoDB user')
    parser.add_argument('--mongo-db', '-d', help='The MongoDB db name')

    main(parser.parse_args())
