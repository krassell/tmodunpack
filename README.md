# TMod Unpacker

## About

TMod Unpacker is small tool used to mass unpack tModLoader's TMod files.  
It also prints various additional info about TMod files it is extracting, including addon name, version and whether file's declared hash corresponds to actual hash of contents.

---
## Requirements

* Python 3

---
## Usage

You can process any number of files by specifying their names after script invocation string, i.e.  
**Windows**  
`python tmodunpack.py filename.tmod [optionalfilename2.tmod ...]`  
**\*nix**  
`python3 ./tmodunpack.py filename.tmod [optionalfilename2.tmod ...]`  

The resulting files will be neatly stored in directories named after tmod files, preceded by `unpacked_`, i.e. `unpacked_filename.tmod`.  

**Optional arguments:**  
`-h` / `--help` - Show usage info.
`-v` / `--verbose` - List unpacked files.  
`-p` / `--png` - Create .png image for every .rawimg file for easier content browsing.  
`-H` / `--header` - Print header info only, do not unpack anything.  

---
