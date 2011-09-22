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

import java.io.DataOutputStream;
import java.io.IOException;
import java.text.ParseException;

class VisionXYData {
	final short x, y;
	final long frameTime;
	
	private static short convertCoordinate(float f, int limit) {
		return (short) Math.min(Math.max(0, Math.round(10 * f)), limit * 10 - 1);
	}
	
	VisionXYData(float x, float y, String frameTime) throws ParseException {
		this.x = convertCoordinate(x, 244);
		this.y = convertCoordinate(y, 122);
		this.frameTime = Synchronizer.getBrickTime(frameTime);
	}
	
	public void write(DataOutputStream output) throws IOException {
		output.writeByte(15);
		output.writeShort(x);
		output.writeShort(y);
		output.writeLong(frameTime);
	}
}