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
import java.util.ArrayList;
import java.util.List;

class MoveCommand {
	private List<PlainPoint> points = new ArrayList<PlainPoint>();
	private Float final_rotation = null;
	private boolean allowReversing = false;
	
	MoveCommand() {
		// empty command that just makes it stop
	}
	
	MoveCommand(DataInputStream input, byte cmd) throws IOException {
		short n = input.readShort();
		float x, y;
		
		for(int i = 0; i < n; ++i) {
			// the input is in thirds of a millimetres, here it is converted to full centimetres
			x = input.readShort() / 10.0f;
			y = input.readShort() / 10.0f;
			points.add(new PlainPoint(x, y));
		}
		
		if(cmd == 1 || cmd == 2)
			final_rotation = input.readFloat();
		
		if(cmd == 2 || cmd == 4)
			allowReversing = true;
	}
	
	List<PlainPoint> getRoute() {
		return points;
	}
	
	Float getFinalRotation() {
		return final_rotation;
	}
	
	boolean reversingAllowed() {
		return allowReversing;
	}
}