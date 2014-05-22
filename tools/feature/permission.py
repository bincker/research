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
import common, apicall
from androguard.core.bytecodes import apk

def get_permissions(app_path):
  """Get the permissions of the app by androgruard"""

  a = apk.APK(app_path)
  p = a.get_permissions()
  p = list(set(p))
  p.sort()

  return '\n'.join(p)

def main():
  """Main function"""

  # Arguments
  parser = argparse.ArgumentParser(description='Extract the permissions of \
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
  tables = ['permissions' for c in batch]
  works = [get_permissions for c in batch]
  suss = [0 for c in batch]
  docs = [batch[c][0] for c in batch]
  paths = [batch[c][1] for c in batch]

  # Multiprocessing
  event = multiprocessing.Event()
  pool = multiprocessing.Pool(args.t[0], apicall.do_work_init, [event])
  args_for_pool = zip(
      configs, tables, works, suss, batch.keys(), docs, paths)
  result = pool.map_async(apicall.do_work_wrapper, args_for_pool)

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
