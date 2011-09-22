# ###################################################
# Copyright (C) 2011 SDP 2011 Group 11
# This file is part of SDP 2011 Group 11's SDP solution.
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
# along with This program.  If not, see <http://www.gnu.org/licenses/>.
# ###################################################

import os
import sys
sys.path.append("src/sdp/vision/")
import vision
import calibrate

# Set tolerance level, ptol for position, rtol for rotation

ptol = 10
rtol = 0.5

# Set counters for performance

totalfiles = 0
successful = 0
failure = 0

# Instance calibration

c = calibrate.Calibrate((9,6))
c.calibrate_camera_from_mem("src/sdp/vision/calibration_data/")

# Cycle through valid folders and files

for folder in sorted(os.listdir("fixtures"))[1:-1]:
	folderpath = "fixtures/" + folder + "/"
	# Instance vision with empty background (should be only filename starting with e)
	def f(x):
		return x[0] == "e"
	v = vision.Vision(vision.cv.LoadImage(folderpath + filter(f, os.listdir(folderpath))[0]), c, fix_distortions=False)
	for file in os.listdir(folderpath)[1:]:
		# Open file if it is XML
		if file[-3:] == "xml":
			totalfiles = totalfiles + 1
			xml = open(folderpath + file, 'r')
			# Fetch values from file, use trys for rotation as we don't have them yet
			for line in xml:
				# Image path
				if(line[0:2] == "<f"):
					imagepath = folderpath + line.split("\"")[1]
				# Ball
				if(line[0:7] == "    <ba"):
					xml_ball = line.split("\"")
					xml_ballx = int(xml_ball[1])
					xml_bally = int(xml_ball[3])
					xml_ballr = int(xml_ball[5])
				# Yellow robot
				if(line[0:6] == "    <y"):
					xml_yellow = line.split("\"")
					xml_yellowx = int(xml_yellow[1])
					xml_yellowy = int(xml_yellow[3])
					try:
						xml_yellowr = int(xml_yellow[5])
					except ValueError:
						xml_yellowr = -1
				# Blue robot
				if(line[0:7] == "    <br"):
					xml_blue = line.split("\"")
					xml_bluex = int(xml_blue[1])
					xml_bluey = int(xml_blue[3])
					try:
						xml_bluer = int(xml_blue[5])
					except ValueError:
						xml_bluer = -1
			xml.close()
			# Pass imagepath into vision and return results
			v.update(vision.cv.LoadImage(imagepath))
			ball = v.get_ball()
			if(ball != None):
				((vision_ballx, vision_bally), _) = ball
			else:
				vision_ballx = -1
				vision_bally = -1
			# At the moment we don't care about ball radius
			vision_ballr = -1
			yellowbot = v.get_robot('yellow')
			if(yellowbot != (None, None)):
				((vision_yellowx, vision_yellowy), vision_yellowr) = yellowbot
			else:
				vision_yellowx = -1
				vision_yellowy = -1
				vision_yellowr = -1
			bluebot = v.get_robot('blue')
			if(bluebot != (None, None)):
				((vision_bluex, vision_bluey), vision_bluer) = bluebot
			else:
				vision_bluex = -1
				vision_bluey = -1
				vision_bluer = -1
			# Compare values, print errors to console
			failflag = 0
			if(xml_ballx - ptol > vision_ballx or xml_ballx + ptol < vision_ballx):
				failflag = 1
				print("| ERROR ballx: | Vision: " + str(vision_ballx).zfill(13) + " | XML: " + str(xml_ballx).zfill(3) + " | File: " + imagepath + " |")
			if(xml_bally - ptol > vision_bally or xml_bally + ptol < vision_bally):
				failflag = 1
				print("| ERROR bally: | Vision: " + str(vision_bally).zfill(13) + " | XML: " + str(xml_bally).zfill(3) + " | File: " + imagepath + " |")
			if(xml_ballr - ptol > vision_ballr or xml_ballr + ptol < vision_ballr):
				failflag = 1
				print("| ERROR ballr: | Vision: " + str(vision_ballr).zfill(13) + " | XML: " + str(xml_ballr).zfill(3) + " | File: " + imagepath + " |")
			if(xml_yellowx - ptol > vision_yellowx or xml_yellowx + ptol < vision_yellowx):
				failflag = 1
				print("| ERROR yellx: | Vision: " + str(vision_yellowx).zfill(13) + " | XML: " + str(xml_yellowx).zfill(3) + " | File: " + imagepath + " |")
			if(xml_yellowy - ptol > vision_yellowy or xml_yellowy + ptol < vision_yellowy):
				failflag = 1
				print("| ERROR yelly: | Vision: " + str(vision_yellowy).zfill(13) + " | XML: " + str(xml_yellowy).zfill(3) + " | File: " + imagepath + " |")
			if(xml_yellowr - ptol > vision_yellowr or xml_yellowr + ptol < vision_yellowr):
				failflag = 1
				print("| ERROR yellr: | Vision: " + str(vision_yellowr).zfill(13) + " | XML: " + str(xml_yellowr).zfill(3) + " | File: " + imagepath + " |")
			if(xml_bluex - ptol > vision_bluex or xml_bluex + ptol < vision_bluex):
				failflag = 0
				print("| ERROR bluex: | Vision: " + str(vision_bluex).zfill(13) + " | XML: " + str(xml_bluex).zfill(3) + " | File: " + imagepath + " |")
			if(xml_bluey - ptol > vision_bluey or xml_bluey + ptol < vision_bluey):
				failflag = 1
				print("| ERROR bluey: | Vision: " + str(vision_bluey).zfill(13) + " | XML: " + str(xml_bluey).zfill(3) + " | File: " + imagepath + " |")
			if(xml_bluer - ptol > vision_bluer or xml_bluer + ptol < vision_bluer):
				failflag = 0
				print("| ERROR bluer: | Vision: " + str(vision_bluer).zfill(13) + " | XML: " + str(xml_bluer).zfill(3) + " | File: " + imagepath + " |")
			# Increment relevant counter
			if(failflag == 1):
				failure = failure + 1
			else:
				successful = successful + 1
# Print results!
print("\n| RESULT | Total: " + str(totalfiles) + " | Successful: " + str(successful) + " | Failed: " + str(failure)) + " |"
