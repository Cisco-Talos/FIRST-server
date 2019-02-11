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

#   Third Party Modules
from django.db import models
from django.utils import timezone


class User(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=128)
    email = models.CharField(max_length=254)
    handle = models.CharField(max_length=32)
    number = models.IntegerField()
    api_key = models.UUIDField(unique=True)
    created = models.DateTimeField(default=timezone.now)
    rank = models.BigIntegerField(default=0)
    active = models.BooleanField(default=True)

    service = models.CharField(max_length=16)
    auth_data = models.CharField(max_length=32768)

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
    description = models.CharField(max_length=256)
    path = models.CharField(max_length=256)
    obj_name = models.CharField(max_length=32)

    developer = models.ForeignKey('User')
    active = models.BooleanField(default=False)

    @property
    def rank(self):
        #   TODO: Complete
        #return len(self.applied)
        return 0

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
    metadata = models.ForeignKey('Metadata')
    sample = models.ForeignKey('Sample')
    user =   models.ForeignKey('User')

    class Meta:
        db_table = 'AppliedMetadata'
        unique_together = ("metadata", "sample", "user")


class MetadataDetails(models.Model):
    name = models.CharField(max_length=256)
    prototype = models.CharField(max_length=256)
    comment = models.CharField(max_length=512)
    committed = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'MetadataDetails'


class Metadata(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey('User')
    details = models.ManyToManyField('MetadataDetails')

    @property
    def rank(self):
        if hasattr(self, 'id'):
            return AppliedMetadata.objects.filter(metadata=self.id).count()

        return 0

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
            'rank' : self.rank
        })

        if full:
            #   Convert committed time back with:
            #   datetime.datetime.strptime(<dt>, '%Y-%m-%dT%H:%M:%S.%f')
            data['history'] = [{'name' : d.name,
                                'prototype' : d.prototype,
                                'comment' : d.comment,
                                'committed' : d.committed.isoformat()}
                                for d in self.details.order_by('committed')]

        return data

    class Meta:
        db_table = 'Metadata'
        indexes = [models.Index(fields=['user'])]


class FunctionApis(models.Model):
    api = models.CharField(max_length=128, unique=True)

    class Meta:
        db_table = 'FunctionApis'


class Function(models.Model):
    id = models.BigAutoField(primary_key=True)

    sha256 = models.CharField(max_length=64)
    opcodes = models.BinaryField()
    apis = models.ManyToManyField('FunctionApis')
    metadata = models.ManyToManyField('Metadata')
    architecture = models.CharField(max_length=64)

    def dump(self, full=False):
        data = {'opcodes' : self.opcodes,
                'architecture' : self.architecture,
                'sha256' : self.sha256}

        if full:
            data['apis'] = [x['api'] for x in self.apis.values('api')]
            data['id'] = self.id

        return data

    class Meta:
        db_table = 'Function'
        unique_together = ('sha256', 'architecture')


class Sample(models.Model):
    id = models.BigAutoField(primary_key=True)

    md5 = models.CharField(max_length=32)
    crc32 = models.BigIntegerField()
    sha1 = models.CharField(max_length=40, null=True, blank=True)
    sha256 = models.CharField(max_length=64, null=True, blank=True)
    seen_by = models.ManyToManyField('User')
    functions = models.ManyToManyField('Function')
    last_seen = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        db_table = 'Sample'
        index_together = ['md5', 'crc32']
        unique_together = ('md5', 'crc32')

    def dump(self):
        return {'md5' : self.md5, 'crc32' : self.crc32,
                'seen_by' : [str(x.id) for x in self.seen_by.all()],
                'functions' : [str(x.id) for x in self.functions.all()],
                'sha1' : self.sha1,
                'sha256' : self.sha256}
