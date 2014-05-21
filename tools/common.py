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

def initdb(dbname, username, password=None, host=None):
  if host == None:
    sql = 'dbname=%s user=%s' % (dbname, username)

  else:
    sql = 'dbname=%s user=%s password=%s host=%s' % \
        (dbname, username, password, host)
  return psycopg2.connect(sql)

def initdb_from_file(config_file):
  config = json.load(open(config_file, 'r'))

  dbname = config['dbname']
  user = config['user']

  if 'host' in config:
    return initdb(dbname, user, config['password'], config['host'])

  else:
    return initdb(dbname, user)

