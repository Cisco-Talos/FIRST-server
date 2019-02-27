USE first_db;

DELETE FROM AppliedMetadata;
ALTER TABLE AppliedMetadata AUTO_INCREMENT = 1;

DELETE FROM Metadata_details;
ALTER TABLE Metadata_details AUTO_INCREMENT = 1;

DELETE FROM Function_metadata;
ALTER TABLE Function_metadata AUTO_INCREMENT = 1;

DELETE FROM MetadataDetails;
ALTER TABLE MetadataDetails AUTO_INCREMENT = 1;

DELETE FROM Metadata;
ALTER TABLE Metadata AUTO_INCREMENT = 1;

DELETE FROM Engine; 
ALTER TABLE Engine AUTO_INCREMENT = 1;

DELETE FROM Sample_seen_by; 
ALTER TABLE Sample_seen_by AUTO_INCREMENT = 1;

DELETE FROM Sample_functions;
ALTER TABLE Sample_functions AUTO_INCREMENT = 1;

DELETE FROM Function_apis;
ALTER TABLE Function_apis AUTO_INCREMENT = 1;

DELETE FROM FunctionApis;
ALTER TABLE FunctionApis AUTO_INCREMENT = 1;

DELETE FROM Sample;
ALTER TABLE Sample AUTO_INCREMENT = 1;

DELETE FROM Function;
ALTER TABLE Function AUTO_INCREMENT = 1;

DELETE FROM User;
ALTER TABLE User AUTO_INCREMENT = 1;

LOAD DATA LOCAL INFILE "FunctionApis" INTO TABLE FunctionApis COLUMNS TERMINATED BY "|";

LOAD DATA LOCAL INFILE "Function" INTO TABLE Function FIELDS TERMINATED BY "|" (id, sha256, @var1, architecture) SET opcodes = UNHEX(@var1);

LOAD DATA LOCAL INFILE"Function_apis" INTO TABLE Function_apis FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE "User" INTO TABLE User FIELDS TERMINATED BY "|" (id, name, email, handle, number, api_key, @var1, rank, active, service, auth_data) SET created = STR_TO_DATE(@var1, '%Y-%m-%dT%H:%i:%SZ');

LOAD DATA LOCAL INFILE"Sample" INTO TABLE Sample FIELDS TERMINATED BY "|" (id, md5, crc32, sha1, sha256, @var1) SET last_seen = STR_TO_DATE(@var1, '%Y-%m-%dT%H:%i:%SZ');

LOAD DATA LOCAL INFILE"Sample_functions" INTO TABLE Sample_functions FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"MetadataDetails" INTO TABLE MetadataDetails FIELDS TERMINATED BY "|" LINES TERMINATED BY "\t\n" (id, name, prototype, comment, @var1) SET committed = STR_TO_DATE(@var1, '%Y-%m-%dT%H:%i:%SZ');

LOAD DATA LOCAL INFILE"Sample_seen_by" INTO TABLE Sample_seen_by FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"Engine" INTO TABLE Engine FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"Metadata" INTO TABLE Metadata FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"Metadata_details" INTO TABLE Metadata_details FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"AppliedMetadata" INTO TABLE AppliedMetadata FIELDS TERMINATED BY "|";

LOAD DATA LOCAL INFILE"Function_metadata" INTO TABLE Function_metadata FIELDS TERMINATED BY "|";
