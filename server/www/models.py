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
from django.db import models
from django.db.transaction import commit


class User(models.Model):
    name = models.CharField(max_length=128)
    email = models.CharField(max_length=254)
    handle = models.CharField(max_length=32)
    number = models.IntegerField()
    created = models.DateTimeField(default=datetime.datetime.utcnow)
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
                            'rank' : self.rank,
                            'created' : self.created,
                            'active' : self.active})
        return data
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),            
        ]
        index_together = ("handle", "number")

    
    
class API(models.Model):
    key = models.UUIDField(unique=True)
    # many to many relationship:
    user = models.ManyToManyField(User,blank=True)
    
    
class Engine(models.Model):
    name = models.CharField(max_length=16, unique=True)
    description = models.CharField(max_length=128)
    path = models.CharField(max_length=256)
    obj_name = models.CharField(max_length=32)
    
    developer = models.OneToOneField(User)    
    active = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),            
        ]

    def dump(self, full=False):
        data = {'name' : self.name,
                'description' : self.description,
                'rank' : self.rank,
                'developer' : Engine.objects.filter(engine_id = self.id)}

        if full:
            data.update({'path' : self.path})

        return data

    @property
    def rank(self):
        return len(self.applied)
    
class AppliedEngine(models.Model): 
    engine_id = models.ForeignKey(Engine)
    sample_id = models.OneToOneField('Sample') 
    user_id =   models.OneToOneField(User)
    engine_metadata_id  = models.BigIntegerField();
    
    class Meta:
        unique_together = ("sample_id", "user_id", "engine_metadata_id")  

class Metadata(models.Model):
    user = models.OneToOneField(User ) 
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),            
        ]
        
    def dump(self, full=False):
        data = {'creator' : User.objects.filter(metadata_id = self.id),
                'name' : MetaDataName.objects.filter(metadata_id = self.id).first(),
                'prototype' : MetaDataPrototype.objects.filter(metadata_id = self.id).first(),
                'comment' : MetaDataComment.objects.filter(metadata_id = self.id).first(),
                'rank' : len(self.applied)}

        if full:
            data['history'] = []
            name = MetaDataName.objects.filter(metadata_id = self.id)
            committed = MetaDataCommited.objects.filter(metadata_id = self.id)
            prototype = MetaDataPrototype.objects.filter(metadata_id = self.id);
            comment = MetaDataComment.objects.filter(metadata_id = self.id);
            
            for i in xrange(len(name) - 1, -1, -1):
                #   Convert back with:
                #   datetime.datetime.strptime(<dt>, '%Y-%m-%dT%H:%M:%S.%f')
                commit = committed[i].isoformat()
                data['history'].append({'name' : name[i],
                                        'prototype' : prototype[i],
                                        'comment' : comment[i],
                                        'committed' : commit})

        return data

    def has_changed(self, name, prototype, comment):
        if (not self.name) or (not self.prototype) or (not comment):
            return True
        
        actualName = MetaDataName.objects.filter(metadata_id = self.id).first()
        actualPrototype = MetaDataPrototype.objects.filter(metadata_id = self.id).first()
        actualComment = MetaDataComment.objects.filter(metadata_id = self.id).first();
        
        if ((actualName.name != name)
            or (actualPrototype.prototype != prototype)
            or (actualComment.comment != comment)):
            return True

        return False

    @property
    def rank(self):
        return len(self.applied)

class AppliedMetaData(models.Model): 
    metadata_id = models.ForeignKey(Engine)
    sample_id = models.OneToOneField('Sample') 
    user_id =   models.OneToOneField(User)
    engine_metadata_id  = models.BigIntegerField();
    class Meta:
        unique_together = ("metadata_id", "sample_id", "user_id") 
    
class MetaDataName(models.Model):
    name = models.CharField(max_length=128)
    models.ForeignKey(Metadata)
    
class MetaDataPrototype(models.Model):
    prototype = models.CharField(max_length=256)
    models.ForeignKey(Metadata)
    
class MetaDataComment(models.Model):
    comment = models.CharField(max_length=128)
    models.ForeignKey(Metadata)
    
class MetaDataCommited(models.Model):
    committed = models.DateTimeField(default=datetime.datetime.utcnow, blank=True)
    models.ForeignKey(Metadata)

class Function(models.Model):
    sha256 = models.CharField(max_length=64)
    opcodes = models.BinaryField
    metadata = models.ForeignKey(Metadata)
    mnemonic_hash = models.ForeignKey('MnemonicHash')
    #  Return value from idaapi.get_file_type_name()
    architecture = models.CharField(max_length=64)

    def dump(self):
        return {'id' : self.id,
                'opcodes' : self.opcodes,
                'apis'  : self.functionapis_set.all(),
                'metadata' : [str(x.api) for x in Metadata.objects.filter(function_id = self.id)],
                'architecture' : self.architecture,
                'sha256' : self.sha256}

class FunctionApis(models.Model):
    api = models.CharField(max_length=64)
    models.ForeignKey(Function)
    

class Sample(models.Model):
    md5 = models.CharField(max_length=32)
    crc32 = models.IntegerField()
    sha1 = models.CharField(max_length=40)
    sha256 = models.CharField(max_length=64)
    seen_by = models.ManyToManyField( User, blank=True)
    functions = models.ManyToManyField( Function, blank=True)
    last_seen = models.DateTimeField(default=datetime.datetime.utcnow, blank=True)

    class Meta:
        index_together = ['md5', 'crc32']
    
    def dump(self):
        data = {'md5' : self.md5, 'crc32' : self.crc32,
                'seen_by' : [str(x.id) for x in User.objects.filter(sample_id = self.id)],
                'functions' : [str(x.id) for x in Function.objects.filter(sample_id = self.id)]}

        if 'sha1' in self:
            data['sha1'] = self.sha1

        if 'sha256' in self:
            data['sha256'] = self.sha256

        return data

class MnemonicHash(models.Model):
    sha256 = models.CharField(max_length=64)
    architecture = models.CharField(max_length=64)

    class Meta:
        index_together = ('sha256', 'architecture')
        
    def dump(self):
        return {'sha256' : self.sha256,
                'architecture' : self.architecture,
                'functions' : self.function_set.all()}

    def function_list(self):
        return [str(x) for x in Function.objects.filter(MnemonicHash_id = self.id)]



