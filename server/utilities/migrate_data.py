#!/usr/bin/python
import json
import os
import base64
import binascii
import argparse

def main(prefix):

    # Declarations for ID counters
    function_ids = {}
    function_id_counter = 1

    apis_ids = {}
    apis_id_counter = 1

    user_ids = {}
    user_id_counter = 1

    sample_ids = {}
    sample_id_counter = 1

    engine_ids = {}
    engine_id_counter = 1

    metadata_details_ids = {}
    metadata_details_id_counter = 1

    metadata_id_counter = 1

    # Collections used to keep temporary data
    applied_metadata_temp = []

    # User
    with open(os.path.join(prefix, "user.json"), "r") as f:
        with open(os.path.join(prefix, "User"), "w") as f_out:
            for l in f:
                d = json.loads(l.strip())
                f_out.write("0|%s|%s|%s|%d|%s|%s|%d|%d|%s|%s\n" % (d['name'], 
                                                                   d['email'], 
                                                                   d['handle'], 
                                                                   d['number'], 
                                                                   binascii.hexlify(base64.b64decode(d['api_key']["$binary"])).lower(), 
                                                                   str(d['created']['$date'])[:-5] + "Z", 
                                                                   int(d['rank']['$numberLong']), 
                                                                   1 if d['active'] else 0, 
                                                                   d['service'], 
                                                                   d['auth_data']))
                user_ids[d["_id"]["$oid"]] = user_id_counter
                user_id_counter += 1

    # Functions, Function APIs, Metadata
    with open(os.path.join(prefix, "function.json"), "r") as f:
        f_FunctionApis = open(os.path.join(prefix, "FunctionApis"), "w")
        f_Function = open(os.path.join(prefix, "Function"), "w")
        f_Function_apis = open(os.path.join(prefix, "Function_apis"), "w")
        f_Metadata = open(os.path.join(prefix, "Metadata"), "w")
        f_Function_metadata = open(os.path.join(prefix, "Function_metadata"), "w")
        f_MetadataDetails = open(os.path.join(prefix, "MetadataDetails"), "w")
        f_Metadata_details = open(os.path.join(prefix, "Metadata_details"), "w")

        # We need to keep track of unique functions, otherwise we might
        # insert repeated records in the CSV.
        unique_functions = {}

        # Keep track of unique metadata details, to avoid repetitions
        unique_metadata_details = {}

        for l in f:
            d = json.loads(l.strip())

            opcodes_text = binascii.hexlify(base64.b64decode(d["opcodes"]["$binary"])).upper()

            if (d['sha256'], d['architecture']) not in unique_functions:
                # Add new function
                unique_functions[(d['sha256'], d['architecture'])] = function_id_counter
                f_Function.write(("0|%s|%s|%s\n") % (d["sha256"], opcodes_text, d["architecture"]))
                # Map of function_ids
                function_ids[d["_id"]["$oid"]] = function_id_counter
                function_id_counter += 1
            else:
                # Duplicate function, reuse previous function id, but consider its linked data
                function_ids[d["_id"]["$oid"]] = unique_functions[(d['sha256'], d['architecture'])]
                #print("Discarding duplicate function... Reusing id %d" % function_ids[d["_id"]["$oid"]])

            if "apis" in d:
                for a in d["apis"]:
                    if a not in apis_ids:
                        apis_ids[a] = apis_id_counter
                        apis_id_counter += 1
                        f_FunctionApis.write("0|%s\n" % (a))
                    f_Function_apis.write("0|%d|%d\n" % (function_ids[d["_id"]["$oid"]], apis_ids[a]))

            if "metadata" in d:
                # 0 - N Metadata records, each record is associated to a User and Function,
                #     and each Metadata record can be associated to several MetadataDetails.
                for m in d["metadata"]:
                    # Get user id
                    if "user" in m and "$oid" in m["user"] and m["user"]["$oid"] in user_ids:
                        user_id = user_ids[m["user"]["$oid"]]
                    else:
                        user_id = 0

                    # This is an 1-N relationship between Metadata and User
                    f_Metadata.write("0|%d\n" % (user_id))
                    # This an N-M relationship between Function and Metadata
                    f_Function_metadata.write("0|%d|%d\n" % (function_ids[d["_id"]["$oid"]], metadata_id_counter))

                    # Store temporarly the Applied relationship (N-M) between User, Metadata, and Sample
                    # We temporarily store the oid because we don't have the mapped ids yet.
                    if "applied" in m:
                        for application in m["applied"]:
                            applied_metadata_temp.append((metadata_id_counter, application[0], application[1])) 

                    if metadata_id_counter not in unique_metadata_details:
                        unique_metadata_details[metadata_id_counter] = []

                    # Metadata details (name, comment, committed, prototype)
                    nb_details = max(len(m.get("name", [])), len(m.get("comment", [])),len(m.get("committed", [])),len(m.get("prototype", [])))
                    for i in range(0, nb_details):
                        name = m["name"][i] if "name" in m and (len(m["name"]) > i) else "" 
                        comment = m["comment"][i] if "comment" in m and (len(m["comment"]) > i) else ""
                        committed = m["committed"][i]["$date"][:-5] + "Z" if "committed" in m and (len(m["committed"]) > i) else ""
                        prototype = m["prototype"][i] if "prototype" in m and (len(m["prototype"]) > i) else ""

                        # We consider only unique entries. Unique by: name, comment, prototype and metadata_id
                        # where metadata_id represents each unique (User,Function) tuple.
                        if (name, comment, prototype) not in unique_metadata_details[metadata_id_counter]:
                            unique_metadata_details[metadata_id_counter].append((name, comment, prototype))
                            f_MetadataDetails.write("0|%s|%s|%s|%s\t\n" % (name, prototype, comment, committed))
                            f_Metadata_details.write(("0|%d|%d\n" % (metadata_id_counter, metadata_details_id_counter)))
                            metadata_details_id_counter += 1

                    metadata_id_counter += 1

        f_FunctionApis.close()
        f_Function.close()
        f_Function_apis.close()
        f_Metadata.close()
        f_Function_metadata.close()
        f_MetadataDetails.close()
        f_Metadata_details.close()

    # Sample

    sample_seen_by = []
    sample_functions = {}

    with open(os.path.join(prefix, "sample.json"), "r") as f:
        f_Sample = open(os.path.join(prefix, "Sample"), "w")
        f_Sample_seen_by = open(os.path.join(prefix, "Sample_seen_by"), "w")

        for l in f:
            d = json.loads(l.strip())

            if isinstance(d['crc32'], dict) and "$numberLong" in d['crc32']:
                d['crc32'] = int(d['crc32']['$numberLong'])
            if not 'sha1' in d:
                d['sha1'] = ""
            if not 'sha256' in d:
                d['sha256'] = ""

            f_Sample.write("0|%s|%d|%s|%s|%s\n" % (d['md5'], d['crc32'], d['sha1'], d['sha256'], str(d['last_seen']['$date'])[:-5] + "Z"))

            # Seen by
            for l in d['seen_by']:
                if l['$oid'] in user_ids:
                    f_Sample_seen_by.write("0|%d|%d\n" % (sample_id_counter, user_ids[l['$oid']]))

            if sample_id_counter not in sample_functions:
                sample_functions[sample_id_counter] = []

            # Functions
            for l in d['functions']:
                if l['$oid'] in function_ids:
                    if function_ids[l['$oid']] not in sample_functions[sample_id_counter]:
                        sample_functions[sample_id_counter].append(function_ids[l['$oid']])

            sample_ids[d["_id"]["$oid"]] = sample_id_counter
            sample_id_counter += 1

        f_Sample.close()
        f_Sample_seen_by.close()

    f_Sample_functions = open(os.path.join(prefix, "Sample_functions"), "w")
    for sid in sample_functions:
        for fid in sample_functions[sid]:
            f_Sample_functions.write("0|%d|%d\n" % (sid, fid))
    f_Sample_functions.close()

    # Engine
    with open(os.path.join(prefix, "engine.json"), "r") as f:
        f_Engine = open(os.path.join(prefix, "Engine"), "w")
        for l in f:
            d = json.loads(l.strip())

            if 'developer' in d and '$oid' in d['developer'] and d['developer']['$oid'] in user_ids:
                developer_id = user_ids[d['developer']['$oid']]
            else:
                developer_id = 0

            f_Engine.write("0|%s|%s|%s|%s|%d|%d\n" % (d['name'], d['description'], d['path'], d['obj_name'], 1 if d['active'] else 0, developer_id))
            engine_ids[d["_id"]["$oid"]] = engine_id_counter
            engine_id_counter += 1

    # Applied metadata

    f = open(os.path.join(prefix, "AppliedMetadata"), "w")
    for metadata_id, sample_oid, user_oid in applied_metadata_temp:
        f.write("0|%d|%d|%d\n" % (metadata_id, sample_ids[sample_oid], user_ids[user_oid]))
    f.close()

if __name__ == "__main__":
    description = """Convert mongoexport generated JSON Files into MySQL import CSV files.

     Expected input files:

        function.json
        sample.json
        engine.json
        user.json

     These files should be generated by running the following commands over the
     mongo database:

     mongoexport -d [database name] -c function -o function.json
     mongoexport -d [database name] -c sample -o sample.json
     mongoexport -d [database name] -c engine -o function.json
     mongoexport -d [database name] -c user -o user.json

     Finally, the generated files can be imported into MySQL by running the mysql queries
     in mysql_import.sql, from the directory where the output files were generated.

     mysql --user [user] --password --host [host] < /path/to/mysql_import.sql

     WARNING: These MySQL script requires the database tables to be created before-hand:
              See FIRST-server documentation to understand how to generate and apply
              the corresponding Django migrations.
     WARNING: This script handles function duplications, so the number of functions
              in the mongo export and the resulting MySQL database might vary.
                  """
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('path', type=str, help='The path where the input json files (see --help)  are located, and where the output files will be generated.')
    args = parser.parse_args()
    main(args.path)
