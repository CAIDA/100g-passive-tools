# 100g-passive-tools

Scripts to access CAIDA's 100G passive pcap data. Two access methods are provided; **rclone + native Swift is recommended** for all users who wish to download the large `.anon.pcap.gz` files.

## Access methods at a glance

| Method | When to use | Status |
|---|---|---|
| **rclone + native Swift** | Large pcap downloads; built-in retries | **Preferred method of access** |
| **boto3 / AWS S3** | Small `.stats` files; legacy approach | Retained for existing setups with working S3 credentials |

The S3-compatible path can fail with `SignatureDoesNotMatch` (HTTP 403) on large `.anon.pcap.gz` objects due to an ongoing Swift storage reorganization. The [`boto3` branch](https://github.com/CAIDA/100g-passive-tools/tree/boto3) is a frozen legacy snapshot kept for reference.

Native Swift authentication resolves segmented large objects correctly, and includes retries that should solve the error mentioned above.

---

## Prerequisites

Individual `.anon.pcap.gz` files can run >1 TB each. A full one-hour capture (both directions) requires at least 2 TB of disk space to download.

```bash
git clone https://github.com/CAIDA/100g-passive-tools.git
```

**rclone (preferred method):** Install from [rclone.org/install](https://rclone.org/install) or via a package manager. The `rclone_*.py` scripts require only standard library Python.

**boto3 method only:** Tested on Python 3.11. Install dependencies with `pip install -r requirements.txt`.

---

## rclone + Swift method (preferred)

The rclone scripts are intended as a direct replacement for the original boto3 scripts. The common flags are the same: use `-ts` for the capture timestamp, `-b` for the container, and `-f` / `--full` when you want the two `.anon.pcap.gz` files in addition to the default `.stats` files.

### Configuration

Copy `rclone.conf-example` to `~/.config/rclone/rclone.conf` (or your `$RCLONE_CONFIG` path) and fill in the username and password from your CAIDA-issued credentials:

```ini
[limbo]
type = swift
user = YOUR_USERNAME
key = YOUR_PASSWORD
auth = https://auth-limbo.caida.org
tenant = passive
auth_version = 3
domain = Default
endpoint_type = public
```

### Verify access

```bash
rclone ls limbo:100g-anon-pcap-2024
```

> **Note:** Data users are scoped to specific containers. Always target `limbo:<container>` directly.

### Scripts

**[rclone_list-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/rclone_list-objects.py)**

```bash
python3 rclone_list-objects.py -b 100g-anon-pcap-2024                                    # list objects
python3 rclone_list-objects.py -ts -b 100g-anon-pcap-2024                                # unique timestamps
python3 rclone_list-objects.py --buckets "100g-anon-pcap-2024 100g-anon-pcap-2025"       # multiple containers
```

**[rclone_download-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/rclone_download-objects.py)**

```bash
python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024            # stats only (default)
python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024 --dry-run  # preview
python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024 --full     # stats + pcaps
```

Downloads write to `downloads/monitor=100g-01/year={YYYY}/mon={MM}/date={ts}.UTC/`. In default mode, the script downloads the two expected `.stats` files. With `--full`, it downloads those stats files plus the two expected `.anon.pcap.gz` files.

### Integrity check

```bash
gzip -t <file>.anon.pcap.gz
```

rclone cannot verify MD5 on segmented (SLO/DLO) objects — `gzip -t` is the recommended end-to-end integrity check.

---

## boto3 / S3 method (legacy, retained)

Configure `swift_config.ini` using [swift_config-example.ini](https://github.com/CAIDA/100g-passive-tools/blob/main/swift_config-example.ini) as a template. Refer to [100g-anon_download-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_download-objects.py) and [100g-anon_list-objects.py](https://github.com/CAIDA/100g-passive-tools/blob/main/100g-anon_list-objects.py) for usage.

This approach is a bit fragile, especially while the containers are undergoing maintenance. As of June 2026, we are reorganizing the data stores on disk, which can cause this approach to fail. The transition toward `rclone` is to reconcile this fragility by authenticating via native Swift.

---

## Troubleshooting

**Access denied from your IP**
Container access is gated by a per-user IP-range ACL. Connect from the IP address registered with CAIDA. Contact CAIDA if your IP has changed.

**`SignatureDoesNotMatch` on large pcap files**
Known issue with the S3 path on segmented large objects during storage reorganization. Switch to the rclone + Swift method above.

**`Bad Request` (HTTP 400) on rclone auth**
Missing `domain = Default` in `rclone.conf`. `rclone`'s swift backend does not infer the domain — it must be set explicitly.

**403 on `rclone lsd limbo:` or account-level listing**
Expected — data users are scoped to specific containers. Target `limbo:<container>` directly (e.g. `rclone ls limbo:100g-anon-pcap-2024`).

**rclone reports skipped checksums on pcap files**
Expected. rclone cannot verify MD5 on segmented (SLO/DLO) objects. Use `gzip -t <file>.anon.pcap.gz` for integrity verification instead.

Refer to the [Wiki Troubleshooting page](https://github.com/CAIDA/100g-passive-tools/wiki/Troubleshooting) for additional guidance.
