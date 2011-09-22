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

public class Location {
	public boolean sharpTurn = false;
	public float x, y, rotation;
	public long time;
	
	Location() {
		time = System.currentTimeMillis();
	}
	
	Location(float x, float y, float rotation, long time) {
		this.x = x;
		this.y = y;
		this.rotation = rotation;
		this.time = time;
	}
	
	void update(float x, float y, float rotation, long time, boolean sharpTurn) {
		this.x = x;
		this.y = y;
		this.rotation = rotation;
		this.time = time;
		this.sharpTurn = sharpTurn;
	}
	
	public String toString() {
		return "loc(" + x + ", " + y + ", " + rotation + ": " + time + ")";
	}
}