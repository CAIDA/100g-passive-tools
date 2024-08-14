#+
# NAME:
#   100g-anon_list-objects.py
# PURPOSE:
#   List the files in the 100g-anon-pcap bucket/container 
# INPUTS:
#   [Optional] {timestamp flag}: -ts
# OUTPUTS:
#   [Default]
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dira.anon.pcap.gz
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dira.stats
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.anon.pcap.gz
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.stats
#
#   [Timestamp]
#     20240418-181500
#     20240523-210000
#     20240620-191500
#     20240718-190000
#
# EXAMPLES:
#   python3 100g-anon_download-objects.py -ts {timestamp}
# ASSUMPTIONS:
#   1) [IMPORTANT] `swift_config.ini` is configured with the following credentials
#        aws_access_key_id
#        aws_secret_access_key
#-

import os
import json
import boto3
import botocore
import argparse
import configparser

HOME = os.path.abspath(os.getcwd())
SWIFT_CONFIG = f"{HOME}/swift_config.ini"

# Configurations
config = configparser.ConfigParser()
config.read(SWIFT_CONFIG)
access_config = config["100g_s3_access"]

parser = argparse.ArgumentParser(description='Generate anchor file templates')
parser.add_argument('-ts', '--timestamps', dest='timestamps', action='store_true', default=False, help='List unique timestamps of objects')
args = parser.parse_args()

#boto3.set_stream_logger(name='botocore')  # this enables debug tracing
session = boto3.Session()
s3_client = session.client(
    service_name = 's3',
    endpoint_url = access_config["endpoint_url"],
    aws_access_key_id = access_config["aws_access_key_id"],
    aws_secret_access_key = access_config["aws_secret_access_key"],
    config=botocore.client.Config(signature_version='s3')
)

results = []
response = s3_client.list_objects(Bucket=access_config["bucket"])

# Print out objects in bucket
for obj in response["Contents"]:
    if args.timestamps:
        # Example file: monitor=100g-01/year=2024/mon=06/date=20240620-191500.UTC/20240620-191500.dira.anon.pcap.gz
        results.append((obj["Key"].split("/")[-1]).split(".")[0])
    else:
        print(obj["Key"])

if args.timestamps:
    [print(x) for x in sorted(set(results))]
