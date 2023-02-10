#https://github.com/yutkin/Lenta.Ru-News-Dataset/releases/download/v1.1/lenta-ru-news.csv.bz2

import urllib.request
import bz2
import sys
import os
from urllib.parse import urlparse

def hook(blocks, block_size, total_size):
	current = blocks * block_size
	percent = 100.0 * current / total_size
	# Found this somewhere, don't remember where sorry
	line = '[{0}{1}]'.format('=' * int(percent / 2), ' ' * (50 - int(percent / 2)))
	status = '\r{0:3.0f}%{1} {2:3.1f}/{3:3.1f} MB'
	sys.stdout.write(status.format(percent, line, current/1024/1024, total_size/1024/1024))


url = 'https://github.com/yutkin/Lenta.Ru-News-Dataset/releases/download/v1.1/lenta-ru-news.csv.bz2'
a = urlparse(url)
filename = os.path.basename(a.path)
if not os.path.isfile(filename):
	filehandle, _ = urllib.request.urlretrieve(url, filename, reporthook=hook)

zipfile = bz2.BZ2File(filename) # open the file
data = zipfile.read() # get the decompressed data
newfilepath = filename[:-4] # assuming the filepath ends with .bz2
open(newfilepath, 'wb').write(data) # write a uncompressed file
