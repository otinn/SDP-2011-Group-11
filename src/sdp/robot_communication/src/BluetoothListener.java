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
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class BluetoothListener extends Thread {
	private DataInputStream input;
	
	public BluetoothListener(DataInputStream input) {
		super();
		setDaemon(true);
		this.input = input;
	}
	
	public void run() {
		Pattern brick_pong = Pattern.compile("^/brick/pong\\s+([0-9]+)\\s+([0-9]+)\\s+([0-9]+)$");
		Matcher match;
		
		boolean started_receiving = false;
		long start_time = 0;
		
		StringBuilder buf = new StringBuilder();
		while(true) {
			char c;
			try {
				c = input.readChar();
				if(!started_receiving) {
					started_receiving = true;
					start_time = System.currentTimeMillis();
				}
			} catch(IOException e) {
				e.printStackTrace();
				return;
			}
			if(c == '\n') {
				String s = buf.toString();
				match = brick_pong.matcher(s);
				if(match.matches())
					Synchronizer.addBrickMessage(Long.parseLong(match.group(1)), Long.parseLong(match.group(2)), Long.parseLong(match.group(3)), start_time);
				else
					OutputSender.add(s);
				
				buf.delete(0, buf.length());
				started_receiving = false;
			} else
				buf.append(c);
		}
	}
}