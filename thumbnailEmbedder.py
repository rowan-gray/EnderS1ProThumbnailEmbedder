#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# Contains code from the jpg re-encoder thumbnail post processor script:
# github.com/alexqzd/Marlin/blob/Gcode-preview/Display%20firmware/gcode_thumb_to_jpg.py
# ------------------------------------------------------------------------------

import sys
import re
import os
import base64 
import io
import subprocess

from PyQt6.QtCore import QBuffer

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip3", "install", package])

try:
    from PIL import Image, ImageOps
except ImportError:
    install("Pillow")
    from PIL import Image

def main():
    # Get the g-code source file name
    source_file = sys.argv[1]

    lines = None
    # Read the ENTIRE g-code file into memory
    with open(source_file, "r") as f:
        lines = f.read()

    if (lines is None):
        print("Failed to read in file.")

    jpg, lines = extractJPG(lines)
    time = extractEstimatedPrintingTime(lines)
    filament = extractFilamentUsed(lines)
    layer_height = getLayerHeight()
    dimensions, lines = extractDimensions(lines)

    temp_file = source_file + ".tmp"
    with open(temp_file, "w") as output_file:
        writeToFile(output_file, jpg, time, filament, layer_height, dimensions, lines)
    
    os.remove(source_file)
    os.rename(temp_file, source_file)

def extractJPG(lines):
    thumb_expresion = '; thumbnail_JPG begin.*?\n((.|\n)*?); thumbnail_JPG end'
    size_expresion = '; thumbnail_JPG begin [0-9]+x[0-9]+ [0-9]+'
    tail_expresion = '; thumbnail_JPG end'

    thumb_iter = re.finditer(thumb_expresion, lines)
    size_iter = re.finditer(size_expresion, lines)
    tail_iter = re.finditer(tail_expresion, lines)

    thumb_match = next(thumb_iter, None)
    size_match = next(size_iter, None)
    tail_match = next(tail_iter, None)

    if (thumb_match == None or size_match == None or tail_match == None):
        return

    firstIndex = size_match.start()
    lastIndex = tail_match.end()

    original = thumb_match.group(1)

    # gets rid of comments and newlines to get the pure JPG data.
    encoded = original.replace("; ", "")
    encoded = encoded.replace("\n", "")
    encoded = encoded.replace("\r", "")

    # converts to an pip image
    decoded = base64.b64decode(encoded)
    img_png = Image.open(io.BytesIO(decoded))
    img_png_rgb = img_png.convert('RGB')

    # removes from lines
    lines= lines[:firstIndex] + lines[lastIndex:]
    
    return img_png_rgb, lines
    
def extractDimensions(lines):
    dimensionsRegex = ";MINX:{0};MINY:{0};MINZ:{0};MAXX:{0};MAXY:{0};MAXZ:{0}".format("((\d|.)+\s*)")

    dimensions_iter = re.finditer(dimensionsRegex, lines)
    dimensions_match = next(dimensions_iter, None)

    if (dimensions_match == None):
        print("Failed to find dimensions.")
        return "", lines
    
    firstIndex = dimensions_match.start()
    lastIndex = dimensions_match.end()

    dimensions = dimensions_match.group(0)

    lines= lines[:firstIndex] + lines[lastIndex:]

    return dimensions, lines

def writeJPG(jpg, out_file, name):
    thumbnail_buffer = QBuffer()
    thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    jpg.save(thumbnail_buffer, "jpeg", quality=40, optimize=True)
    thumbnail_data = thumbnail_buffer.data()
    thumbnail_length = thumbnail_data.length()
    base64_bytes = base64.b64encode(thumbnail_data)
    base64_message = base64_bytes.decode('ascii')
    thumbnail_buffer.close()

    encodedjpg_gcode = encodedJPGToGcodeComment(base64_message)

    width = 300
    height = 300

    x1 = (int)(width/80) + 1
    x2 = width - x1
    header = "; {} begin {}*{} {} {} {} {}".format(name, width, height, thumbnail_length, x1, x2, 500)

    tail = '; {} end'.format(name)

    print("\n".join([header,encodedjpg_gcode,tail]), file=out_file)

def encodedJPGToGcodeComment(encodedString):
    n = 76 # number of encoded JPG characters per line
    return '; ' + '\n; '.join(encodedString[i:i+n] for i in range(0, len(encodedString), n))

def extractEstimatedPrintingTime(lines):
    time = 0
    match = re.search('; estimated printing time \(normal mode\) = (.*)\n', lines)
    if match is not None :
        h = re.search('(\d+)h',match[1])
        h = int(h[1]) if h is not None else 0
        m = re.search('(\d+)m',match[1])
        m = int(m[1]) if m is not None else 0
        s = re.search('(\d+)s',match[1])
        s = int(s[1]) if s is not None else 0
        time = h*3600+m*60+s

        return time

def extractFilamentUsed(lines):
    match = re.search('; filament used \[mm\] = ([0-9.]+)', lines)
    return float(match[1])/1000 if match is not None else 0

def getLayerHeight():
    match = os.getenv('SLIC3R_LAYER_HEIGHT')
    return float(match) if match is not None else 0

def writeToFile(out_file, jpg, time, filament, layer, dimensions, lines):
    try:
        # write it with jpg for printer
        writeJPG(jpg, out_file, "jpg")
        
        print("", file=out_file) # new line

        print(";FLAVOR:Marlin", file=out_file)
        print(";TIME:{:d}".format(time), file=out_file)
        print(";Filament used:{:.6f}m".format(filament), file=out_file)

        #print filler data
        print(";Material Diameter:1.75\n;Material Density:1.24\n;Filament Cost:0.000000\n;Filament Weight:49.942665\n;Filament Length:16.744957", file=out_file)
        
        print(";Layer height:{:.2f}".format(layer), file=out_file)
        print(dimensions, file=out_file)

        print("", file=out_file) # new line

        writeJPG(jpg, out_file, "thumbnail")

        lines = lines.replace("; \n", "")
        lines = lines.replace(";\n", "")

        out_file.write(lines)
    except:
        print('Error writing output file')
        exit(1)

if __name__=="__main__":

    main()