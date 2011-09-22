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

class MotorController extends Thread {
	private final static SimpleMotor motor[] = new SimpleMotor[]{SimpleMotor.A, SimpleMotor.B, SimpleMotor.C};
	
	public void run() {
		MotorCommand cmd;
		int id;
		
		while(!interrupted()) {
			for(id = 0; id < 3; ++id) {
				if(DataContainer.motor[id] != null) {
					synchronized(DataContainer.lock) {
						cmd = DataContainer.motor[id];
						DataContainer.motor[id] = null;
					}
					
					if(cmd.getState() == MotorState.RUN_INF) {
						motor[id].run(100 * cmd.getSpeed() / 127);
					} else if(cmd.getState() == MotorState.BRAKE) {
						motor[id].stop();
					} else { // IDLE
						motor[id].idle();
					}
				}
			}
			
			try {
				Thread.sleep(1);
			} catch(InterruptedException e) {
				break;
			}
		}
		
		for(id = 0; id < 3; ++id)
			motor[id].idle();
	}
}