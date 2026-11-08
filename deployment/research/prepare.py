"""Prepare a private-network deployment and an endpoint-specific extension copy.

Only local files are created. This command neither runs Docker nor installs trust.
"""

import argparse
import ipaddress
import json
import re
import secrets
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ip", required=True, help="Fixed RFC1918 IPv4 address of the university host"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New directory outside the repository or under its ignored workspace/",
    )
    parser.add_argument(
        "--retention-days",
        required=True,
        type=int,
        help="Approved retention, 1 through 365 days",
    )
    parser.add_argument(
        "--protocol", default="research-v1", help="Approved protocol version"
    )
    args = parser.parse_args()
    try:
        ip = ipaddress.IPv4Address(args.ip)
        if not any(ip in network for network in PRIVATE_NETWORKS):
            raise ValueError
    except ValueError:
        parser.error("--ip must be a private RFC1918 IPv4 address")
    if not 1 <= args.retention_days <= 365:
        parser.error("--retention-days must be between 1 and 365")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", args.protocol):
        parser.error("Invalid protocol version")
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "workspace"):
        parser.error("Use ignored workspace/ or a directory outside the repository")
    if output.exists():
        parser.error(
            "Output already exists; existing keys/data will not be overwritten"
        )
    # Refuse existing targets before generating credentials. On failure preserve
    # the partial directory for operator inspection rather than deleting files.
    try:
        output.mkdir(parents=True, mode=0o700)
        secret_dir = output / "secrets"
        secret_dir.mkdir(mode=0o700)
        for name in ("admin", "enrollment"):
            path = secret_dir / f"{name}.txt"
            path.touch(mode=0o600, exist_ok=False)
            path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
            # Local Compose mounts file secrets without remapping their owner.
            # The non-root container needs read access; the enclosing directories
            # stay 0700. On Windows, apply the operator-only ACL in the runbook.
            path.chmod(0o444)
        extension = output / "extension"
        shutil.copytree(ROOT / "browser-extension" / "extension", extension)
        manifest_path = extension / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        origin = f"https://{ip}"
        manifest["host_permissions"].append(origin + "/*")
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        (extension / "research-config.js").write_text(
            "// Study-specific public endpoint; never put credentials here.\n"
            f"globalThis.RESEARCH_API_ORIGIN = {json.dumps(origin)};\n",
            encoding="utf-8",
        )
        env = {
            "RESEARCH_SERVER_IP": str(ip),
            "RESEARCH_PROTOCOL_VERSION": args.protocol,
            "RESEARCH_RETENTION_DAYS": str(args.retention_days),
            "RESEARCH_ADMIN_SECRET_FILE": (secret_dir / "admin.txt").as_posix(),
            "RESEARCH_ENROLLMENT_SECRET_FILE": (
                secret_dir / "enrollment.txt"
            ).as_posix(),
        }
        (output / ".env").write_text(
            "".join(
                f"{key}={json.dumps(value) if key.endswith('_FILE') else value}\n"
                for key, value in env.items()
            ),
            encoding="utf-8",
        )
    except OSError:
        parser.exit(
            1,
            "Preparation failed. Inspect the output directory; no existing files were removed.\n",
        )
    print(f"Prepared local deployment files in {output}")
    print(
        "Keep secrets/ and .env restricted to the operator. Distribute only extension/ and the verified public CA certificate."
    )
    print("No service was started and no client trust was installed.")


if __name__ == "__main__":
    main()
