#!/usr/bin/python
#
# Copyright (C) 2014  Che-Hsun Liu  <chehsunliu@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
#

import re

def parse_type(s):
  m = re.search(r'(\[*)(.*)', s)
  a = m.groups()[0]
  t = m.groups()[1]

  if t[0] == 'L':
    tc = t[1:-1]
  
  else:
    tc = {
        'V': 'void',
        'Z': 'boolean',
        'B': 'byte',
        'S': 'short',
        'C': 'char',
        'I': 'int',
        'J': 'long',
        'F': 'float',
        'D': 'double'
        } [t[0]]

  for i in range(len(a)):
    tc += '[]'
  return tc


def parse(s):
  s = s.replace('/', '.')
  m = re.search(r'(L[^;]*;)->([^\(]*)\(([^\)]*)\)(.*)', s)

  if m:
    result = \
        '<' + \
        parse_type(m.groups()[0]) + ': ' + \
        parse_type(m.groups()[3]) + ' ' + \
        m.groups()[1] + '('

    args = []
    for arg in m.groups()[2].split():
      args.append(parse_type(arg))
    result += ','.join(args)

    result += ')>'
    return result

  else:
    return None


def main():
  s1 = 'Landroid/support/v4/widget/DrawerLayout$SavedState$1;->newArray(I)[Landroid/support/v4/widget/DrawerLayout$SavedState;'
  s2 = 'v1, v2, Landroid/support/v4/view/ViewCompatKitKat;->setAccessibilityLiveRegion(Landroid/view/View; I)V'

  print parse(s1)
  print parse(s2)

if __name__ == '__main__':
  main()

