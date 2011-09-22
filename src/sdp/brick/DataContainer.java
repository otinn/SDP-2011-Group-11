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

public abstract class DataContainer {
	static Object lock = new Object();
	static MoveCommand move = new MoveCommand();
	static MotorCommand motor[] = new MotorCommand[3];
	static VisionXYData xy = null;
	static VisionRotationData rotation = null;
	static PingCommand ping = null;
	static boolean print_state = false;
	
	static float powerMultiplier = 1.2f; // every power is multiplied by this constant
	static float maxSoftTurn = 0.8f; // max radians the wanted and current heading can differ to not turn on spot
	static float maxHeadingStabilizer = 1f; // amount one wheel power can be lower than the faster one [0, 1]
	static float maxPowerLimiterConstant = 0.7f; // extra percents of power that can be used per cm to the target
	static int powerLimitZone = 20; // closer than this many cm to the target the power will be limited to the initial value
	static int accelerationInterval = 0; // increase power every this many milliseconds
	static int initStraightPower = 60; // initial power to use when going in a straight line
	static int initMidStraightTurnPower = 60; // initial power to use when turning on spot in MovementNodes
	static int initTurnPower = 60; // initial power to use when turning on spot in TurningNodes
}