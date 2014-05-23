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

import argparse, os, json

def main():
  """Main function"""

  # Arguments
  parser = argparse.ArgumentParser(description='Create all the symbolic \
      links of each category in a folder.')

  parser.add_argument('-b', metavar='BATCH_JSON', type=str,
      nargs=1, required=True, help='the docs and paths of apps')
  parser.add_argument('-o', metavar='OUTPUT_FOLDER', type=str,
      nargs=1, required=True, help='the output folder')

  args = parser.parse_args()

  output_folder = args.o[0]

  # Check if the output folder exists.
  if not os.path.isdir(output_folder):
    print '[Error] The specified folder does not exist.'
    return

  # Load the batch file.
  batch = json.load(open(args.b[0], 'r'))

  for category in batch:
    # Exclude malicious apps.
    if batch[category][2] == 1:
      continue

    # Check if the category has been analyzed.
    if not os.path.exists(batch[category][0]):
      continue

    report = json.load(open(batch[category][0], 'r'))

    for app in report:
      if report[app] >= 2 or report[app] < 0:
        continue

      target_path = batch[category][1] + '/' + app
      destination_path = output_folder + '/' + app

      if not os.path.exists(destination_path):
        os.symlink(target_path, destination_path)


if __name__ == '__main__':
  main()
