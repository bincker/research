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

import feature
import argparse, os, json
from multiprocessing import Pool

def extract(args):
  config_file = args[0]
  category = args[1]
  doc = args[2]
  path = args[3]

  conn = feature.init_from_file(config_file)
  cur = conn.cursor()

  if not os.path.exists(doc):
    return
  print category

  report = json.load(open(doc, 'r'))

  for apk in report.keys():

    apk_path = path + '/' + apk

    if report[apk] >= 2 or report[apk] < 0:
      continue

    feature.extract_apicall(cur, apk, apk_path, 0, category)
    conn.commit()

  cur.close()
  conn.close()

#--------------------------------------------------------------------
# Main
#--------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Extract the apicalls of \
    all the apps in the specified folder.')

parser.add_argument('-p', metavar='DATABASE_CONFIG_FILE', type=str,
    nargs=1, required=True, help='configuration of database')
parser.add_argument('-b', metavar='BATCH_JSON', type=str,
    nargs=1, required=True, help='details')

args = parser.parse_args()

batch = json.load(open(args.b[0], 'r'))

ps = []
pool = Pool(processes=4)

for category in batch:
  doc = batch[category][0]
  path = batch[category][1]

  ps.append([args.p[0], category, doc, path])

pool.map(extract, ps)
pool.close()
pool.join()
