# 100g-passive-tools
This repository contains code recipes to demonstrate how to access CAIDA's 100G passive pcap data using various methods.

---
Clone the repository into an environment that has a minimum of **2TB of disk space**
```
git clone https://github.com/CAIDA/100g-passive-tools.git
```

### Configuration
---
In order to access CAIDA's swift server, a `swift_config.ini` file will have to be configured in the repository directory, using the AWS S3 credentials provided in the confirmation email (`aws_access_key_id` and `aws_secret_access_key`).<br/><br/>
**Note:** One can use the following config file template to get started: [swift_config-example.ini](https://github.com/CAIDA/100g-passive-tools/blob/main/swift_config-example.ini)

### Considerations

---
Each one-directional anonymized pcap file, captured monthly, can reach up to approximately **1TB in size**, so users will need more than **2TB of space** to download the entire one-hour capture.

### Troubleshooting

---
Refer to the following [Wiki Page](https://github.com/CAIDA/100g-passive-tools/wiki/Troubleshooting) to troubleshoot commonly found errors.

<br/>

# Access Methods
**Note:** Refer to the [requirements.txt](https://github.com/CAIDA/100g-passive-tools/blob/main/requirements.txt) file to install the dependencies needed for the recipes.
<br/><br/>

### AWS SDK (boto3)

---
**Note:** This method requires a `swift_config.ini` file to be configured, and assumes you've installed [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) locally.

Refer to the following recipes to download or list out files for a given capture, [100g-anon_download-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_download-objects.py) and [100g-anon_list-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_list-objects.py)

<br/>

### AWS CLI

---
**Note:** This method requires your `~/.aws/credentials` file to be configured, and assumes you've set up [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) locally.<br/>
For installing instructions, reference [AWS Documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
```
[default]
aws_access_key_id = 
aws_secret_access_key = 
```

**List out files in the 100g-anon-pcap bucket/container**<br/>
```
aws s3api list-objects --bucket 100g-anon-pcap-{year} --endpoint-url https://hermes.caida.org --output text
```
**Note:** `--output {text|json|table}`

**Download a file in the 100g-anon-pcap-{year} bucket/container**<br/>
```
aws s3api get-object --bucket 100g-anon-pcap-{year} --key monitor=100g-01/mon=05/date=20240523-210000.UTC/20240523-210000.dira.stats --endpoint-url https://hermes.caida.org --output text 20240523-210000.dira.stats
```
