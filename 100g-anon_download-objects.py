#+
# NAME:
#   100g-anon_download-objects.py
# PURPOSE:
#   Downloads anonymized pcap files for a given timestamp 
# INPUTS:
#   {timestamp} - yyyymmdd-hhmmss 
#     e.g. 20240418-181500
# OUTPUTS:
#   ./downloads/monitor=100g-01/year={YYYY}/mon={MM}/date={timestamp}.UTC/{file}
# EXAMPLES:
#   python3 100g-anon_download-objects.py {timestamp}
# ASSUMPTIONS:
#   1) [IMPORTANT] Assumes that one has at least 3TB of disk space to store
#      the two pcap files (one for each direction).
#
#   2) [IMPORTANT] `swift_config.ini` is configured with the following credentials
#        aws_access_key_id
#        aws_secret_access_key
#-

import re
import os
import sys
import boto3
import botocore
import argparse
import configparser
from pathlib import Path

HOME = os.path.abspath(os.getcwd())
SWIFT_CONFIG = f"{HOME}/swift_config.ini"

# Configurations
config = configparser.ConfigParser()
config.read(SWIFT_CONFIG)
access_config = config["100g_s3_access"]

parser = argparse.ArgumentParser(description='Generate anchor file templates')
parser.add_argument('-ts', '--timestamp', dest='timestamp', help='Specifiy which capture to download')
args = parser.parse_args()

def config_client() -> object:
    """
    Configures the s3 client
    """
    #boto3.set_stream_logger(name='botocore')  # this enables debug tracing
    session = boto3.Session()
    s3_client = session.client(
        service_name='s3',
        endpoint_url = access_config["endpoint_url"],
        aws_access_key_id = access_config["aws_access_key_id"],
        aws_secret_access_key = access_config["aws_secret_access_key"],
        config=botocore.client.Config(signature_version='s3v4'),
    )
    return s3_client

def download(s3_client:object, key:str, filename:str) -> None:
    """
    Retrieves files from swift bucket/container
    """
    try:
        s3_client.download_file(Bucket=access_config["bucket"], Key=key, Filename=filename)
        print(f"Downloaded {os.path.basename(key)} into {filename}")
    except Exception as error:
        print("-"*50)
        print(f"Error: Unable to download file: {key}")
        print(f"{error}")
        print("-"*50)

def download_files() -> None:
    """
    Downloads the files associated with the specified timestamp
    """
    s3_client = config_client()
    # e.g. 20240418-181500
    year = (args.timestamp).split("-")[0][:4]
    month = (args.timestamp).split("-")[0][4:6]

    file_prefix = f"monitor=100g-01/year={year}/mon={month}/date={args.timestamp}.UTC"

    # Have to create directories in order to download files
    file_path = f"downloads/{file_prefix}"
    print(f"Creating directory path: {file_path}")
    Path(file_path).mkdir(parents=True, exist_ok=True)

    for direction in ["a", "b"]:
        for file_suffix in ["stats"]: # , "anon.pcap.gz"
            key = f"{file_prefix}/{args.timestamp}.dir{direction}.{file_suffix}"
            filename = f'{HOME}/downloads/{key}'
            download(s3_client, key, filename)

def main():
    # Validates Input
    ts_pattern = re.compile('\d{8}-\d{6}') # e.g. 20240418-181500
    if not (ts_pattern.match(str(args.timestamp))):
        print(f"Incorrect timestamp format: {args.timestamp} --> YYYYMMDD-HHMMSS")
        sys.exit()

    download_files()

if __name__ == "__main__":
    main()
