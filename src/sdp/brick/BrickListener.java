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
import lejos.nxt.LCD;
import lejos.nxt.comm.BTConnection;
import lejos.nxt.comm.Bluetooth;

public class BrickListener extends Thread {
	private BrickSender sender;
	private DataInputStream input;
	
	private void stopEverything() {
		synchronized(DataContainer.lock) {
			DataContainer.move = new MoveCommand();
			for(int i = 0; i < 3; ++i)
				DataContainer.motor[i] = new MotorCommand((byte) i);
		}
		sender.interrupt();
	}
	
	private void listen() throws IOException {
		int num = 0;
		while(!interrupted()) {
			byte cmd = input.readByte();
			
			synchronized(DataContainer.lock) {
				if(1 <= cmd && cmd <= 4) {
					DataContainer.move = new MoveCommand(input, cmd);
				} else if(5 <= cmd && cmd <= 13) {
					MotorCommand t = new MotorCommand(input, cmd);
					DataContainer.motor[t.getId()] = t;
				} else if(cmd == 14) {
					DataContainer.ping = new PingCommand(input);
				} else if(cmd == 15) {
					DataContainer.xy = new VisionXYData(input);
				} else if(cmd == 16) {
					DataContainer.rotation = new VisionRotationData(input);
				} else if(cmd == 17) {
					DataContainer.print_state = true;
				} else if(cmd == 18) {
					DataContainer.powerMultiplier = input.readFloat();
				} else if(cmd == 19) {
					DataContainer.maxSoftTurn = input.readFloat();
				} else if(cmd == 20) {
					DataContainer.maxHeadingStabilizer = input.readFloat();
				} else if(cmd == 21) {
					DataContainer.maxPowerLimiterConstant = input.readFloat();
				} else if(cmd == 22) {
					DataContainer.powerLimitZone = input.readByte();
				} else if(cmd == 23) {
					DataContainer.accelerationInterval = input.readByte();
				} else if(cmd == 24) {
					DataContainer.initStraightPower = input.readByte();
				} else if(cmd == 25) {
					DataContainer.initMidStraightTurnPower = input.readByte();
				} else if(cmd == 26) {
					DataContainer.initTurnPower = input.readByte();
				} else {
					throw new IOException("Unknown cmd " + cmd);
				}
			}
			
			++num;
			LCD.drawString("recv " + num + ": " + cmd + " ", 0, 0);
			LCD.refresh();
		}
	}
	
	public void run() {
		while(!interrupted()) {
			LCD.clear();
			LCD.drawString("Waiting for PC", 0, 0);
			LCD.refresh();
			
			BTConnection connection = Bluetooth.waitForConnection();
			sender = new BrickSender(connection.openDataOutputStream());
			sender.start();
			
			input = connection.openDataInputStream();
			BrickSender.add("/brick/connected");
			
			LCD.clear();
			LCD.drawString("Waiting", 0, 0);
			LCD.refresh();
			
			try {
				listen();
			} catch(IOException e) {
				BrickSender.add("Error: " + e.getMessage());
			}
			
			connection.close();
			stopEverything();
		}
	}
}
