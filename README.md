# 100g-passive-tools
This repository contains code recipes to demonstrate how to access CAIDA's 100G passive pcap data using various methods.

### Configuration
---
After sending a request using this [form](https://www.caida.org/catalog/datasets/request_user_info_forms/passive_100g_dataset_request/), once approved, you will receiving a confirmation email containing AWS S3 credentials (`aws_access_key_id` and `aws_secret_access_key`).

In order to access CAIDA's swift server, a `swift_config.ini` file will have to be configured using the credentials provided.<br/>
**Note:** One can use the following config file template to get started: [swift_config-example.ini](https://github.com/CAIDA/100g-passive-tools/blob/main/swift_config-example.ini)

### Considerations

---
Each one-directional anonymized pcap file, captured monthly, can reach up to approximately **1TB in size**, so users will need more than **2TB of space** to download the entire one-hour capture.

### Troubleshooting

---
Refer to the following [Wiki Page](https://github.com/CAIDA/100g-passive-tools/wiki/Troubleshooting) to troubleshoot commonly found errors.

<br/>

# Access Methods

### AWS SDK (boto3)

---
**Note:** This method requires a `swift_config.ini` file to be configured.

Refer to the following recipes to download or list out files for a given capture, [100g-anon_download-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_download-objects.py) and [100g-anon_list-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_list-objects.py)

### AWS CLI

---
**Note:** This method requires your `~/.aws/credentials` file to be configured.
```
[default]
aws_access_key_id = 
aws_secret_access_key = 
```

**List out files in the 100g-anon-pcap bucket/container**<br/>
```
aws s3api list-objects --bucket 100g-anon-pcap --endpoint-url https://hermes.caida.org
```

**Download a file in the 100g-anon-pcap bucket/container**<br/>
```
aws s3api get-object --bucket 100g-anon-pcap --key monitor=100g-01/year=2024/mon=05/date=20240523-210000.UTC/20240523-210000.dira.stats --endpoint-url https://hermes.caida.org --output text 20240523-210000.dira.stats
```
