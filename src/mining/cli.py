from __future__ import annotations
import argparse
import json
import logging
from src.mining.config import DataConfig, TrainConfig

def _add_dataclass_args(parser: argparse.ArgumentParser, cls) -> None:
    """Add one --option per dataclass field, using the field default."""
    for name, field in cls.__dataclass_fields__.items():
        default = field.default
        flag = "--" + name.replace("_", "-")
        if isinstance(default, bool):
            parser.add_argument(flag, type=lambda s: s.lower() in ("1", "true", "yes"), default=default)
        else:
            parser.add_argument(flag, type=type(default), default=default)


def _from_args(cls, args: argparse.Namespace):
    return cls(**{name: getattr(args, name) for name in cls.__dataclass_fields__})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mining", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("synthetic", help="write fake data for a smoke test")
    p.add_argument("--out", default="data/synthetic")

    p = sub.add_parser("build-dataset", help="export patches from Earth Engine")
    _add_dataclass_args(p, DataConfig)
    p.add_argument("--limit", type=int, default=None, help="only export the first N sites")

    p = sub.add_parser("train", help="train and test the baseline")
    _add_dataclass_args(p, TrainConfig)

    p = sub.add_parser("evaluate", help="re-evaluate a saved run")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--data-dir", default="data/mining_patches")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    if args.command == "synthetic":
        from src.mining.synthetic import make_synthetic_dataset
        print(make_synthetic_dataset(args.out))
    elif args.command == "build-dataset":
        from src.mining.build_dataset import build_dataset
        print(build_dataset(_from_args(DataConfig, args), limit=args.limit))
    elif args.command == "train":
        from src.mining.train import train
        result = train(_from_args(TrainConfig, args))
        print(json.dumps({"val": result["val"], "test": result["test"]}, indent=2))
    elif args.command == "evaluate":
        from src.mining.evaluate import evaluate_run
        print(json.dumps(evaluate_run(args.run_dir, args.data_dir, args.split), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())