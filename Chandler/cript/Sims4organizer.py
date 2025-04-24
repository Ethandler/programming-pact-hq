import os
import sys
import argparse

def scan_folder(root_path, read_bytes=1024):
    """
    Recursively scans the directory at root_path to identify problematic files.

    Functionality:
    - Finds files that are zero bytes in size.
    - Detects files that cannot be stat'ed or read (unreadable).
    - Attempts to read up to `read_bytes` bytes from each file to confirm readability.

    Args:
        root_path (str): The root directory path to start scanning from.
        read_bytes (int, optional): Number of bytes to read from each file to test readability. Defaults to 1024.

    Returns:
        dict: A dictionary with two keys:
            'zero_size' (list of str): List of filepaths that have zero bytes.
            'unreadable' (list of tuples): List of tuples (filepath, error_message) 
                                           for files that could not be read or stat'ed.
    """
    zero_size = []
    unreadable = []

    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            fullpath = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(fullpath)
            except OSError as e:
                # Could not even stat the file
                unreadable.append((fullpath, f"stat error: {e}"))
                continue

            if size == 0:
                zero_size.append(fullpath)
                continue

            # Try to open and read a small chunk
            try:
                with open(fullpath, 'rb') as f:
                    data = f.read(read_bytes)
                    # If you want, you could also verify that len(data)>0,
                    # but non-zero size almost always returns some bytes.
            except Exception as e:
                unreadable.append((fullpath, f"read error: {e}"))

    return {
        'zero_size': zero_size,
        'unreadable': unreadable,
    }

def main():
    """
    Command-line interface for scanning a folder for zero-byte and unreadable files.

    Parses command-line arguments to get the folder path and optional output report file path.
    Validates the folder, performs the scan, prints a summary and detailed report,
    and optionally writes the results to a specified text file.

    No input parameters; arguments are provided via the command line.

    Outputs:
        - Prints summary and detailed listing to stdout.
        - Optionally writes a report file if '--output' argument is supplied.
    Exits:
        - With code 1 if the specified folder is invalid.
    """
    parser = argparse.ArgumentParser(
        description="Scan a folder for zero-byte or unreadable files."
    )
    parser.add_argument(
        "folder",
        help="Path to your Sims 4 installation or mods folder"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Optional path to save the report (text file)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    report = scan_folder(args.folder)

    # Print summary
    print(f"\nScan complete for: {args.folder}\n")
    print(f"Zero-byte files    : {len(report['zero_size'])}")
    print(f"Unreadable files   : {len(report['unreadable'])}\n")

    # Detailed listing
    if report['zero_size']:
        print("=== Zero-byte files ===")
        for p in report['zero_size']:
            print(p)
        print()

    if report['unreadable']:
        print("=== Unreadable files (with error) ===")
        for p, err in report['unreadable']:
            print(f"{p}  -->  {err}")
        print()

    # Optionally save to file
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as out:
                out.write(f"Scan report for: {args.folder}\n\n")
                out.write(f"Zero-byte files ({len(report['zero_size'])}):\n")
                for p in report['zero_size']:
                    out.write(p + "\n")
                out.write(f"\nUnreadable files ({len(report['unreadable'])}):\n")
                for p, err in report['unreadable']:
                    out.write(f"{p} --> {err}\n")
            print(f"Report saved to {args.output}")
        except Exception as e:
            print(f"Failed to write report: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
