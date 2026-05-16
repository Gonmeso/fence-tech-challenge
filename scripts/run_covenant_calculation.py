#!/usr/bin/env python3
import argparse
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from business.calculator.resolver import CalculatorResolver  # noqa: E402
from business.covenant import CovenantHandler  # noqa: E402
from business.enums import FacilityType  # noqa: E402
from core.settings import get_settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--facility", required=True, choices=["educa", "payearly", "nomina"])
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    payload = Path(args.file).read_text()
    handler = CovenantHandler(CalculatorResolver(get_settings()))
    result = handler.calculate(
        facility_type=FacilityType(args.facility),
        payload=payload,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
