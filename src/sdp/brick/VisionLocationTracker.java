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

class BoundedLocationList {
	private final static int MAX_SIZE = 300;
	private final Location[] elements = new Location[MAX_SIZE];
	private int begin = 0, next = 1, len = 1;
	private Location t;
	
	BoundedLocationList(Location l) {
		for(int i = 0; i < MAX_SIZE; ++i)
			elements[i] = new Location(l.x, l.y, l.rotation, l.time);
	}
	
	void add(Location l) {
		elements[next].update(l.x, l.y, l.rotation, l.time, l.sharpTurn);
		++next;
		if(next == MAX_SIZE)
			next = 0;
		if(len == MAX_SIZE) {
			++begin;
			if(begin == MAX_SIZE)
				begin = 0;
		} else
			++len;
	}
	
	int size() {
		return len;
	}
	
	Location get(int pos) {
		pos += begin;
		if(pos >= MAX_SIZE)
			pos -= MAX_SIZE;
		return elements[pos];
	}
	
	void update(Location state) {
		int loc = next - 1;
		if(loc == -1)
			loc = MAX_SIZE - 1;
		t = elements[loc];
		state.update(t.x, t.y, t.rotation, t.time, t.sharpTurn);
	}
	
	/**
	 * @return last position before the time
	 */
	int getPos(long time) {
		int pos = next - 1;
		if(pos == -1)
			pos = MAX_SIZE - 1;
		int lpos = len - 1;
		while(lpos > 0 && elements[pos].time >= time) {
			--pos;
			if(pos == -1)
				pos = MAX_SIZE - 1;
			--lpos;
		}
		return lpos;
	}
}

public class VisionLocationTracker {
	private BoundedLocationList history = null;
	private VisionXYData xy_msg = null;
	private VisionRotationData rotation_msg = null;
	private long lastUpdated = 0;
	
	VisionLocationTracker(Location state) {
		history = new BoundedLocationList(state);
	}
	
	protected void updateXY() {
		final int pos = history.getPos(xy_msg.frameTime);
		final float dx, dy;
		if(pos + 1 == history.size()) {
			dx = xy_msg.x - history.get(pos).x;
			dy = xy_msg.y - history.get(pos).y;
		} else {
			final int dtime = Math.max(1, (int) (history.get(pos + 1).time - history.get(pos).time));
			final int rtime = Math.max(1, (int) (xy_msg.frameTime - history.get(pos).time));
			final float ratio = rtime / (float) dtime;
			dx = xy_msg.x - (history.get(pos).x + (history.get(pos + 1).x - history.get(pos).x) * ratio);
			dy = xy_msg.y - (history.get(pos).y + (history.get(pos + 1).y - history.get(pos).y) * ratio);
		}
		
		if(pos + 1 == history.size()) {
			history.get(pos).x = xy_msg.x;
			history.get(pos).y = xy_msg.y;
		} else {
			for(int i = pos + 1; i < history.size(); ++i) {
				history.get(i).x += dx;
				history.get(i).y += dy;
			}
		}
	}
	
	protected void updateRotation() {
		final int pos = history.getPos(rotation_msg.frameTime);
		final float posx, posy, diff;
		if(pos + 1 == history.size()) {
			posx = history.get(pos).x;
			posy = history.get(pos).y;
			diff = rotation_msg.rotation - history.get(pos).rotation;
		} else {
			final int dtime = Math.max(1, (int) (history.get(pos + 1).time - history.get(pos).time));
			final int rtime = Math.max(1, (int) (rotation_msg.frameTime - history.get(pos).time));
			final float ratio = rtime / (float) dtime;
			posx = history.get(pos).x + (history.get(pos + 1).x - history.get(pos).x) * ratio;
			posy = history.get(pos).y + (history.get(pos + 1).y - history.get(pos).y) * ratio;
			final float rot1 = history.get(pos + 1).rotation - history.get(pos).rotation;
			final float rot2 = (float) (rot1 < 0? rot1 + 2 * Math.PI: rot1 - 2 * Math.PI);
			final float rot = history.get(pos).rotation + (Math.abs(rot1) < Math.abs(rot2)? rot1: rot2) * ratio;
			diff = rotation_msg.rotation - rot;
		}
		
		final float sin_rdiff = (float) Math.sin(diff + Math.PI / 2);
		final float cos_rdiff = (float) Math.cos(diff + Math.PI / 2);
		
		if(pos + 1 == history.size()) {
			history.get(pos).rotation = rotation_msg.rotation;
		} else {
			for(int i = pos + 1; i < history.size(); ++i) {
				final float dx = history.get(i).x - posx;
				final float dy = history.get(i).y - posy;
				
				history.get(i).x = posx + dx * sin_rdiff - dy * cos_rdiff;
				history.get(i).y = posy + dy * sin_rdiff + dx * cos_rdiff;
				history.get(i).rotation = Utility.normalizeRotation(history.get(i).rotation + diff);
			}
		}
	}
	
	private void printState() {
		BrickSender.add("begin transmission");
		for(int i = 0; i < history.size(); ++i)
			BrickSender.add("" + i + ": " + history.get(i).toString());
		if(xy_msg != null)
			BrickSender.add("xy: " + xy_msg.toString());
		if(rotation_msg != null)
			BrickSender.add("rotation: " + rotation_msg.toString());
		BrickSender.add("end transmission");
	}
	
	
	private boolean canUpdate(long time) {
		final long now = System.currentTimeMillis();
		if(now - lastUpdated > 4000)
			return true;
		int pos = history.getPos(time);
		for(int i = pos; i >= 0 && time - history.get(i).time <= 100; --i)
			if(history.get(i).sharpTurn)
				return false;
		for(int i = pos + 1; i < history.size() && history.get(i).time - time <= 100; ++i)
			if(history.get(i).sharpTurn)
				return false;
		return true;
	}
	
	public void updateLocation(Location state) {
		int last = history.size() - 1;
		history.add(state);
		boolean print = false;
		
		if(DataContainer.xy != null || DataContainer.rotation != null) {
			synchronized(DataContainer.lock) {
				if(DataContainer.xy != null) {
					xy_msg = DataContainer.xy;
					DataContainer.xy = null;
				}
				if(DataContainer.rotation != null) {
					rotation_msg = DataContainer.rotation;
					DataContainer.rotation = null;
				}
				if(rotation_msg != null) {
					print = DataContainer.print_state;
					DataContainer.print_state = false;
				}
			}
			
			boolean ok = false;
			if(xy_msg != null && canUpdate(xy_msg.frameTime))
				ok = true;
			else if(rotation_msg != null && canUpdate(rotation_msg.frameTime))
				ok = true;
			
			if(ok) {
				String old = history.get(last).toString();
				if(xy_msg != null)
					BrickSender.add("xy update: " + xy_msg.frameTime + " vs " + System.currentTimeMillis());
				if(rotation_msg != null)
					BrickSender.add("rotation update: " + rotation_msg.frameTime + " vs " + System.currentTimeMillis());
				if(print)
					printState();
				if(xy_msg == null)
					updateRotation();
				else if(rotation_msg == null)
					updateXY();
				else if(rotation_msg.frameTime < xy_msg.frameTime) {
					updateRotation();
					updateXY();
				} else {
					updateXY();
					updateRotation();
				}
				if(print)
					printState();
				BrickSender.add("update: " + old + " -> " + history.get(last).toString());
				lastUpdated = System.currentTimeMillis();
			}
			
			xy_msg = null;
			rotation_msg = null;
		}
		
		history.update(state);
	}
}
