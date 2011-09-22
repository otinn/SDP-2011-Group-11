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

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.ParseException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class InputListener extends Thread {
	public InputListener() {
		super();
		setDaemon(true);
	}
	
	private static int getMotorId(String name) {
		if(name.equals("B") || name.equals("left"))
			return 1;
		if(name.equals("C") || name.equals("right"))
			return 2;
		return 0;
	}
	
	public void run() {
		String time_format = "([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\\.([0-9]+)"; // 7 groups
		String real_format = "-?[0-9]+(\\.[0-9]+)?([eE]-?[0-9]+)?"; // 2 groups
		Pattern vision_pong = Pattern.compile("^/general/vision/pong\\s+([0-9]+)\\s+([0-9]+)\\s+([0-9]+)$");
		Pattern vision_xy = Pattern.compile("^/vision/xy\\s+us\\s+(" + real_format + ")\\s+(" + real_format + ")\\s+(" + time_format + ")$");
		Pattern vision_rotation = Pattern.compile("^/vision/rotation\\s+us\\s+(" + real_format + ")\\s+(" + time_format + ")$");
		Pattern motor_brake_idle = Pattern.compile("^/movement/order/(brake|idle)\\s+(A|B|C|left|right)$");
		Pattern motor_run_inf = Pattern.compile("^/movement/order/run_inf\\s+(A|B|C|left|right)\\s+(-?[0-9]+)$");
		Pattern kicker_run_inf = Pattern.compile("^/kicker/order/run_inf\\s+(-?[0-9]+)$");
		Pattern power_multiplier = Pattern.compile("^/general/robot/power_multiplier\\s+(" + real_format + ")$");
		Pattern maxSoftTurn = Pattern.compile("^/general/robot/max_soft_turn\\s+(" + real_format + ")$");
		Pattern maxHeadingStabilizer = Pattern.compile("^/general/robot/max_heading_stabilizer\\s+(" + real_format + ")$");
		Pattern maxPowerLimiterConstant = Pattern.compile("^/general/robot/max_power_limiter_constant\\s+(" + real_format + ")$");
		Pattern powerLimitZone = Pattern.compile("^/general/robot/power_limit_zone\\s+([0-9]{1,2})$");
		Pattern accelerationInterval = Pattern.compile("^/general/robot/acceleration_interval\\s+([0-9]{1,2})$");
		Pattern initStraightPower = Pattern.compile("^/general/robot/init_straight_power\\s+([0-9]{1,2})$");
		Pattern initMidStraightTurnPower = Pattern.compile("^/general/robot/init_mid_straight_turn_power\\s+([0-9]{1,2})$");
		Pattern initTurnPower = Pattern.compile("^/general/robot/init_turn_power\\s+([0-9]{1,2})$");
		Pattern magic_offset = Pattern.compile("^/general/robot/magic_offset\\s+(-?[0-9]+)$");
		Pattern move = Pattern.compile("^/planner/move\\s+(.+)$");
		Pattern move_rev = Pattern.compile("^/planner/move_rev\\s+(.+)$");
		
		BufferedReader stdIn = new BufferedReader(new InputStreamReader(System.in));
		long received;
		Matcher match;
		String s;
		
		while(true) {
			try {
				s = stdIn.readLine().trim();
			} catch(IOException e) {
				e.printStackTrace();
				return;
			}
			
			match = vision_pong.matcher(s);
			if(match.matches()) {
				received = System.currentTimeMillis();
				Synchronizer.addVisionMessage(Long.parseLong(match.group(1)), Long.parseLong(match.group(2)), Long.parseLong(match.group(3)), received);
				continue;
			}
			
			synchronized(DataContainer.lock) {
				match = vision_xy.matcher(s);
				if(match.matches()) {
					try {
						DataContainer.xy = new VisionXYData(Float.parseFloat(match.group(1)), Float.parseFloat(match.group(4)), match.group(7));
					} catch(NumberFormatException e) {
						e.printStackTrace();
					} catch(ParseException e) {
						e.printStackTrace();
					}
					continue;
				}
				
				match = vision_rotation.matcher(s);
				if(match.matches()) {
					try {
						DataContainer.rotation = new VisionRotationData(Float.parseFloat(match.group(1)), match.group(4));
					} catch(NumberFormatException e) {
						e.printStackTrace();
					} catch(ParseException e) {
						e.printStackTrace();
					}
					continue;
				}
				
				match = move.matcher(s);
				if(match.matches()) {
					try {
						DataContainer.move = new MoveCommand(match.group(1), false);
					} catch(IOException e) {
						e.printStackTrace();
					}
					continue;
				}
				
				match = move_rev.matcher(s);
				if(match.matches()) {
					try {
						DataContainer.move = new MoveCommand(match.group(1), true);
					} catch(IOException e) {
						e.printStackTrace();
					}
					continue;
				}
				
				match = motor_brake_idle.matcher(s);
				if(match.matches()) {
					DataContainer.motor[getMotorId(match.group(2))] = new MotorCommand(match.group(1).equals("idle")? MotorState.IDLE: MotorState.BRAKE);
					continue;
				}
				
				match = motor_run_inf.matcher(s);
				if(match.matches()) {
					DataContainer.motor[getMotorId(match.group(1))] = new MotorCommand((int) Integer.parseInt(match.group(2)));
					continue;
				}
				
				if(s.equals("/kicker/order/brake")) {
					DataContainer.motor[getMotorId("kicker")] = new MotorCommand(MotorState.BRAKE);
					continue;
				}
				
				match = kicker_run_inf.matcher(s);
				if(match.matches()) {
					DataContainer.motor[getMotorId("kicker")] = new MotorCommand((int) Integer.parseInt(match.group(1)));
					continue;
				}
				
				match = power_multiplier.matcher(s);
				if(match.matches()) {
					DataContainer.powerMultiplier = Float.parseFloat(match.group(1));
					continue;
				}
				
				match = maxSoftTurn.matcher(s);
				if(match.matches()) {
					DataContainer.maxSoftTurn = Float.parseFloat(match.group(1));
					continue;
				}
				
				match = maxHeadingStabilizer.matcher(s);
				if(match.matches()) {
					DataContainer.maxHeadingStabilizer = Float.parseFloat(match.group(1));
					continue;
				}
				
				match = maxPowerLimiterConstant.matcher(s);
				if(match.matches()) {
					DataContainer.maxPowerLimiterConstant = Float.parseFloat(match.group(1));
					continue;
				}
				
				match = powerLimitZone.matcher(s);
				if(match.matches()) {
					DataContainer.powerLimitZone = Byte.parseByte(match.group(1));
					continue;
				}
				
				match = accelerationInterval.matcher(s);
				if(match.matches()) {
					DataContainer.accelerationInterval = Byte.parseByte(match.group(1));
					continue;
				}
				
				match = initStraightPower.matcher(s);
				if(match.matches()) {
					DataContainer.initStraightPower = Byte.parseByte(match.group(1));
					continue;
				}
				
				match = initMidStraightTurnPower.matcher(s);
				if(match.matches()) {
					DataContainer.initMidStraightTurnPower = Byte.parseByte(match.group(1));
					continue;
				}
				
				match = initTurnPower.matcher(s);
				if(match.matches()) {
					DataContainer.initTurnPower = Byte.parseByte(match.group(1));
					continue;
				}
				
				match = magic_offset.matcher(s);
				if(match.matches()) {
					DataContainer.magicOffset = Integer.parseInt(match.group(1));
					continue;
				}
				
				if(s.equals("/general/robot/debug/print_state")) {
					DataContainer.printState = true;
					continue;
				}
			}
			
			if(s.equals("/central/exit")) {
				System.out.println("/general/exiting obeying exit message");
				return;
			} else if(s.equals("")) {
				System.out.println("/general/exiting received empty message");
				return;
			}
		}
	}
}