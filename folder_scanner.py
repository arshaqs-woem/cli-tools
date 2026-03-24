import os
import sys
from collections import defaultdict


def scan_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid folder.")
        sys.exit(1)

    total_files = 0
    total_size = 0
    largest_file = ("", 0)
    file_types = defaultdict(int)

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue

            total_files += 1
            total_size += size

            if size > largest_file[1]:
                largest_file = (filepath, size)

            ext = os.path.splitext(filename)[1].lower()
            file_types[ext if ext else "(no extension)"] += 1

    return total_files, total_size, largest_file, file_types


def format_size(size_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def generate_report(folder_path, total_files, total_size, largest_file, file_types):
    lines = []
    lines.append("=" * 40)
    lines.append("FOLDER SCAN REPORT")
    lines.append("=" * 40)
    lines.append(f"Folder:       {folder_path}")
    lines.append(f"Total files:  {total_files}")
    lines.append(f"Total size:   {format_size(total_size)}")

    if largest_file[0]:
        lines.append(f"Largest file: {largest_file[0]} ({format_size(largest_file[1])})")
    else:
        lines.append("Largest file: N/A")

    lines.append("\nFile types breakdown:")
    for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
        lines.append(f"  {ext:<20} {count} file(s)")

    lines.append("=" * 40)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python folder_scanner.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    total_files, total_size, largest_file, file_types = scan_folder(folder_path)
    report = generate_report(folder_path, total_files, total_size, largest_file, file_types)

    print(report)

    report_path = os.path.join(folder_path, "scan_report.txt")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
