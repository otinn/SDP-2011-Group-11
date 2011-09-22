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

class MotorCommand {
	final MotorState state;
	final int speed;
	
	MotorCommand(MotorState state) {
		this.state = state;
		this.speed = 0;
	}
	
	MotorCommand(int speed) {
		this.state = MotorState.RUN_INF;
		this.speed = Math.min(127, Math.max(-128, speed));
	}
	
	public void write(int id, DataOutputStream output) throws IOException {
		if(state == MotorState.IDLE) {
			output.writeByte(5 + id);
		} else if(state == MotorState.BRAKE) {
			output.writeByte(8 + id);
		} else {
			output.writeByte(11 + id);
			output.writeByte(speed);
		}
	}
}