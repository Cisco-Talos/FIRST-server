#-------------------------------------------------------------------------------
#
#   FIRST Django ORM Models
#   Copyright (C) 2017  Angel M. Villegas
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
from __future__ import unicode_literals
import datetime

#   Third Party Modules
from django.db import models
from django.utils import timezone


class User(models.Model):
    name = models.CharField(max_length=128)
    email = models.CharField(max_length=254)
    handle = models.CharField(max_length=32)
    number = models.IntegerField()
    api_key = models.UUIDField(unique=True)
    created = models.DateTimeField(default=timezone.now)
    rank = models.BigIntegerField(default=0)
    active = models.BooleanField(default=True)

    service = models.CharField(max_length=16)
    auth_data = models.CharField(max_length=4096)

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

    class Meta:
        db_table = 'User'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['api_key']),
        ]
        index_together = ("handle", "number")


class Engine(models.Model):
    name = models.CharField(max_length=16, unique=True)
    description = models.CharField(max_length=128)
    path = models.CharField(max_length=256)
    obj_name = models.CharField(max_length=32)

    developer = models.ForeignKey('User')
    active = models.BooleanField(default=False)

    #@property
    #def rank(self):
    #    return len(self.applied)

    def dump(self, full=False):
        data = {'name' : self.name,
                'description' : self.description,
                'rank' : self.rank,
                'developer' : self.developer.user_handle}

        if full:
            data.update({'path' : self.path})

        return data

    class Meta:
        db_table = 'Engine'
        indexes = [
            models.Index(fields=['name']),
        ]


#   TODO: Create scheme for tracking applied metadata for engines
#
#class AppliedEngine(models.Model):
#    engine_id = models.ForeignKey(Engine)
#    sample_id = models.ForeignKey(Sample)
#    user_id =   models.ForeignKey(User)
#    engine_metadata_id  = models.BigIntegerField();
#
#    class Meta:
#        db_table = 'AppliedEngine'
#        unique_together = ("sample_id", "user_id", "engine_metadata_id")

class AppliedMetadata(models.Model):
    metadata_id = models.ForeignKey('Metadata')
    sample_id = models.OneToOneField('Sample')
    user_id =   models.OneToOneField('User')

    class Meta:
        db_table = 'AppliedMetadata'
        unique_together = ("metadata_id", "sample_id", "user_id")


class MetadataDetails(models.Model):
    name = models.CharField(max_length=256)
    prototype = models.CharField(max_length=256)
    comment = models.CharField(max_length=256)
    committed = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'MetadataDetails'


class Metadata(models.Model):
    user = models.ForeignKey('User')
    details = models.ManyToManyField('Metadatadetails')
    applied = models.ManyToManyField('AppliedMetadata')

    @property
    def rank(self):
        return self.applied.count()

    def has_changed(self, name, prototype, comment):
        if not self.details.exists():
            return True

        latest = self.details.latest('committed')
        if ((latest.name != name)
            or (latest.prototype != prototype)
            or (latest.comment != comment)):
            return True

        return False

    def dump(self, full=False):
        data = {'creator' : self.user.user_handle}
        latest_details = self.details.latest('committed')
        data.update({
            'name' : latest_details.name,
            'prototype' : latest_details.prototype,
            'comment' : latest_details.comment,
            'rank' : AppliedMetadata(metadata_id=latest_details.id).count()
        })

        if full:
            data['history'] = []
            for d in xrange(self.details.count()):
                #   Convert committed time back with:
                #   datetime.datetime.strptime(<dt>, '%Y-%m-%dT%H:%M:%S.%f')
                data['history'].append({'name' : d.name,
                                        'prototype' : d.prototype,
                                        'comment' : d.comment,
                                        'committed' : d.commit.isoformat()})

        return data

    class Meta:
        db_table = 'Metadata'
        indexes = [models.Index(fields=['user'])]


class FunctionApis(models.Model):
    api = models.CharField(max_length=64)

    class Meta:
        db_table = 'FunctionApis'


class Function(models.Model):
    sha256 = models.CharField(max_length=64)
    opcodes = models.BinaryField()
    apis = models.ManyToManyField('FunctionApis')
    metadata = models.ManyToManyField('Metadata')
    architecture = models.CharField(max_length=64)

    def dump(self):
        return {'id' : self.id,
                'opcodes' : self.opcodes,
                'apis'  : [str(x.api) for x in self.apis.all()],
                'metadata' : [str(x.api) for x in self.metadata.all()],
                'architecture' : self.architecture,
                'sha256' : self.sha256}

    class Meta:
        db_table = 'Function'


class Sample(models.Model):
    md5 = models.CharField(max_length=32)
    crc32 = models.IntegerField()
    sha1 = models.CharField(max_length=40, null=True, blank=True)
    sha256 = models.CharField(max_length=64, null=True, blank=True)
    seen_by = models.ManyToManyField('User')
    functions = models.ManyToManyField('Function')
    last_seen = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        index_together = ['md5', 'crc32']

    def dump(self):
        data = {'md5' : self.md5, 'crc32' : self.crc32,
                'seen_by' : [str(x.id) for x in self.seen_by.all()],
                'functions' : [str(x.id) for x in self.functions.all()]}

        if 'sha1' in self:
            data['sha1'] = self.sha1

        if 'sha256' in self:
            data['sha256'] = self.sha256

        return data
