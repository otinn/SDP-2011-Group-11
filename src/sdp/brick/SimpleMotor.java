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

import lejos.nxt.MotorPort;

public class SimpleMotor {
	public final static SimpleMotor A = new SimpleMotor(MotorPort.A);
	public final static SimpleMotor B = new SimpleMotor(MotorPort.B);
	public final static SimpleMotor C = new SimpleMotor(MotorPort.C);
	
	private final MotorPort port;
	private int lastPower, lastCmd;
	
	private SimpleMotor(MotorPort port) {
		this.port = port;
		lastPower = 0;
		lastCmd = MotorPort.FLOAT;
		port.controlMotor(0, MotorPort.FLOAT);
	}
	
	public void idle() {
		if(lastCmd != MotorPort.FLOAT) {
			lastCmd = MotorPort.FLOAT;
			port.controlMotor(0, MotorPort.FLOAT);
		}
	}
	
	public void stop() {
		if(lastCmd != MotorPort.STOP) {
			lastCmd = MotorPort.STOP;
			port.controlMotor(0, MotorPort.STOP);
		}
	}
	
	/**
	 * @param power [-100, 100]
	 */
	public void run(int power) {
		if(power < 0)
			power = -Math.max(30, Math.min(100, -power));
		else
			power = Math.max(30, Math.min(100, power));
		if(lastCmd != MotorPort.BACKWARD || lastPower != power) {
			lastCmd = MotorPort.BACKWARD;
			if(power < 0)
				port.controlMotor(-power, MotorPort.FORWARD);
			else
				port.controlMotor(power, MotorPort.BACKWARD);
		}
	}
}
