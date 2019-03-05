from django.test import TestCase
from django.urls import reverse
from first_core.models import User
from first_core.models import Sample 
from first_core.models import Engine

import datetime
import json

# NOTE: Before running these tests with "manage.py test rest", you 
#       will need to have all the migrations ready, both for the
#       main database "manage.py makemigrations" and the following 
#       pluggable engines: ExactMatch, MnemomicHash, and BasicMasking.
#       In order to prepare these migrations, run the engine_shell.py
#       and install the engines (on the real database). That will
#       create the corresponding rows in the database, and also
#       invoke the makemigrations for each of those pluggable modules.
#       (You can remove the entries from the database later, as the
#       only important thing here are the migrations. The database
#       entries for the test database are created in this test script).

def create_user(**kwargs):
    return User.objects.create(**kwargs)

def create_engine(**kwargs):
    return Engine.objects.create(**kwargs)

class RestTests(TestCase):
    def test_connection(self):
        '''
            Connection test with correct and incorrect API keys
        '''
        user1 = create_user(name = "user1",
                    email = "user1@noreply.cisco.com",
                    handle = "user1_h4x0r",
                    number = "1337",
                    api_key = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
                    created = datetime.datetime.now(),
                    rank = 0,
                    active = True)

        # Test correct API key
        response = self.client.get(reverse("rest:test_connection",  kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}))
        self.assertIs(response.status_code == 200 and \
                      json.loads(str(response.content, encoding="utf-8")) == {"status": "connected"}, True)

        # Test incorrect API key
        response = self.client.get(reverse("rest:test_connection",  kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAABB'}))
        self.assertIs(response.status_code == 401, True)

    def test_sample_architecture(self):
        '''
            Test sample/architecures
        '''
        user1 = create_user(name = "user1",
                    email = "user1@noreply.cisco.com",
                    handle = "user1_h4x0r",
                    number = "1337",
                    api_key = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
                    created = datetime.datetime.now(),
                    rank = 0,
                    active = True)

        response = self.client.get(reverse("rest:architectures",  kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}))

        passed = True
        if response.status_code == 200:
            d = json.loads(str(response.content, encoding="utf-8"))
            if "failed" in d and d['failed'] == False: 
                if "architectures" in d:
                    for arch in ["intel64", "arm32", "sparc", "sysz", "intel32", "arm64", "intel16", "ppc", "mips"]:
                        if arch not in d["architectures"]:
                            passed = False
                            break
                else:
                    passed = False
            else:
                passed = False
        else:
            passed = False

        self.assertIs(passed, True)

    def test_sample_checkin(self):
        '''
            Test sample checkin
        '''
        user1 = create_user(name = "user1",
                    email = "user1@noreply.cisco.com",
                    handle = "user1_h4x0r",
                    number = "1337",
                    api_key = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
                    created = datetime.datetime.now(),
                    rank = 0,
                    active = True)

        response = self.client.post(reverse("rest:checkin", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {"md5": "AA" * 16, "crc32": 0, "sha1": "AA" * 40, "sha256": "AA" * 64} )

        passed = True
        if response.status_code == 200:
            d = json.loads(str(response.content, encoding="utf-8"))
            if "failed" not in d or d["failed"] is True:
                passed = False
            if "checkin" not in d or d["checkin"] is False:
                passed = False
        else:
            passed = False

        self.assertIs(passed, True)

        # Get the last_seen date of the sample
        s = Sample.objects.get(md5="AA" * 16)
        self.assertIs(s is None, False)
        last_seen_1 = s.last_seen

        # Run again, the last_seen data should be updated and a new relationship between the other user
        # and the sample should be created

        user2 = create_user(name = "user2",
                    email = "user2@noreply.cisco.com",
                    handle = "user2_h4x0r",
                    number = "1338",
                    api_key = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAACC",
                    created = datetime.datetime.now(),
                    rank = 0,
                    active = True)

        response = self.client.post(reverse("rest:checkin", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAACC'}), 
                {"md5": "AA" * 16, "crc32": 0, "sha1": "AA" * 40, "sha256": "AA" * 64} )

        passed = True
        if response.status_code == 200:
            d = json.loads(str(response.content, encoding="utf-8"))
            if "failed" not in d or d["failed"] is True:
                passed = False
            if "checkin" not in d or d["checkin"] is False:
                passed = False
        else:
            passed = False

        # Now, get the last seen date of the sample
        s = Sample.objects.get(md5="AA" * 16)
        self.assertIs(s is None, False)
        last_seen_2 = s.last_seen

        self.assertIs(last_seen_1 < last_seen_2, True)

        # Sample has been seen by 2 users
        self.assertIs(len(s.seen_by.all()), 2)

    def test_metadata(self):
        '''
            Big test for all the metadata related
            functionality. It is used to test the
            different metadata related APIs.
        '''
        # User1 adds some metadata to a pair of functions

        # First, we need to create the user
        user1 = create_user(name = "user1",
                    email = "user1@noreply.cisco.com",
                    handle = "user1_h4x0r",
                    number = "1337",
                    api_key = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
                    created = datetime.datetime.now(),
                    rank = 0,
                    active = True)

        # Second, we need to create/activate the Engines
        e1 = create_engine(name = "ExactMatch",
                      description = "Desc of ExactMatch",
                      path = "first_core.engines.exact_match",
                      obj_name = "ExactMatchEngine",
                      developer = user1,
                      active = True)

        e2 = create_engine(name = "MnemonicHash",
                      description = "Desc of MnemonicHash",
                      path = "first_core.engines.mnemonic_hash",
                      obj_name = "MnemonicHashEngine",
                      developer = user1,
                      active = True)

        e3 = create_engine(name = "BasicMasking",
                      description = "Desc of BasicMasking",
                      path = "first_core.engines.basic_masking",
                      obj_name = "BasicMaskingEngine",
                      developer = user1,
                      active = True)

        # And test that these engines have been correctly created
        self.assertIs(e1 is not None and e2 is not None and e3 is not None, True)

        # Create the sample
        response = self.client.post(reverse("rest:checkin", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {"md5": "AA" * 16, "crc32": 0, "sha1": "AA" * 40, "sha256": "AA" * 64} )

        self.assertIs(response.status_code, 200)
        d = json.loads(str(response.content, encoding="utf-8"))
        self.assertIs("checkin" in d and d["checkin"] is True, True)

        response = self.client.post(reverse("rest:metadata_add", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {"md5": "AA" * 16, "crc32": 0, 
                'functions' : json.dumps( 
                    {
                    'function_id_0' :
                        {
                            'opcodes' : "VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIDEzIGxhenkgZG9ncy4=",
                            'architecture' : "intel32",
                            'name' : "my_function_0",
                            'prototype' : "int my_function_0(int a)",
                            'comment' : "This is a comment for function 0",
                            'apis' : ["ExitProcess", "CreateProcessA"]
                        },
                    'function_id_1' :
                        {
                            'opcodes' : "VTHSieWLRQhWi3UMU41Y/w+2DBaITBMBg8IBhMl18VteXcM=",
                            'architecture' : "intel32",
                            'name' : "my_function_1",
                            'prototype' : "int my_function_1(int b)",
                            'comment' : "This is a comment for function 1",
                            'apis' : ["CreateThread", "WriteProcessMemory"]
                        }
                    })})

        self.assertIs(response.status_code, 200)
        #b'{"failed": false, "results": {"function_id_0": "00000000000000000000000001", "function_id_1": "00000000000000000000000003"}}'
        d = json.loads(str(response.content, encoding="utf-8"))
        self.assertIs("failed" in d and d["failed"] is False, True)
        self.assertIs("results" in d, True)
        self.assertIs("function_id_0" in d["results"], True)
        self.assertIs("function_id_1" in d["results"], True)
        self.assertIs(d["results"]["function_id_0"] is not None, True)
        self.assertIs(d["results"]["function_id_1"] is not None, True)

        # Retrieve metadata created by user
        response = self.client.get(reverse("rest:metadata_created", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}))
        self.assertIs(response.status_code, 200)
        d = json.loads(str(response.content, encoding="utf-8"))

        self.assertIs("failed" in d and d["failed"] is False, True)
        self.assertIs("page" in d and d["page"] == 1, True)
        self.assertIs("pages" in d and d["pages"] == 1, True)
        self.assertIs("results" in d and len(list(d["results"])) == 2, True)

        # We collect the metadata ids
        metadata_ids = []
        for f in d["results"]:
            if f["name"] == "my_function_0":
                self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                self.assertIs(f["prototype"] == "int my_function_0(int a)" , True)
                self.assertIs(f["comment"] == "This is a comment for function 0" , True)
                self.assertIs(f["rank"] == 1 , True)
                self.assertIs(f["id"] is not None , True)
                metadata_ids.append(f["id"])
            elif f["name"] == "my_function_1":
                self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                self.assertIs(f["prototype"] == "int my_function_1(int b)" , True)
                self.assertIs(f["comment"] == "This is a comment for function 1" , True)
                self.assertIs(f["rank"] == 1 , True)
                self.assertIs(f["id"] is not None , True)
                metadata_ids.append(f["id"])
            else:
                self.assertIs("Incorrect function name...", True)

        # Test for metadata_get
        response = self.client.post(reverse("rest:metadata_get", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}),
                                   {"metadata": json.dumps(metadata_ids) } )
        self.assertIs(response.status_code, 200)
        d = json.loads(str(response.content, encoding="utf-8"))

        self.assertIs("failed" in d and d["failed"] is False, True)
        self.assertIs("results" in d and len(list(d["results"])) == len(metadata_ids), True)

        for metadata_id in metadata_ids:
            self.assertIs(metadata_id in d["results"], True)
            f = d["results"][metadata_id]
            if f["name"] == "my_function_0":
                self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                self.assertIs(f["prototype"] == "int my_function_0(int a)" , True)
                self.assertIs(f["comment"] == "This is a comment for function 0" , True)
                self.assertIs(f["rank"] == 1 , True)
                self.assertIs(f["id"] is not None , True)
            elif f["name"] == "my_function_1":
                self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                self.assertIs(f["prototype"] == "int my_function_1(int b)" , True)
                self.assertIs(f["comment"] == "This is a comment for function 1" , True)
                self.assertIs(f["rank"] == 1 , True)
                self.assertIs(f["id"] is not None , True)
            else:
                self.assertIs("Incorrect function name...", True)

        # Test for metadata_scan

        response = self.client.post(reverse("rest:metadata_scan", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {'functions' : json.dumps( 
                    {
                    'function_id_0' :
                        {
                            'opcodes' : "VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIDEzIGxhenkgZG9ncy4=",
                            'architecture' : "intel32",
                            'apis' : ["ExitProcess", "CreateProcessA"]
                        },
                    'function_id_1' :
                        {
                            'opcodes' : "VTHSieWLRQhWi3UMU41Y/w+2DBaITBMBg8IBhMl18VteXcM=",
                            'architecture' : "intel32",
                            'apis' : ["CreateThread", "WriteProcessMemory"]
                        },
                    'function_id_2' :
                        {
                            'opcodes' : "VTHSieWLafrci3UMU41Y/w+2DBaITBMBg8IBhMl18VteXcM=",
                            'architecture' : "intel32",
                            'apis' : ["CreateThread", "WriteProcessMemory"]
                        }

                    })})

        self.assertIs(response.status_code, 200)
        d = json.loads(str(response.content, encoding="utf-8"))

        self.assertIs("failed" in d and d["failed"] is False, True)
        self.assertIs("results" in d and "engines" in d["results"] and "matches" in d["results"], True)
        self.assertIs("ExactMatch" in d["results"]["engines"], True)
        self.assertIs("MnemonicHash" in d["results"]["engines"], True)
        self.assertIs("BasicMasking" in d["results"]["engines"], True)

        self.assertIs("function_id_0" in d["results"]["matches"], True)
        self.assertIs("function_id_1" in d["results"]["matches"], True)
        self.assertIs("function_id_2" not in d["results"]["matches"], True)

        for f_id in d["results"]["matches"]:
            for f in d["results"]["matches"][f_id]:
                if f["name"] == "my_function_0":
                    self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                    self.assertIs(f["prototype"] == "int my_function_0(int a)" , True)
                    self.assertIs(f["comment"] == "This is a comment for function 0" , True)
                    self.assertIs(f["rank"] == 1 , True)
                    self.assertIs(f["similarity"] == 100.0 , True)
                    self.assertIs(set(f["engines"]) == set(['MnemonicHash', 'ExactMatch', 'BasicMasking']) , True)
                    self.assertIs(f["id"] is not None , True)
                elif f["name"] == "my_function_1":
                    self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
                    self.assertIs(f["prototype"] == "int my_function_1(int b)" , True)
                    self.assertIs(f["comment"] == "This is a comment for function 1" , True)
                    self.assertIs(f["rank"] == 1 , True)
                    self.assertIs(f["similarity"] == 100.0 , True)
                    self.assertIs(set(f["engines"]) == set(['MnemonicHash', 'ExactMatch', 'BasicMasking']) , True)
                    self.assertIs(f["id"] is not None , True)
                else:
                    self.assertIs("Incorrect function name...", True)

        # Test metadata applied / unapplied

        # Apply the metadata
        for metadata_id in metadata_ids:
            response = self.client.post(reverse("rest:metadata_applied", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                    {"md5": "AA" * 16, "crc32": 0, "id": metadata_id })
            self.assertIs(response.status_code, 200)
            d = json.loads(str(response.content, encoding="utf-8"))
            self.assertIs("failed" in d and d["failed"] is False, True)
            self.assertIs("results" in d and d["results"] is True, True)

        # Unapply the metadata
        for metadata_id in metadata_ids:
            response = self.client.post(reverse("rest:metadata_unapplied", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                    {"md5": "AA" * 16, "crc32": 0, "id": metadata_id })
            self.assertIs(response.status_code, 200)
            d = json.loads(str(response.content, encoding="utf-8"))
            self.assertIs("failed" in d and d["failed"] is False, True)
            self.assertIs("results" in d and d["results"] is True, True)


        # Test metadata history
        # First, we update the metadata, with a second version
        response = self.client.post(reverse("rest:metadata_add", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {"md5": "AA" * 16, "crc32": 0, 
                'functions' : json.dumps( 
                    {
                    'function_id_0' :
                        {
                            'opcodes' : "VGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIDEzIGxhenkgZG9ncy4=",
                            'architecture' : "intel32",
                            'name' : "my_function_0_v2",
                            'prototype' : "int my_function_0_v2(int a)",
                            'comment' : "This is a v2 comment for function 0",
                            'apis' : ["ExitProcess", "CreateProcessA"]
                        },
                    'function_id_1' :
                        {
                            'opcodes' : "VTHSieWLRQhWi3UMU41Y/w+2DBaITBMBg8IBhMl18VteXcM=",
                            'architecture' : "intel32",
                            'name' : "my_function_1_v2",
                            'prototype' : "int my_function_1_v2(int b)",
                            'comment' : "This is a v2 comment for function 1",
                            'apis' : ["CreateThread", "WriteProcessMemory"]
                        }
                    })})

        self.assertIs(response.status_code, 200)

        # Then, we retrieve the history
        response = self.client.post(reverse("rest:metadata_history", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'}), 
                {"metadata": json.dumps(metadata_ids) })

        self.assertIs(response.status_code, 200)
        d = json.loads(str(response.content, encoding="utf-8"))
        self.assertIs("failed" in d and d["failed"] is False, True)
        self.assertIs("results" in d and isinstance(d["results"], dict), True)
        for _id in d["results"].keys():
            f = d["results"][_id]
            self.assertIs(f["creator"] == "user1_h4x0r#1337" , True)
            self.assertIs("history" in f and isinstance(f["history"], list) , True)
            for fh in f["history"]:
                self.assertIs("committed" in fh and fh["committed"] is not None, True)
                if fh["name"] == "my_function_0":
                    self.assertIs(fh["prototype"] == "int my_function_0(int a)" , True)
                    self.assertIs(fh["comment"] == "This is a comment for function 0" , True)
                elif fh["name"] == "my_function_0_v2":
                    self.assertIs(fh["prototype"] == "int my_function_0_v2(int a)" , True)
                    self.assertIs(fh["comment"] == "This is a v2 comment for function 0" , True)
                elif fh["name"] == "my_function_1":
                    self.assertIs(fh["prototype"] == "int my_function_1(int b)" , True)
                    self.assertIs(fh["comment"] == "This is a comment for function 1" , True)
                elif fh["name"] == "my_function_1_v2":
                    self.assertIs(fh["prototype"] == "int my_function_1_v2(int b)" , True)
                    self.assertIs(fh["comment"] == "This is a v2 comment for function 1" , True)
                else:
                    self.assertIs("Incorrect function name...", True)

        # Finally, test metadata deletion
        for _id in metadata_ids:
            response = self.client.get(reverse("rest:metadata_delete", kwargs={'api_key' : 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA', '_id': _id}))
            self.assertIs(response.status_code, 200)
            d = json.loads(str(response.content, encoding="utf-8"))
            self.assertIs('failed' in d and d['failed'] is False, True)
            self.assertIs('deleted' in d and d['deleted'] is True, True)

        print("Successfully finished tests!!")
