# SPDX-FileCopyrightText: 2021 mara004 <geisserml@gmail.com>
# SPDX-License-Identifier: MIT

VMAJOR = 0  # changes that break compatibility
VMINOR = 13  # new features that do not tamper with the API
VPATCH = 0  # bug fixes
VRC = None  # release candidates (optional)

VSTRING = str(VMAJOR) + '.'+str(VMINOR) + '.'+str(VPATCH)
if VRC is not None:
    VSTRING += '-rc.'+str(VRC)
