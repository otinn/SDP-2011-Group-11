/*
 * Copyright (C) 2011 SDP 2011 Group 11
 * This file is part of SDP 2011 Group 11's SDP solution.
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with This program.  If not, see <http://www.gnu.org/licenses/>.
 */

import java.io.DataInputStream;
import java.io.IOException;

class VisionXYData {
	final float x, y;
	final long frameTime;
	
	VisionXYData(DataInputStream input) throws IOException {
		// the input is in millimetres, here it is converted to full centimetres
		x = input.readShort() / 10.0f;
		y = input.readShort() / 10.0f;
		frameTime = input.readLong();
	}
	
	public String toString() {
		return "xy_msg(" + x + ", " + y + ": " + frameTime + ")";
	}
}