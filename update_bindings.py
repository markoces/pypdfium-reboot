#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2021 mara004 <geisserml@gmail.com>
# SPDX-License-Identifier: MIT

import tarfile
import zipfile
import subprocess
import os
import glob
import shutil
import fileinput
from urllib import request

# TODO clean up /dist, /build and /pypdfium_reboot.egg-info

# determine current directory for relative paths
thisdirectory = os.path.dirname(os.path.realpath(__file__)) + '/'

## make sure we have the latest ctypesgen
#subprocess.run("python3 -m pip install -U ctypesgen", shell=True)

# extract the latest tag needed to determine the URL
latest_tag = subprocess.run(["git ls-remote https://github.com/bblanchon/pdfium-binaries.git |grep -ohP 'chromium/\d+' |tail -n1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
latest_tag = latest_tag.stdout.decode('UTF-8')[:-1].split('/')[1]
print(latest_tag)

# automatically increment pypdfium version if it's a new chromium build

with open(thisdirectory+'pypdfium/pdfium_version.txt', 'r') as f:
    previous_cversion = f.read().split('/')[1]

if int(latest_tag) > int(previous_cversion):
    versionupdate = True
    print("new pdfium build version - incrementing pypdfium version")
    with fileinput.FileInput(thisdirectory+'pypdfium/version.py', inplace=True) as f:
        for line in f:
            # TODO set VPATCH back to 0
            searchexp = 'VMINOR = '  # use minor version by default
            if searchexp in line:
                # fetch previous version
                version = line[line.index(searchexp)+len(searchexp):line.index('  #')]
                # replace with new version
                print(line.replace(searchexp+version, searchexp+str(int(version)+1)), end='')
            else:
                # take the line as-is
                print(line, end='')
else:
    versionupdate = False
    print("same pdfium build version - will re-create bindings nevertheless")

# update chromium/pdfium version file
with open(thisdirectory+'pypdfium/pdfium_version.txt', 'w') as f:
    f.write('chromium/'+latest_tag)

# craft release url
base_url = "https://github.com/bblanchon/pdfium-binaries/releases/download/chromium%2F" + latest_tag + '/'
print(base_url)

# files to download
filenames = {
    'linux'  : 'pdfium-linux.tgz',
    'darwin' : 'pdfium-darwin-x64.tgz',
    'win32'  : 'pdfium-windows-x64.zip',
}

# initialise dict to fill in the paths of the downloaded files
files = dict()

# download tarballs & zipfile and update the paths dictionary
for platform, file in filenames.items():
    download_url = base_url + file
    target_path = thisdirectory+file
    print(download_url, target_path)
    request.urlretrieve(download_url, target_path)
    files.update({platform : target_path})

print(files)


# functions to extract single files without their parent directories

def tar_flatextract(member):
    for info in archive.getmembers():
        if info.name.endswith(member):
            if info.name[-1] == '/':
                continue
            info.name = os.path.basename(info.name)
            archive.extract(info, './pypdfium')

def zip_flatextract(member):
    for info in archive.infolist():
        if info.filename.endswith(member):
            if info.filename[-1] == '/':
                continue
            info.filename = os.path.basename(info.filename)
            archive.extract(info, './pypdfium')


# extract the archives

for platform, file in files.items():
    
    # open the archive
    if file.endswith('.tgz'):
        archive = tarfile.open(file, 'r')
    elif file.endswith('.zip'):
        archive = zipfile.ZipFile(file, 'r')
    
    # Linux binary extraction
    # special because we will be using the Linux archive for ctypesgen
    if platform == 'linux':
        archive.extractall('./linux_tar')
        os.rename(f"{thisdirectory}linux_tar/lib/libpdfium.so", f"{thisdirectory}linux_tar/lib/pdfium")
        shutil.copyfile('./linux_tar/lib/pdfium', './pypdfium/pdfium')
    
    # macOS and Windows binary extraction
    elif platform == 'darwin':
        tar_flatextract('lib/libpdfium.dylib')
        os.rename(f'{thisdirectory}pypdfium/libpdfium.dylib', f'{thisdirectory}pypdfium/pdfium.dylib')
    elif platform == 'win32':
        zip_flatextract('x64/bin/pdfium.dll')
    
    # close the archive and delete it
    archive.close()
    os.remove(file)


# finally, call ctypesgen
ctypesgen_command = f"ctypesgen --library=pdfium -L {thisdirectory}linux_tar/lib {thisdirectory}linux_tar/include/*.h -o pypdfium/pypdfium.py"
print(ctypesgen_command)
subprocess.run([ctypesgen_command], shell=True)


# delete the extracted Linux pdfium binary + headers
shutil.rmtree(thisdirectory+'linux_tar/')

# add and commit to git
#subprocess.run([f'git add {thisdirectory}pypdfium/*'], shell=True)
#subprocess.run([f'git commit -m "[AUTOCOMMIT] run update_bindings.py - version update {str(versionupdate).lower()}"'], shell=True)

# build the wheel
wheel_command = 'python3 setup.py bdist_wheel'
print(wheel_command)
subprocess.run([wheel_command], shell=True)

"""
# install wheel locally

# get all files in the dist/ directory
builddir_files = glob.glob(f'{thisdirectory}dist/*')

# take the latest one
wheel = max(builddir_files, key=os.path.getctime)
print(wheel)

# craft install command
install_command = 'python3 -m pip install -U ' + wheel
print(install_command)

# run it
subprocess.run(install_command, shell=True)
"""
