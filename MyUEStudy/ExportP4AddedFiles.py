import argparse
import csv
import locale
import marshal
import subprocess
from datetime import datetime
from pathlib import PurePosixPath


DEFAULT_USER = "testuser"
DEFAULT_P4_CWD = r"F:\ProjectRoot"
DEFAULT_ROOT = r"F:\ProjectRoot\Scripts\..."
DEFAULT_OUT_CSV = r"F:\p4_added_by_testuser.csv"
DEFAULT_EXTS = (".h", ".cpp")


def decode(value):
    if isinstance(value, bytes):
        encoding = locale.getpreferredencoding(False) or "utf-8"
        return value.decode(encoding, errors="replace")
    return value


def format_p4_errors(records, stderr):
    messages = []
    for record in records:
        if record.get("code") == "error":
            data = record.get("data", "").strip()
            if data:
                messages.append(data)

    if stderr.strip():
        messages.append(stderr.strip())

    if not messages:
        messages.append("p4 returned a non-zero exit code but did not provide an error message.")

    return "\n".join(messages)


def run_p4_marshal(args, p4_cwd):
    proc = subprocess.Popen(
        ["p4", "-G", "-d", p4_cwd, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    records = []
    while True:
        try:
            record = marshal.load(proc.stdout)
        except EOFError:
            break

        records.append({decode(k): decode(v) for k, v in record.items()})

    stderr = proc.stderr.read().decode("utf-8", errors="replace")
    code = proc.wait()

    if code != 0:
        detail = format_p4_errors(records, stderr)
        raise RuntimeError(f"p4 {' '.join(args)} failed:\n{detail}")

    return records


def get_changes(user, root, p4_cwd):
    records = run_p4_marshal([
        "changes",
        "-s",
        "submitted",
        "-u",
        user,
        root,
    ], p4_cwd)

    changes = []
    for record in records:
        if record.get("code") == "stat" and "change" in record:
            changes.append({
                "change": record["change"],
                "time": record.get("time", ""),
                "user": record.get("user", ""),
                "client": record.get("client", ""),
                "description": record.get("desc", "").replace("\n", " ").strip(),
            })

    return changes


def get_added_files(change, extensions, p4_cwd):
    records = run_p4_marshal(["describe", "-s", change["change"]], p4_cwd)
    rows = []

    for record in records:
        if record.get("code") != "stat":
            continue

        index = 0
        while f"depotFile{index}" in record:
            depot_file = record[f"depotFile{index}"]
            action = record.get(f"action{index}", "")
            rev = record.get(f"rev{index}", "")
            filetype = record.get(f"type{index}", "")
            suffix = PurePosixPath(depot_file).suffix.lower()

            if action == "add" and suffix in extensions:
                submitted_time = ""
                if change["time"]:
                    submitted_time = datetime.fromtimestamp(int(change["time"])).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                rows.append({
                    "change": change["change"],
                    "submitted_time": submitted_time,
                    "user": change["user"],
                    "client": change["client"],
                    "depot_file": depot_file,
                    "rev": rev,
                    "action": action,
                    "filetype": filetype,
                    "description": change["description"],
                })

            index += 1

    return rows


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export submitted Perforce add actions for .h/.cpp files to CSV."
    )
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--p4-cwd", default=DEFAULT_P4_CWD)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--out", default=DEFAULT_OUT_CSV)
    parser.add_argument("--ext", nargs="+", default=list(DEFAULT_EXTS))
    return parser.parse_args()


def main():
    args = parse_args()
    extensions = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in args.ext}

    all_rows = []
    changes = get_changes(args.user, args.root, args.p4_cwd)
    print(f"Found {len(changes)} submitted changelists by {args.user}")

    for index, change in enumerate(changes, 1):
        print(f"[{index}/{len(changes)}] Checking change {change['change']}")
        all_rows.extend(get_added_files(change, extensions, args.p4_cwd))

    with open(args.out, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "change",
                "submitted_time",
                "user",
                "client",
                "depot_file",
                "rev",
                "action",
                "filetype",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Exported {len(all_rows)} files to: {args.out}")


if __name__ == "__main__":
    main()
