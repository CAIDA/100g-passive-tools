#+
# NAME:
#   100g-anon_list-objects.py
# PURPOSE:
#   List the files in the 100g-anon-pcap bucket/container 
# INPUTS:
#   [Optional] {timestamp flag}: -ts
#   [Optional] {bucket flag}: -b
# OUTPUTS:
#   [Default]
#     monitor=100g-01/mon=04/date=20240418-181500.UTC/20240418-181500.dira.anon.pcap.gz
#     monitor=100g-01/mon=04/date=20240418-181500.UTC/20240418-181500.dira.stats
#     monitor=100g-01/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.anon.pcap.gz
#     monitor=100g-01/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.stats
#
#   [Timestamp]
#     20240418-181500
#     20240523-210000
#     20240620-191500
#     20240718-190000
#
# EXAMPLES:
#   python3 100g-anon_list-objects.py
#   python3 100g-anon_list-objects.py -ts {timestamp}
#   python3 100g-anon_list-objects.py -b {bucket}
#   python3 100g-anon_list-objects.py -ts {timestamp} -b {bucket}
# ASSUMPTIONS:
#   1) [IMPORTANT] `swift_config.ini` is configured with the following credentials
#        buckets
#        aws_access_key_id
#        aws_secret_access_key
#-

import os
import json
import boto3
import botocore
import argparse
import configparser
from botocore.exceptions import ClientError

HOME = os.path.abspath(os.getcwd())
SWIFT_CONFIG = f"{HOME}/swift_config.ini"

# Configurations
config = configparser.ConfigParser()
config.read(SWIFT_CONFIG)
access_config = config["100g_s3_access"]

parser = argparse.ArgumentParser(description='List files in 100g-anon-pcap Container')
parser.add_argument('-ts', '--timestamps', dest='timestamps', action='store_true', default=False, help='List unique timestamps of objects')
parser.add_argument('-ab', '--allbuckets', dest='buckets', action='store_true', default=True, help='List objects from all buckets (Default)')
parser.add_argument('-b', '--bucket', dest='bucket', help='List objects from one bucket')
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
if args.bucket:
    try:
        response = s3_client.list_objects(Bucket=args.bucket)
    except ClientError as e:
        print(f"Error occurred: {e}")

    # Print out objects in bucket
    for obj in response["Contents"]:
        if args.timestamps:
            # Example file: monitor=100g-01/mon=06/date=20240620-191500.UTC/20240620-191500.dira.anon.pcap.gz
            results.append((obj["Key"].split("/")[-1]).split(".")[0])
        else:
            print(obj["Key"])
else:
    # Print from all buckets
    responses = []
    try:
        for bucket in access_config["buckets"].split():
            response = s3_client.list_objects(Bucket=bucket)
            responses.append(response)
    except ClientError as e:
        print(f"Error occurred: {e}")

    # Print out objects in each bucket
    for response in responses:
        for obj in response["Contents"]:
            if args.timestamps:
                # Example file: monitor=100g-01/mon=06/date=20240620-191500.UTC/20240620-191500.dira.anon.pcap.gz
                results.append((obj["Key"].split("/")[-1]).split(".")[0])
            else:
                print(obj["Key"])


# Print out unique timestamps
if args.timestamps:
    [print(x) for x in sorted(set(results))]
