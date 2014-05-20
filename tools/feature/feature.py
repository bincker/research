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

import psycopg2
import sys, json, re
from androguard.core.bytecodes import apk as androapk
from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis

def init(dbname, username, password=None, host=None):
  try:
    if host == None:
      sql = 'dbname=%s user=%s' % (dbname, username)

    else:
      sql = 'dbname=%s user=%s password=%s host=%s' % \
          (dbname, username, password, host)
    return psycopg2.connect(sql)

  except:
    print '[Error] Unable to connect to the database.'

def init_from_file(config_file):
  config = json.load(open(config_file, 'r'))

  dbname = config['dbname']
  user = config['user']

  if 'host' in config:
    return init(dbname, user, config['password'], config['host'])

  else:
    return init(dbname, user)

def close(conn):
  try:
    conn.close()

  except Exception as e:
    pass
    #print e

def extract_permission(cur, name, path, sus, category):
  try:
    # Check if the app has been analyzed.
    sql = 'SELECT apk_name FROM permissions WHERE apk_name = %s'
    cur.execute(sql, (name,))
    result = cur.fetchall()
    if len(result) > 0:
      #print '%s has been analyzed' % name
      return
    
    a = androapk.APK(path)
    p = a.get_permissions()
    p = list(set(p))
    sql = 'INSERT INTO permissions VALUES (nextval(%s), %s, %s, %s, %s);'
    data = ('permissions_apk_id_seq', name, sus, category,
        ' '.join(p))
    cur.execute(sql, data)

  except Exception as e:
    pass
    #print e

def extract_apicall(cur, name, path, sus, category):
  try:
    sql = 'SELECT apk_name FROM apicalls WHERE apk_name = %s'
    cur.execute(sql, (name,))
    result = cur.fetchall()
    if len(result) > 0:
      #print '%s has been analyzed' % name
      return

    a = androapk.APK(path)
    d = dvm.DalvikVMFormat(a.get_dex())
    x = analysis.VMAnalysis(d)

    s = set([])
    cs = [cc.get_name() for cc in d.get_classes()]
    
    for method in d.get_methods():
      g = x.get_method(method)

      if method.get_code() == None:
        continue

      for i in g.get_basic_blocks().get(): 
        for ins in i.get_instructions():
          output = ins.get_output()
          m = re.search('(L[^;]*;)->([a-zA-Z0-9_<>]+\()', output)
          if m and m.group(1) not in cs:
            s.add('%s %s' % (m.group(1), m.group(2)[:-1]))

    s = list(s)
    s.sort()

    sql = 'INSERT INTO apicalls VALUES (nextval(%s), %s, %s, %s, %s);'
    data = ('apicalls_apk_id_seq', name, sus, category, '\n'.join(s))
    cur.execute(sql, data)
  except Exception as e:
    print e
