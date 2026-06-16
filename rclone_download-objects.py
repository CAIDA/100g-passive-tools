# +
# NAME:
#   rclone_download-objects.py
# PURPOSE:
#   Downloads anonymized pcap files for a given timestamp via rclone + native Swift.
#   Preferred over 100g-anon_download-objects.py (boto3/S3) for large .anon.pcap.gz
#   files — native Swift auth avoids SignatureDoesNotMatch errors on segmented objects.
# INPUTS:
#   [Required] {timestamp} - YYYYMMDD-HHMMSS
#     e.g. 20240418-181500
#
#   [Required] {bucket} - 100g-anon-pcap-{year}  (Swift container name)
#     e.g. 100g-anon-pcap-2024
#
#   [Optional] {stats_only} - By default, only download stats files.
#     -s / --stats-only : Download only stats files (default: True)
#     -f / --full       : Download stats and anon.pcap.gz files
#
#   [Optional] {remote} - rclone remote name
#     default: "limbo" (override via --remote or RCLONE_REMOTE env var)
#
#   [Optional] {log_level} - Logging verbosity (default: INFO)
# OUTPUTS:
#   ./downloads/monitor=100g-01/year={YYYY}/mon={MM}/date={timestamp}.UTC/{file}
# EXAMPLES:
#   python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024
#   python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024 --dry-run
#   python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024 --full
#   python3 rclone_download-objects.py -ts 20240418-181500 -b 100g-anon-pcap-2024 --remote my_remote
# ASSUMPTIONS:
#   1) [IMPORTANT] rclone is installed and the [limbo] remote is configured in
#      ~/.config/rclone/rclone.conf (see rclone.conf-example).
#
#   2) [IMPORTANT] Assumes at least 3TB of disk space to store both pcap files
#      (one per direction). Individual files can exceed 1TB.
#
#   3) Connection from a registered IP range is required — access is gated by
#      a Swift ACL on the container.
#
#   4) rclone cannot verify MD5 on segmented large objects. Run
#      `gzip -t <file>.anon.pcap.gz` to verify integrity after download.
# -

import re
import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_REMOTE = os.environ.get("RCLONE_REMOTE", "limbo")

parser = argparse.ArgumentParser(
    description="Download files for a given capture via rclone + native Swift")
parser.add_argument("-s", "--stats-only", dest="stats_only", action="store_true",
                    help="Download only stats files (default)")
parser.add_argument("-f", "--full", dest="stats_only", action="store_false",
                    help="Download full pcap and stats files")
parser.set_defaults(stats_only=True)
parser.add_argument("-ts", "--timestamp", dest="timestamp",
                    help="Specify which capture to download (YYYYMMDD-HHMMSS)")
parser.add_argument("-b", "--bucket", dest="bucket",
                    help="Specify which container to download from (e.g. 100g-anon-pcap-2024)")
parser.add_argument("--remote", dest="remote", default=DEFAULT_REMOTE,
                    help=f"rclone remote name (default: {DEFAULT_REMOTE!r}; override via RCLONE_REMOTE)")
parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False,
                    help="Show which files would be downloaded without transferring them")
parser.add_argument("--log-level", dest="log_level", default="INFO",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    help="Logging verbosity (default: INFO)")


def build_prefix(timestamp: str) -> str:
    year = timestamp[:4]
    month = timestamp[4:6]
    return f"monitor=100g-01/year={year}/mon={month}/date={timestamp}.UTC"


def expected_keys(timestamp: str, stats_only: bool) -> list[str]:
    prefix = build_prefix(timestamp)
    file_suffixes = ["stats"] if stats_only else ["stats", "anon.pcap.gz"]
    return [
        f"{prefix}/{timestamp}.dir{direction}.{file_suffix}"
        for direction in ["a", "b"]
        for file_suffix in file_suffixes
    ]


def run_rclone(remote: str, bucket: str, key: str, filename: Path, dry_run: bool = False) -> int:
    src = f"{remote}:{bucket}/{key}"

    cmd = [
        "rclone", "copyto",
        "--retries", "5",
        "--low-level-retries", "20",
        "--stats", "10s",
    ]
    if dry_run:
        cmd += ["--dry-run"]
    cmd += [src, str(filename)]

    log.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    return result.returncode


def main() -> None:
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    ts_pattern = re.compile(r"\d{8}-\d{6}")
    errors: list[str] = []

    if not args.timestamp:
        errors.append("Timestamp is required --> -ts YYYYMMDD-HHMMSS")
    elif not ts_pattern.fullmatch(args.timestamp):
        errors.append(f"Incorrect timestamp format: {args.timestamp!r} --> YYYYMMDD-HHMMSS")

    if not args.bucket:
        errors.append("Bucket/container is required --> -b 100g-anon-pcap-{year}")

    if errors:
        for msg in errors:
            log.error(msg)
        sys.exit(1)

    prefix = build_prefix(args.timestamp)
    dst_dir = Path.cwd() / "downloads" / prefix
    keys = expected_keys(args.timestamp, args.stats_only)

    if not args.dry_run:
        print(f"Creating directory path: {dst_dir}")
        dst_dir.mkdir(parents=True, exist_ok=True)
    else:
        for key in keys:
            filename = Path.cwd() / "downloads" / key
            print(f"Would download {key} into {filename}")
        return

    failures: list[str] = []
    for key in keys:
        filename = Path.cwd() / "downloads" / key
        rc = run_rclone(args.remote, args.bucket, key, filename, args.dry_run)
        if rc == 0:
            if not args.dry_run:
                print(f"Downloaded {Path(key).name} into {filename}")
            continue

        failures.append(key)
        log.error("Unable to download file: %s", key)

    if failures:
        log.error("Failed to download %d file(s)", len(failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
