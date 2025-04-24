# Sims4Org: Zero-Byte and Corrupt File Scanner

## Overview

Sims4Org is a utility script for scanning Sims 4 folders to detect and report problematic files, such as zero-byte files or unreadable mod files.

## Features

- Recursive folder scanning
- Identifies:
  - Zero-byte files
  - Files that cannot be read or stat'ed
- Optional output report file

## Requirements

No external packages are required. Uses only built-in Python libraries.

## How to Run

```bash
python sims4org.py "/path/to/sims4/mods" --output report.txt
```

## Arguments

- `folder`: Required. The Sims 4 mods or installation directory to scan.
- `--output` / `-o`: Optional. File path to save a readable scan report.

## Example Output

```<<<<<<< SEARCH
>>>>>>> REPLACE


Scan complete for: C:/Users/Ethan/Documents/Electronic Arts/The Sims 4/Mods
Zero-byte files    : 3
Unreadable files   : 2

=== Zero-byte files ===
mod_1.package
mod_2.package
...

=== Unreadable files ===
mod_5.package  -->  read error: [Errno 13] Permission denied
...
```

## Use Cases

- Cleaning up broken or corrupt Sims 4 mods
- Generating mod integrity reports for troubleshooting

## License

MIT License
