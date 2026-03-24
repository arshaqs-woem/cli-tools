import os
import sys
from collections import defaultdict


def scan_folder(folder_path, filter_ext=None, exclude_hidden=False):
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid folder.")
        sys.exit(1)

    total_files = 0
    total_size = 0
    largest_file = ("", 0)
    oldest_file = ("", float("inf"))
    newest_file = ("", 0)
    file_types = defaultdict(int)

    for root, dirs, files in os.walk(folder_path):
        if exclude_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            if exclude_hidden and filename.startswith("."):
                continue

            ext = os.path.splitext(filename)[1].lower()

            if filter_ext and ext != filter_ext:
                continue

            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
            except OSError:
                continue

            total_files += 1
            total_size += size

            if size > largest_file[1]:
                largest_file = (filepath, size)

            if mtime < oldest_file[1]:
                oldest_file = (filepath, mtime)

            if mtime > newest_file[1]:
                newest_file = (filepath, mtime)

            file_types[ext if ext else "(no extension)"] += 1

    return total_files, total_size, largest_file, oldest_file, newest_file, file_types, exclude_hidden


def format_size(size_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def format_time(mtime):
    import datetime
    return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")


def generate_report(folder_path, total_files, total_size, largest_file, oldest_file, newest_file, file_types, filter_ext=None, exclude_hidden=False):
    lines = []
    lines.append("=" * 40)
    lines.append("FOLDER SCAN REPORT")
    lines.append("=" * 40)
    lines.append(f"Folder:       {folder_path}")
    if filter_ext:
        lines.append(f"Filter:       {filter_ext} files only")
    if exclude_hidden:
        lines.append(f"Hidden files: excluded")
    lines.append(f"Total files:  {total_files}")
    lines.append(f"Total size:   {format_size(total_size)}")

    if largest_file[0]:
        lines.append(f"Largest file: {largest_file[0]} ({format_size(largest_file[1])})")
    else:
        lines.append("Largest file: N/A")

    if oldest_file[0]:
        lines.append(f"Oldest file:  {oldest_file[0]} ({format_time(oldest_file[1])})")
        lines.append(f"Newest file:  {newest_file[0]} ({format_time(newest_file[1])})")
    else:
        lines.append("Oldest file:  N/A")
        lines.append("Newest file:  N/A")

    lines.append("\nFile types breakdown:")
    for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
        lines.append(f"  {ext:<20} {count} file(s)")

    lines.append("=" * 40)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python folder_scanner.py <folder_path> [--ext .pdf] [--no-hidden]")
        sys.exit(1)

    folder_path = sys.argv[1]
    filter_ext = None
    exclude_hidden = "--no-hidden" in sys.argv

    if "--ext" in sys.argv:
        idx = sys.argv.index("--ext")
        if idx + 1 < len(sys.argv):
            filter_ext = sys.argv[idx + 1].lower()
            if not filter_ext.startswith("."):
                filter_ext = "." + filter_ext

    total_files, total_size, largest_file, oldest_file, newest_file, file_types, exclude_hidden = scan_folder(folder_path, filter_ext, exclude_hidden)
    report = generate_report(folder_path, total_files, total_size, largest_file, oldest_file, newest_file, file_types, filter_ext, exclude_hidden)

    print(report)

    report_path = os.path.join(folder_path, "scan_report.txt")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
