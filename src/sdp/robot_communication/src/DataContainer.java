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

abstract class DataContainer {
	static Object lock = new Object();
	static MoveCommand move = null;
	static MotorCommand motor[] = new MotorCommand[3];
	static VisionXYData xy = null;
	static VisionRotationData rotation = null;
	static BrickPingCommand brickPing = null;
	static boolean printState = false;
	static int magicOffset = -225;
	
	static Float powerMultiplier = null;
	static Float maxSoftTurn = null;
	static Float maxHeadingStabilizer = null;
	static Float maxPowerLimiterConstant = null;
	static Byte powerLimitZone = null;
	static Byte accelerationInterval = null;
	static Byte initStraightPower = null;
	static Byte initMidStraightTurnPower = null;
	static Byte initTurnPower = null;
}