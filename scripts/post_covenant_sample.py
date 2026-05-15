#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib import request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--facility", required=True, choices=["educa", "payearly", "nomina"])
    parser.add_argument("--file", required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/covenants/calculate")
    args = parser.parse_args()

    payload = json.dumps(json.loads(Path(args.file).read_text())).encode()
    req = request.Request(
        args.url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Fence-Facility-Type": args.facility,
        },
        method="POST",
    )

    with request.urlopen(req) as response:
        print(response.read().decode())


if __name__ == "__main__":
    main()
