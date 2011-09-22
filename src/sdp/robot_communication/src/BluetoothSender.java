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

class BluetoothSender extends Thread {
	private DataOutputStream output;
	
	public BluetoothSender(DataOutputStream output) {
		super();
		setDaemon(true);
		this.output = output;
	}
	
	public void run() {
		boolean any = false;
		long lastSentXY = 0, lastSentRotation = 0, lastSentMove = 0, now, visionStep = 300, moveStep = 200;
		
		try {
			while(!interrupted()) {
				any = false;
				now = System.currentTimeMillis();
				
				if(Synchronizer.brickReady()) {
					for(int i = 0; i < 3; ++i)
						if(DataContainer.motor[i] != null) {
							any = true;
							synchronized(DataContainer.lock) {
								DataContainer.motor[i].write(i, output);
								DataContainer.motor[i] = null;
							}
						}
					
					if(lastSentMove + moveStep < now && DataContainer.move != null) {
						lastSentMove = now;
						any = true;
						synchronized(DataContainer.lock) {
							DataContainer.move.write(output);
							DataContainer.move = null;
						}
					}
					
					if(lastSentXY + visionStep < now && DataContainer.xy != null) {
						lastSentXY = now;
						any = true;
						synchronized(DataContainer.lock) {
							DataContainer.xy.write(output);
							DataContainer.xy = null;
						}
					}
					
					if(lastSentRotation + visionStep < now && DataContainer.rotation != null) {
						lastSentRotation = now;
						any = true;
						synchronized(DataContainer.lock) {
							DataContainer.rotation.write(output);
							DataContainer.rotation = null;
						}
					}
					
					if(DataContainer.powerMultiplier != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(18);
							output.writeFloat(DataContainer.powerMultiplier);
							DataContainer.powerMultiplier = null;
						}
					}
					
					if(DataContainer.maxSoftTurn != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(19);
							output.writeFloat(DataContainer.maxSoftTurn);
							DataContainer.maxSoftTurn = null;
						}
					}
					
					if(DataContainer.maxHeadingStabilizer != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(20);
							output.writeFloat(DataContainer.maxHeadingStabilizer);
							DataContainer.maxHeadingStabilizer = null;
						}
					}
					
					if(DataContainer.maxPowerLimiterConstant != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(21);
							output.writeFloat(DataContainer.maxPowerLimiterConstant);
							DataContainer.maxPowerLimiterConstant = null;
						}
					}
					
					if(DataContainer.powerLimitZone != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(22);
							output.writeByte(DataContainer.powerLimitZone);
							DataContainer.powerLimitZone = null;
						}
					}
					
					if(DataContainer.accelerationInterval != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(23);
							output.writeByte(DataContainer.accelerationInterval);
							DataContainer.accelerationInterval = null;
						}
					}
					
					if(DataContainer.initStraightPower != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(24);
							output.writeByte(DataContainer.initStraightPower);
							DataContainer.initStraightPower = null;
						}
					}
					
					if(DataContainer.initMidStraightTurnPower != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(25);
							output.writeByte(DataContainer.initMidStraightTurnPower);
							DataContainer.initMidStraightTurnPower = null;
						}
					}
					
					if(DataContainer.initTurnPower != null) {
						any = true;
						synchronized(DataContainer.lock) {
							output.writeByte(26);
							output.writeByte(DataContainer.initTurnPower);
							DataContainer.initTurnPower = null;
						}
					}
				}
				
				if(DataContainer.brickPing != null) {
					any = true;
					synchronized(DataContainer.lock) {
						DataContainer.brickPing.write(output);
						DataContainer.brickPing = null;
					}
				}
				
				if(DataContainer.printState) {
					any = true;
					synchronized(DataContainer.lock) {
						output.writeByte(17);
						DataContainer.printState = false;
					}
				}
				
				if(!any) {
					output.flush();
					try {
						Thread.sleep(0, 100);
					} catch(InterruptedException e) {
						break;
					}
				}
			}
		} catch(IOException e) {
			e.printStackTrace();
		}
	}
}