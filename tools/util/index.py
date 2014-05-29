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

import argparse, json, psycopg2, os
import common

def index(conn, doc, folder, category, host):
  """
  Index all the apps into the database.

  """
  
  cur = conn.cursor()
  report = json.load(open(doc, 'r'))

  total = len(report.keys())
  count = 0

  for app in report:
    count += 1
    print '(%3d/%3d) %s' % (count, total, app)

    # Check if the app is too large.
    if report[app] < 0:
      continue

    is_sus = report[app] >= 2
    path = folder + '/' + app

    try:
      sql = 'SELECT a_category FROM apps WHERE a_name = %s'
      cur.execute(sql, (app,))
      result = cur.fetchone()

      if result != None:
        c_list = result[0]

        if category not in c_list:
          c_list.append(category)
          c_list.sort()
          
          sql = 'UPDATE apps SET a_category = %s WHERE a_name = %s'
          cur.execute(sql, (c_list, app))

      else:
        sql = 'INSERT INTO apps (a_name, a_is_sus, a_category, a_host, \
            a_path) VALUES (%s, %s, %s, %s, %s)'
        
        cur.execute(sql, (app, is_sus, [category], host, path))

    except psycopg2.Error as e:
      print e.__class__, '\n', e, '\n', e.pgcode

  conn.commit()
  cur.close()
  

def main():
  """
  Index all the apps into the database.

  """

  # Arguments
  parser = argparse.ArgumentParser(description='Index all the apps into \
      the database.')

  parser.add_argument('-c', metavar='DATABASE_CONFIG_FILE', type=str,
      nargs=1, required=True, help='the infomation needed for connection')
  parser.add_argument('-b', metavar='BATCH_JSON', type=str,
      nargs=1, required=True, help='the docs and paths of apps')
  parser.add_argument('-H', metavar='HOST', type=str,
      nargs=1, required=True, help='the host that the apps is located on')

  args = parser.parse_args()

  # Create the table.
  try:
    conn = common.initdb_from_file(args.c[0])
    cur = conn.cursor()

    sql = 'CREATE TABLE IF NOT EXISTS apps ( \
        a_id SERIAL PRIMARY KEY, \
        a_name VARCHAR (128) UNIQUE NOT NULL, \
        a_is_sus BOOL, \
        a_category VARCHAR (32) [], \
        a_host VARCHAR (32), \
        a_path VARCHAR, \
        a_perm_list VARCHAR [], \
        a_api_list VARCHAR [])'
    cur.execute(sql)
    conn.commit()

  except psycopg2.Error as e:
    print e.__class__
    print e
    print e.pgcode

  finally:
    cur.close()

  batch = json.load(open(args.b[0], 'r'))

  for category in batch:
    doc = batch[category][0]
    folder = batch[category][1]

    if os.path.exists(doc):
      index(conn, doc, folder, category, args.H[0])

  conn.close()
  

if __name__ == '__main__':
  main()

