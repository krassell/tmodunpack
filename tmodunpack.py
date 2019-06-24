#!/bin/python3
# -*- coding: utf-8 -*-

# Tmod unpacker by krassell, 2018

import io
import sys
import zlib
import struct
import hashlib
import os.path


def readTmodString(f):
    amt = int(f.read(1)[0])
    return f.read(amt)
    
    
def readUInt32(f):
    b = f.read(4)
    return struct.unpack('<I', b)[0]


def unpacktmod(filename):
    try:
        print('=== Processing '+filename+" ===")
        with open(filename, 'br') as f:
            magic = f.read(4)
            if magic != b'TMOD':
                print('Not a tmod file!')
                return
            
            print('TMOD Version  : '+readTmodString(f).decode('utf-8'))
            fsha = f.read(20)
            print('Content SHA1  : '+fsha.hex())
            print('Signature     : '+f.read(256).hex())
            
            packsize = readUInt32(f)  # UNUSED!
            packed = f.read()
            psha = hashlib.sha1(packed).digest()
            if psha == fsha:
                print('[OK] PACK SHA1: '+psha.hex()+' - Matches the declared one')
            else:
                print('[!!] PACK SHA1: '+psha.hex())
                print('Declared SHA and packed files\' SHA do not match, package could have been tampered with!')
                print('Extracting anyway...')
            print('Unpacking...')
            unpacked = io.BytesIO(zlib.decompress(packed,-15))
            print('Done. Extracting files...')
            
            print('Name          : '+readTmodString(unpacked).decode('utf-8'))
            print('Version       : '+readTmodString(unpacked).decode('utf-8'))
            
            fileamt = readUInt32(unpacked)
            print('Archive has '+str(fileamt)+' files.')
            
            exdir = 'unpacked_'+os.path.basename(filename)
            try:
                os.mkdir(exdir)
            except FileExistsError:
                pass
            
            for i in range(fileamt):
                fpath = readTmodString(unpacked).decode('utf-8')
                fsize = readUInt32(unpacked)
                fdata = unpacked.read(fsize)
                print('Extracting '+fpath)
                
                fxpath = os.path.join(exdir,fpath)
                os.makedirs(os.path.dirname(fxpath), exist_ok=True)
                with open(fxpath,'wb') as exfile:
                    exfile.write(fdata)
                    
            print('=== Done! ===')

    except OSError as e:
        print("Couldn't process file "+filename)
        print(str(e))
        

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        unpacktmod(fn)
    if len(sys.argv[1:]) == 0:
        print('Usage: python3 ./tmodunpack.py filename1.tmod [filename2.tmod ...]')

