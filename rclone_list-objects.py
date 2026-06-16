# +
# NAME:
#   rclone_list-objects.py
# PURPOSE:
#   Lists objects in one or more 100g-anon-pcap containers via rclone + native Swift.
#   Lists ALL objects with no truncation (the boto3 equivalent caps at 1000 objects).
# INPUTS:
#   [Optional] {timestamp flag}: -ts / --timestamps
#     Boolean flag — prints unique sorted timestamps instead of full object paths.
#
#   [Optional] {bucket}: -b / --bucket
#     List objects from a single container.
#
#   [Optional] {allbuckets}: -ab / --allbuckets (default)
#     List objects from multiple containers supplied via --buckets or RCLONE_BUCKETS.
#
#   [Optional] {buckets list}: --buckets "c1 c2 ..."
#     Space-separated container names (also readable from RCLONE_BUCKETS env var).
#     Required when using --allbuckets and no -b is given.
#     Note: account-level enumeration (rclone lsd limbo:) returns 403 for data
#     users — containers must be named explicitly here.
#
#   [Optional] {remote}: --remote
#     rclone remote name (default: "limbo"; override via RCLONE_REMOTE env var).
#
#   [Optional] {log_level}: --log-level (default: INFO)
# OUTPUTS:
#   [Default]
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dira.anon.pcap.gz
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dira.stats
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.anon.pcap.gz
#     monitor=100g-01/year=2024/mon=04/date=20240418-181500.UTC/20240418-181500.dirb.stats
#
#   [With -ts]
#     20240418-181500
#     20240523-210000
#     20240620-191500
#
# EXAMPLES:
#   python3 rclone_list-objects.py -b 100g-anon-pcap-2024
#   python3 rclone_list-objects.py -ts -b 100g-anon-pcap-2024
#   python3 rclone_list-objects.py --buckets "100g-anon-pcap-2024 100g-anon-pcap-2025"
#   python3 rclone_list-objects.py -ts --buckets "100g-anon-pcap-2024 100g-anon-pcap-2025"
# ASSUMPTIONS:
#   1) [IMPORTANT] rclone is installed and the [limbo] remote is configured in
#      ~/.config/rclone/rclone.conf (see rclone.conf-example).
#
#   2) Account-level enumeration (rclone lsd limbo:) returns 403 for data users.
#      Always supply containers explicitly via -b or --buckets / RCLONE_BUCKETS.
#
#   3) Connection from a registered IP range is required — access is gated by
#      a Swift ACL on the container.
# -

import os
import sys
import logging
import argparse
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_REMOTE = os.environ.get("RCLONE_REMOTE", "limbo")
DEFAULT_BUCKETS_ENV = os.environ.get("RCLONE_BUCKETS", "")

parser = argparse.ArgumentParser(
    description="List files in 100g-anon-pcap containers via rclone + native Swift")
parser.add_argument("-ts", "--timestamps", dest="timestamps", action="store_true",
                    default=False, help="List unique timestamps of objects")
parser.add_argument("-ab", "--allbuckets", dest="allbuckets", action="store_true",
                    default=True, help="List objects from all known containers (default)")
parser.add_argument("-b", "--bucket", dest="bucket",
                    help="List objects from one container")
parser.add_argument("--buckets", dest="buckets_arg", default=DEFAULT_BUCKETS_ENV,
                    metavar="BUCKETS",
                    help="Space-separated container names for --allbuckets (env: RCLONE_BUCKETS)")
parser.add_argument("--remote", dest="remote", default=DEFAULT_REMOTE,
                    help=f"rclone remote name (default: {DEFAULT_REMOTE!r}; override via RCLONE_REMOTE)")
parser.add_argument("--log-level", dest="log_level", default="INFO",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    help="Logging verbosity (default: INFO)")


def list_container(remote: str, container: str) -> list[str] | None:
    """Return all object paths in `container` via rclone lsf."""
    cmd = ["rclone", "lsf", "-R", "--files-only", f"{remote}:{container}"]
    log.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("rclone lsf failed for %s: %s", container, result.stderr.strip())
        return None
    return [line for line in result.stdout.splitlines() if line]


def extract_timestamp(path: str) -> str:
    return path.split("/")[-1].split(".")[0]


def main() -> None:
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    if args.bucket:
        containers = [args.bucket]
    else:
        if not args.buckets_arg:
            log.error(
                "No container specified. Use -b <container> for one container, "
                "or --buckets 'c1 c2 ...' (or RCLONE_BUCKETS env var) for multiple."
            )
            sys.exit(1)
        containers = args.buckets_arg.split()

    results: list[str] = []
    failed: list[str] = []

    for container in containers:
        keys = list_container(args.remote, container)
        if keys is None:
            failed.append(container)
            continue
        for key in keys:
            if args.timestamps:
                results.append(extract_timestamp(key))
            else:
                print(key)

    if args.timestamps:
        for ts in sorted(set(results)):
            print(ts)

    if failed:
        log.error("Failed to list: %s", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
