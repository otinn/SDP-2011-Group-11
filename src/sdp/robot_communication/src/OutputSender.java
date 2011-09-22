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

import java.util.concurrent.LinkedBlockingQueue;

class OutputSender extends Thread {
	private static LinkedBlockingQueue<String> queue = new LinkedBlockingQueue<String>();
	private static OutputSender instance = null;
	
	public OutputSender() {
		super();
		setDaemon(true);
	}
	
	public void run() {
		String msg;
		
		try {
			while(!interrupted()) {
				msg = queue.take();
				System.out.println(msg.trim());
				if(queue.size() == 0)
					System.out.flush();
			}
		} catch(InterruptedException e) {
			e.printStackTrace();
		}
	}
	
	public static OutputSender getInstance() {
		if(instance == null)
			instance = new OutputSender();
		return instance;
	}
	
	public static void add(String msg) {
		queue.add(msg);
	}
}
