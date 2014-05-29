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

import common
import psycopg2, argparse, multiprocessing, signal, time, sys
from androguard.core.bytecodes import apk

def get_permissions(app_path):
  """Get the permissions of the app by androgruard"""

  a = apk.APK(app_path)
  p = a.get_permissions()
  p = list(set(p))

  return p


def do_work(config, data):
  # Add this line to make sure it is the parent process that
  # receives CTRL-C.
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  try:
    conn = common.initdb_from_file(config)
    cur = conn.cursor()

  except Exception as e:
    print e

  for app in data:
    with do_work.lock:
      do_work.progress.value += 1

    # Terminate if the parent process exit.
    if do_work.event.is_set():
      break

    a_name = app[0]
    a_path = app[1]

    try:
      sql = 'SELECT a_name FROM apps WHERE a_name = %s AND \
          a_perm_list IS NOT NULL'
      cur.execute(sql, (a_name,))
      if cur.fetchone():
        continue

      p_list = get_permissions(a_path)

      sql = 'UPDATE apps SET a_perm_list = %s WHERE a_name = %s'
      cur.execute(sql, (p_list, a_name))

    except Exception as e:
      print e
  
  conn.commit()

  cur.close()
  conn.close()


def do_work_init(v, l, e):
  do_work.progress = v
  do_work.lock = l
  do_work.event = e


def do_work_wrapper(args):
  do_work(*args)


def main():
  """
  Main

  """

  # Arguments
  parser = argparse.ArgumentParser(description='Get the permissions \
      of all the apps.')

  parser.add_argument('-c', metavar='DATABASE_CONFIG_FILE', type=str,
      nargs=1, required=True, help='the infomation needed for connection')
  parser.add_argument('-H', metavar='HOSTNAME', type=str,
      nargs=1, required=True, help='the host that the apps is located on')
  parser.add_argument('-t', metavar='N', type=int,
      nargs=1, default=[4], help='allow N jobs at once')

  args = parser.parse_args()

  try:
    conn = common.initdb_from_file(args.c[0])
    cur = conn.cursor()

    sql = 'SELECT a_name, a_path FROM apps WHERE a_host = %s'
    cur.execute(sql, (args.H[0],))

    data = []
    total_apps = 0
    while True:
      r = cur.fetchmany(50)
      if r == []:
        break

      data.append(r)
      total_apps += len(r)

  except Exception as e:
    print e

  finally:
    cur.close()
    conn.close()

  configs = [args.c[0] for x in data]
  
  event = multiprocessing.Event()
  progress = multiprocessing.Value('i', 0)
  lock = multiprocessing.Lock()

  pool = multiprocessing.Pool(args.t[0], do_work_init, \
      [progress, lock, event])
  args_for_pool = zip(configs, data)
  result = pool.map_async(do_work_wrapper, args_for_pool)

  try:
    while not result.ready():
      time.sleep(.5)
      print '%6.2f%% %d/%d\r' % (progress.value * 100.0 / total_apps, \
          progress.value, total_apps),
      sys.stdout.flush()
    print ''

    print 'Parent process reaches end!'

  except KeyboardInterrupt:
    print '\nParent process receives CTRL-C'

    # Notify the child processes to terminate.
    event.set()

    result.wait()


if __name__ == '__main__':
  main()

