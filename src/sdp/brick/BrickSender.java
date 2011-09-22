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
import java.util.EmptyQueueException;
import java.util.Queue;

class BrickSender extends Thread {
	private static Queue<String> queue = new Queue<String>();
	private static boolean alive = false;
	private DataOutputStream output;
	
	private void writeString(String s) throws IOException {
		output.writeChars(s + "\n");
		output.flush();
	}
	
	public BrickSender(DataOutputStream output) {
		super();
		this.output = output;
	}
	
	public void run() {
		PingCommand ping;
		alive = true;
		
		boolean any;
		try {
			while(!interrupted()) {
				if(DataContainer.ping != null) {
					synchronized(DataContainer.lock) {
						ping = DataContainer.ping;
						DataContainer.ping = null;
					}
					writeString(ping.toString());
				}
				
				any = false;
				while(!queue.empty()) {
					any = true;
					try {
						writeString((String) queue.peek());
					} catch(EmptyQueueException e) {
						// this can never happen
						alive = false;
						return;
					}
					queue.pop();
				}
				if(!any)
					try {
						Thread.sleep(1);
					} catch(InterruptedException e) {
						break;
					}
			}
		} catch(IOException e) {
			BrickSender.add("Error: " + e.getMessage());
			// the connection has been lost, stop
		}
		
		alive = false;
	}
	
	public static void add(String msg) {
		queue.push(msg);
	}
	
	public static boolean haveConnection() {
		return alive;
	}
	
}