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

class PingCommand {
	private final long pc_sent, brick_received;
	
	PingCommand(DataInputStream input) throws IOException {
		brick_received = System.currentTimeMillis();
		pc_sent = input.readLong();
	}
	
	public String toString() {
		return "/brick/pong " + pc_sent + " " + brick_received + " " + System.currentTimeMillis();
	}
}