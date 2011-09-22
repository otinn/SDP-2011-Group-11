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
import java.util.ArrayList;
import java.util.List;

class MoveCommand {
	public final List<short[]> points;
	public final Float rotation;
	public final boolean allow_reverse;
	
	private static short convertCoordinate(float f, int limit) {
		return (short) Math.min(Math.max(0, Math.round(10 * f)), limit * 10 - 1);
	}
	
	MoveCommand(String cmd, boolean allow_reverse) throws IOException {
		String parts[] = cmd.split("\\s+");
		points = new ArrayList<short[]>();
		int n = Integer.parseInt(parts[0]);
		if(2 * n + 2 != parts.length)
			throw new IOException("wrong /planner/move parameter count");
		
		for(int i = 0; i < n; ++i) {
			float x = Float.parseFloat(parts[2 * i + 1]);
			float y = Float.parseFloat(parts[2 * i + 2]);
			points.add(new short[]{convertCoordinate(x, 244), convertCoordinate(y, 122)});
		}
		if(!parts[2 * n + 1].equals("not_important")) {
			rotation = Float.parseFloat(parts[2 * n + 1]);
		} else
			rotation = null;
		this.allow_reverse = allow_reverse;
	}
	
	public void write(DataOutputStream output) throws IOException {
		output.writeByte((rotation == null? 3: 1) + (allow_reverse? 1: 0));
		output.writeShort(points.size());
		for(int i = 0; i < points.size(); ++i) {
			output.writeShort(points.get(i)[0]);
			output.writeShort(points.get(i)[1]);
		}
		if(rotation != null)
			output.writeFloat(rotation);
	}
}