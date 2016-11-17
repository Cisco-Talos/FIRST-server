#-------------------------------------------------------------------------------
#
#   FIRST MongoDB Models
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
#-------------------------------------------------------------------------------


#   Python Modules
from __future__ import unicode_literals
import datetime

#   Third Party Modules
from bson.objectid import ObjectId
from mongoengine import Document, StringField, UUIDField, \
                        DateTimeField, LongField, ReferenceField, \
                        BinaryField, ListField, BooleanField, ObjectIdField, \
                        IntField, EmbeddedDocument, EmbeddedDocumentListField

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

    @property
    def user_handle(self):
        return '{0.handle}#{0.number:04d}'.format(self)

    def dump(self, full=False):
        data = {'handle' : self.user_handle}

        if full:
            data.update({   'id' : str(self.id),
                            'name' : self.name,
                            'email' : self.email,
                            'api_key' : self.api_key,
                            'rank' : self.rank,
                            'created' : self.created,
                            'active' : self.active})

        return data


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

    def dump(self, full=False):
        data = {'name' : self.name,
                'description' : self.description,
                'rank' : self.rank,
                'developer' : self.developer.user_handle}

        if full:
            data.update({'id' : str(self.id), 'path' : self.path})

        return data

    @property
    def rank(self):
        return len(self.applied)


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

    def dump(self, full=False):
        data = {'creator' : self.user.user_handle,
                'name' : self.name[0],
                'prototype' : self.prototype[0],
                'comment' : self.comment[0],
                'rank' : len(self.applied)}

        if full:
            data['history'] = []
            for i in xrange(len(self.name) - 1, -1, -1):
                #   Convert back with:
                #   datetime.datetime.strptime(<dt>, '%Y-%m-%dT%H:%M:%S.%f')
                committed = self.committed[i].isoformat()
                data['history'].append({'name' : self.name[i],
                                        'prototype' : self.prototype[i],
                                        'comment' : self.comment[i],
                                        'committed' : committed})

        return data

    def has_changed(self, name, prototype, comment):
        if (not self.name) or (not self.prototype) or (not comment):
            return True

        if ((self.name[0] != name)
            or (self.prototype[0] != prototype)
            or (self.comment[0] != comment)):
            return True

        return False

    @property
    def rank(self):
        return len(self.applied)

#   Use bson.Binary to insert binary data
class Function(Document):
    sha256 = StringField(max_length=64)
    opcodes = BinaryField()
    apis = ListField(StringField(max_length=64), default=list)
    metadata = EmbeddedDocumentListField(Metadata, default=list)
    #  Return value from idaapi.get_file_type_name()
    architecture = StringField(max_length=64, required=True)

    meta = {
        'indexes' : []
    }

    def dump(self):
        return {'id' : self.id,
                'opcodes' : self.opcodes,
                'apis'  : self.apis,
                'metadata' : [str(x.id) for x in self.metadata],
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
        data = {'md5' : self.md5, 'crc32' : self.crc32,
                'seen_by' : [str(x.id) for x in self.seen_by],
                'functions' : [str(x.id) for x in self.functions]}

        if 'sha1' in self:
            data['sha1'] = self.sha1

        if 'sha256' in self:
            data['sha256'] = self.sha256

        return data
