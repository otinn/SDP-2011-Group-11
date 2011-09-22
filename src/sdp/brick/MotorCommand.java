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

class MotorCommand {
	private MotorState state;
	private byte speed, id;
	
	MotorCommand(DataInputStream input, byte cmd) throws IOException {
		if(5 <= cmd && cmd <= 7) {
			state = MotorState.IDLE;
			speed = 0;
			id = (byte) (cmd - 5);
		} else if(8 <= cmd && cmd <= 10) {
			state = MotorState.BRAKE;
			speed = 0;
			id = (byte) (cmd - 8);
		} else {
			state = MotorState.RUN_INF;
			speed = input.readByte();
			if(speed == -128)
				speed = -127;
			id = (byte) (cmd - 11);
		}
	}
	
	MotorCommand(byte motor_id) {
		state = MotorState.BRAKE;
		speed = 0;
		id = motor_id;
	}
	
	MotorState getState() {
		return state;
	}
	
	public byte getId() {
		return id;
	}
	
	public byte getSpeed() {
		return speed;
	}
}