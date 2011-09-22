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

class VisionRotationData {
	final float rotation;
	final long frameTime;
	
	private static final float normalizeRotation(float f) {
		while(f < 0)
			f -= 2 * Math.PI;
		while(f > 2 * Math.PI)
			f -= 2 * Math.PI;
		return Math.max(0.0f, f);
	}
	
	VisionRotationData(float rotation, String frameTime) throws ParseException {
		this.rotation = normalizeRotation(rotation);
		this.frameTime = Synchronizer.getBrickTime(frameTime);
	}
	
	public void write(DataOutputStream output) throws IOException {
		output.writeByte(16);
		output.writeFloat(rotation);
		output.writeLong(frameTime);
	}
}