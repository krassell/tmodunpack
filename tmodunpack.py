#!/bin/python3
# -*- coding: utf-8 -*-

# Tmod unpacker by krassell, 2020


import io
import sys
import zlib
import struct
import hashlib
import os.path
import argparse


settings = {
    'verbose': False,
    'png': False,
    'header': False,
}


def readTmodString(f):
    amt = int(f.read(1)[0])
    return f.read(amt)
    
    
def readUInt32(f):
    b = f.read(4)
    return struct.unpack('<I', b)[0]


def toByte(v):
    return struct.pack('<B', v&0xFF)


def toUInt32(v):
    return struct.pack('>I', v&0xFFFFFFFF)


def rawimg_to_png(fpath):
    assert(fpath[-7:]=='.rawimg')
    png_filename = fpath[:-7]+'.png'
    
    # avoid overwriting anything
    if os.path.isfile(png_filename) or os.path.isdir(png_filename):
        return

    width = 0
    height = 0
    img_data = io.BytesIO()
    
    with open(fpath,'rb') as rawfile:
        _version = readUInt32(rawfile)
        width = readUInt32(rawfile)
        height = readUInt32(rawfile)

        # Bottle-neck
        for i in range(height*width):
            rgba = rawfile.read(4)

            if i%width==0:
                img_data.write(b'\0')   # No filtering 
            img_data.write(rgba)

    with open(png_filename,'wb') as pngfile:
        output = b'\x89PNG\r\n\x1A\n'
        # make IHDR
        color_type = 6          # red, green, blue and alpha 
        bit_depth = 8
        compression_method = 0  # zlib
        filtertype = 0          # adaptive (each scanline seperately)
        interlaced = 0          # no

        IHDR = toUInt32(width) + toUInt32(height) + toByte(bit_depth)
        IHDR += toByte(color_type) + toByte(compression_method)
        IHDR += toByte(filtertype) + toByte(interlaced)

        IHDR_chunk = b'IHDR' + IHDR

        output += toUInt32(len(IHDR)) + IHDR_chunk + toUInt32(zlib.crc32(IHDR_chunk))

        # write IDAT with actual data

        zlib_obj = zlib.compressobj()
        compressed = zlib_obj.compress(img_data.getvalue())
        compressed += zlib_obj.flush()

        IDAT_chunk = b'IDAT'+compressed
        output += toUInt32(len(compressed)) + IDAT_chunk + toUInt32(zlib.crc32(IDAT_chunk))

        # write IEND
        IEND_chunk = b'IEND'
        output += b'\0'+IEND_chunk+toUInt32(zlib.crc32(IEND_chunk))

        pngfile.write(output)
        

def unpack_pre_0_11_0(f):
    fsha = f.read(20)
    print('Content SHA1  : '+fsha.hex())
    print('Signature     : '+f.read(256).hex())
    
    packsize = readUInt32(f)
    print('Pack size     : '+str(packsize))

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

    if settings['header']:
        print('=== Done! ===')
        return
    
    exdir = 'unpacked_'+os.path.basename(f.name)
    try:
        os.mkdir(exdir)
    except FileExistsError:
        pass
    
    for _ in range(fileamt):
        fpath = readTmodString(unpacked).decode('utf-8')
        fsize = readUInt32(unpacked)
        fdata = unpacked.read(fsize)
        
        if settings['verbose']:
            print('Extracting '+fpath)
        
        fxpath = os.path.join(exdir,fpath)
        os.makedirs(os.path.dirname(fxpath), exist_ok=True)
        with open(fxpath,'wb') as exfile:
            exfile.write(fdata)

        if settings['png'] and fxpath[-7:]=='.rawimg':
            rawimg_to_png(fxpath)
    print('=== Done! ===')


def unpack_post_0_11_0(f):
    fsha = f.read(20)
    print('Content SHA1  : '+fsha.hex())
    print('Signature     : '+f.read(256).hex())
    
    packsize = readUInt32(f)
    print('Pack size     : '+str(packsize))

    print('Mod name      : '+readTmodString(f).decode('utf-8'))
    print('Mod version   : '+readTmodString(f).decode('utf-8'))

    fileamt = readUInt32(f)
    print('Archive has '+str(fileamt)+' files.')

    if settings['header']:
        print('=== Done! ===')
        return
    
    exdir = 'unpacked_'+os.path.basename(f.name)
    try:
        os.mkdir(exdir)
    except FileExistsError:
        pass
    
    offset = 0
    file_entries = []
    for _ in range(fileamt):
        file_entry = {
            'path': readTmodString(f).decode('utf-8'),
            'offset': offset,
            'size': readUInt32(f),
            'size_compressed': readUInt32(f),
        }

        offset+=file_entry['size_compressed']
        file_entries.append(file_entry)

    base_offset = f.tell()
    
    for file_entry in file_entries:
        f.seek(base_offset+file_entry['offset'])
        fdata = f.read(file_entry['size_compressed'])

        if file_entry['size'] != file_entry['size_compressed']:
            fdata = zlib.decompress(fdata,-15)
        
        fpath = file_entry['path']

        if settings['verbose']:
            print('Extracting '+fpath)
        
        fxpath = os.path.join(exdir,fpath)
        os.makedirs(os.path.dirname(fxpath), exist_ok=True)
        with open(fxpath,'wb') as exfile:
            exfile.write(fdata)

        if settings['png'] and fxpath[-7:]=='.rawimg':
            rawimg_to_png(fxpath)
    
    print('=== Done! ===')


def dispatch_versioned_reader(f, version):
    # cutoff point is 0.11.0    
    if int(version.split('.')[1]) >= 11:
        unpack_post_0_11_0(f)
    else:
        unpack_pre_0_11_0(f)


def unpacktmod(filename):
    try:
        print('=== Processing '+filename+" ===")
        with open(filename, 'br') as f:
            magic = f.read(4)
            if magic != b'TMOD':
                print('Not a tmod file!')
                return
            
            tmod_version = readTmodString(f).decode('utf-8')
            print('TMOD Version  : '+tmod_version)

            dispatch_versioned_reader(f, tmod_version)

    except OSError as e:
        print("Couldn't process file "+filename)
        print(str(e))
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mass-unpack TMod files.')

    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='file to be processed')
    parser.add_argument('-v, --verbose', dest='verbose', action='store_const',
                        const=True, default=False,
                        help='Print which file is unpacking at the moment')
    parser.add_argument('-p, --png', dest='png', action='store_const',
                        const=True, default=False,
                        help='Create .png images for each encountered .rawimg file for ease of viewing')
    parser.add_argument('-H, --header', dest='header', action='store_const',
                        const=True, default=False,
                        help='Print header info only, do not unpack anything')
                                               

    args = parser.parse_args()
    settings.update(args.__dict__)
    for fn in args.files:
        unpacktmod(fn)
 
