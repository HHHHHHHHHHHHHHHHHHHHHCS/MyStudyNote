#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def normalize_resource_path(value):
    return str(value).replace("\\", "/")


def resource_name(resource_path):
    stripped = resource_path.rstrip("/")
    if not stripped:
        return ""
    return stripped.rsplit("/", 1)[-1]


def format_size(size_bytes):
    size = int(size_bytes)
    units = (
        ("GB", 1024 ** 3),
        ("MB", 1024 ** 2),
        ("KB", 1024),
    )

    for suffix, factor in units:
        if size >= factor:
            return f"{size / factor:.2f} {suffix}"

    return f"{size} B"


def entry_size(entry):
    value = entry.get("[NotInMeta]EntrySize")
    if value is not None:
        return int(value)
    return entry_block_size(entry)


def entry_block_size(entry):
    total = 0
    for block in entry.get("EntryDataBlocks") or ():
        value = block.get("Size")
        if value is not None:
            total += int(value)
    return total


def detect_text_encoding(path):
    with path.open("rb") as fp:
        bom = fp.read(4)

    if bom.startswith(b"\xff\xfe"):
        return "utf-16"
    if bom.startswith(b"\xfe\xff"):
        return "utf-16"
    if bom.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"


def iter_sidecar_entries(json_path):
    encoding = detect_text_encoding(json_path)
    with json_path.open("r", encoding=encoding) as fp:
        meta = json.load(fp)

    entries = meta.get("Meta_EntryInfos")
    if not isinstance(entries, list):
        raise ValueError("Meta_EntryInfos not found or is not a list")

    return entries


def write_sidecar_entries(writer, pak_path, json_path, include_extra_fields, min_size_bytes):
    written = 0
    for entry in iter_sidecar_entries(json_path):
        raw_path = entry.get("FilePathNameToMountPoint")
        if not raw_path:
            continue

        size_bytes = entry_size(entry)
        if size_bytes < min_size_bytes:
            continue

        res_path = normalize_resource_path(raw_path)
        row = [
            res_path,
            resource_name(res_path),
            pak_path.name,
            size_bytes,
            format_size(size_bytes),
        ]

        if include_extra_fields:
            row.extend(
                [
                    entry.get("EntryOffset", ""),
                    entry_block_size(entry),
                    "",
                    "",
                    "",
                    "SidecarJson",
                ]
            )

        writer.writerow(row)
        written += 1

    return written


def run_unrealpak_list(unrealpak, pak_path, raw_csv_path, crypto_keys=None):
    command = [str(unrealpak), str(pak_path), "-List", f"-csv={raw_csv_path}"]
    if crypto_keys:
        command.append(f"-cryptokeys={crypto_keys}")

    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def write_unrealpak_csv_entries(writer, raw_csv_path, pak_path, include_extra_fields, min_size_bytes):
    written = 0
    with raw_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            normalized = {key.strip(): value for key, value in row.items() if key is not None}
            raw_path = (normalized.get("Filename") or "").strip()
            if not raw_path or raw_path == "<Footer>":
                continue

            size_text = (normalized.get("Size") or "0").strip()
            size_bytes = int(size_text)
            if size_bytes < min_size_bytes:
                continue

            res_path = normalize_resource_path(raw_path)
            out_row = [
                res_path,
                resource_name(res_path),
                pak_path.name,
                size_bytes,
                format_size(size_bytes),
            ]

            if include_extra_fields:
                out_row.extend(
                    [
                        (normalized.get("Offset") or "").strip(),
                        "",
                        (normalized.get("Compressed") or "").strip(),
                        (normalized.get("CompressionMethod") or "").strip(),
                        (normalized.get("Deleted") or "").strip(),
                        "UnrealPak",
                    ]
                )

            writer.writerow(out_row)
            written += 1

    return written


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate a UE pak inventory CSV from sidecar JSON files, with optional UnrealPak fallback."
    )
    parser.add_argument("--input-dir", required=True, help="Directory containing .pak/.json files.")
    parser.add_argument("--output-csv", help="Inventory CSV output path. Defaults to <input-dir>/PakInventory.csv.")
    parser.add_argument("--pak-pattern", default="*.pak", help="Pak glob pattern. Default: *.pak")
    parser.add_argument("--min-size-bytes", type=int, default=0, help="Skip entries smaller than this size.")
    parser.add_argument("--include-extra-fields", action="store_true", help="Include offset/source/debug columns.")
    parser.add_argument("--use-unrealpak-fallback", action="store_true", help="Use UnrealPak when sidecar JSON is missing or invalid.")
    parser.add_argument("--unrealpak", help="Path to UnrealPak.exe.")
    parser.add_argument("--crypto-keys", help="Path to legitimate Crypto.json for encrypted pak indexes.")
    parser.add_argument("--summary-json", help="Optional summary JSON output path.")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output.")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    output_csv = Path(args.output_csv).resolve() if args.output_csv else input_dir / "PakInventory.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    unrealpak = Path(args.unrealpak) if args.unrealpak else None
    crypto_keys = Path(args.crypto_keys) if args.crypto_keys else None

    headers = ["ResourcePath", "ResourceName", "PakFile", "SizeBytes", "SizeText"]
    if args.include_extra_fields:
        headers.extend(["Offset", "CompressedSizeBytes", "Compressed", "CompressionMethod", "Deleted", "Source"])

    stats = {
        "input_dir": str(input_dir),
        "output_csv": str(output_csv),
        "pak_files_seen": 0,
        "json_files_parsed": 0,
        "json_entries_written": 0,
        "fallback_pak_files_parsed": 0,
        "fallback_entries_written": 0,
        "failed_json": [],
        "failed_pak": [],
    }

    pak_files = sorted(input_dir.glob(args.pak_pattern), key=lambda item: item.name.lower())
    stats["pak_files_seen"] = len(pak_files)

    with output_csv.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp, lineterminator="\n")
        writer.writerow(headers)

        for pak_path in pak_files:
            json_path = pak_path.with_suffix(".json")
            wrote_from_json = False

            if json_path.is_file():
                try:
                    if not args.quiet:
                        print(f"Reading JSON: {json_path.name}")
                    count = write_sidecar_entries(
                        writer,
                        pak_path,
                        json_path,
                        args.include_extra_fields,
                        args.min_size_bytes,
                    )
                    stats["json_files_parsed"] += 1
                    stats["json_entries_written"] += count
                    wrote_from_json = True
                except Exception as exc:
                    message = f"{json_path} :: {exc}"
                    stats["failed_json"].append(message)
                    print(f"warning: JSON failed: {message}", file=sys.stderr)

            if wrote_from_json or not args.use_unrealpak_fallback:
                continue

            if unrealpak is None or not unrealpak.is_file():
                stats["failed_pak"].append(f"{pak_path} :: UnrealPak not found: {unrealpak}")
                continue

            raw_csv_path = output_csv.parent / f"{pak_path.stem}.unrealpak.raw.csv"
            if not args.quiet:
                print(f"Fallback UnrealPak: {pak_path.name}")

            result = run_unrealpak_list(unrealpak, pak_path, raw_csv_path, crypto_keys)
            if result.returncode != 0:
                stats["failed_pak"].append(f"{pak_path} :: UnrealPak exit code {result.returncode}\n{result.stdout}")
                continue

            try:
                count = write_unrealpak_csv_entries(
                    writer,
                    raw_csv_path,
                    pak_path,
                    args.include_extra_fields,
                    args.min_size_bytes,
                )
                stats["fallback_pak_files_parsed"] += 1
                stats["fallback_entries_written"] += count
            except Exception as exc:
                stats["failed_pak"].append(f"{pak_path} :: {exc}")

    if args.summary_json:
        summary_json = Path(args.summary_json).resolve()
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        with summary_json.open("w", encoding="utf-8") as fp:
            json.dump(stats, fp, ensure_ascii=False, indent=2)

    print("")
    print(f"OutputCsv: {output_csv}")
    print(f"Pak files seen: {stats['pak_files_seen']}")
    print(f"JSON files parsed: {stats['json_files_parsed']}")
    print(f"JSON entries written: {stats['json_entries_written']}")
    print(f"Fallback pak files parsed: {stats['fallback_pak_files_parsed']}")
    print(f"Fallback entries written: {stats['fallback_entries_written']}")
    print(f"Failed JSON files: {len(stats['failed_json'])}")
    print(f"Failed pak fallbacks: {len(stats['failed_pak'])}")

    return 1 if stats["failed_json"] or stats["failed_pak"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
