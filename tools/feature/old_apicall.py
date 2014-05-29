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

import psycopg2, multiprocessing, signal
import itertools, argparse, os, json, re, zipfile, time, sys
import common
from androguard.core.bytecodes import apk 
from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis

def get_apicalls(app_path):
  """Get the API calls by androguard."""

  a = apk.APK(app_path)
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

  l = list(s)
  l.sort()
  
  return '\n'.join(l)


def do_work(config, table, work, sus, category, doc, path):
  """Assign the work to each child process."""

  # Add this line to make sure it is the parent process that
  # receives CTRL-C.
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  # Establish the connection to the database.
  try:
    conn = common.initdb_from_file(config)
    cur = conn.cursor()

  except psycopg2.OperationalError as e:
    print '[Error] %s - ' % category, e

  # Check if the apps under this category is scanned by VirusTotal.
  if not os.path.exists(doc):
    return
  report = json.load(open(doc, 'r'))
  total = len(report.keys())
  count = 0

  # Start API call extraction.
  print category
  for app_name in report.keys():
    count += 1
    print '%s (%d/%d): %s' % (category, count, total, app_name)

    # Terminate if the parent process exit.
    if do_work.event.is_set():
      break

    # Absolute path of the application
    app_path = path + '/' + app_name

    # Threshold set to 2.
    if report[app_name] >= 2 or report[app_name] < 0:
      continue

    # Checl if the apps has been analyzed.
    sql = 'SELECT apk_name FROM ' + table + ' WHERE apk_name = %s'
    cur.execute(sql, (app_name,))
    result = cur.fetchall()
    if len(result) > 0:
      continue

    # Analyze the application.
    try:
      l = work(app_path)

      sql = 'INSERT INTO ' + table + \
          ' VALUES (nextval(%s), %s, %s, %s, %s);'
      data = ('%s_apk_id_seq' % table, app_name, sus, category, l)
      cur.execute(sql, data)
      conn.commit()

    except zipfile.BadZipfile:
      #print 'Broken zip'
      continue

    except UnicodeEncodeError:
      print 'Unicode error'
      continue

    except psycopg2.Warning:
      print 'PSY_WARNING'
      continue
    
    except psycopg2.Error:
      print 'PSY_ERROR'
      continue

    except:
      continue

  # Close the database connection.
  print 'Terminating \t%s' % category
  try:
    cur.close()
    conn.close()

  except: 
    print 'no....'
    raise


def do_work_init(e):
  do_work.event = e;


def do_work_wrapper(args):
  """Wrap the function do_work to support multiple arguments."""

  return do_work(*args)


def main():
  """Main function"""

  # Arguments
  parser = argparse.ArgumentParser(description='Extract the apicalls of \
      all the apps specified.')

  parser.add_argument('-c', metavar='DATABASE_CONFIG', type=str,
      nargs=1, required=True, help='configuration of database')
  parser.add_argument('-b', metavar='BATCH_JSON', type=str,
      nargs=1, required=True, help='the docs and paths of apps')
  parser.add_argument('-t', metavar='N', type=int,
      nargs=1, default=[4], help='allow N jobs at once')

  args = parser.parse_args()

  # Load the batch file.
  batch = json.load(open(args.b[0], 'r'))

  configs = [args.c[0] for c in batch]
  tables = ['apicalls' for c in batch]
  works = [get_apicalls for c in batch]
  suss = [0 for c in batch]
  docs = [batch[c][0] for c in batch]
  paths = [batch[c][1] for c in batch]

  # Multiprocessing
  event = multiprocessing.Event()
  pool = multiprocessing.Pool(args.t[0], do_work_init, [event])
  args_for_pool = zip(
      configs, tables, works, suss, batch.keys(), docs, paths)
  result = pool.map_async(do_work_wrapper, args_for_pool)

  # Wait for the child processes.
  try:
    while not result.ready():
    #while True:
      time.sleep(5)

    print 'Parent process reaches end!'

  except KeyboardInterrupt:
    print '\nParent process receives CTRL-C'

    # Notify the child processes to terminate.
    event.set()

    result.wait()


if __name__ == '__main__':
  main()
