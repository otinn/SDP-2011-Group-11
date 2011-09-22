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

import lejos.nxt.Battery;
import lejos.nxt.SensorPort;
import lejos.nxt.TouchSensor;

abstract class OrderNode {
	private final static SimpleMotor left = SimpleMotor.B;
	private final static SimpleMotor right = SimpleMotor.C;
	private boolean sharpTurn = false;
	
	public abstract boolean execute(Location state) throws InterruptedException;
	
	protected void brake() throws InterruptedException {
		left.stop();
		right.stop();
	}
	
	protected void idle() {
		left.idle();
		right.idle();
	}
	
	protected void changePower(int leftPower, int rightPower, boolean goBackwards) {
		if(goBackwards) {
			left.run(-rightPower);
			right.run(-leftPower);
		} else {
			left.run(leftPower);
			right.run(rightPower);
		}
		
		if(Math.abs(leftPower - rightPower) <= 5)
			sharpTurn = false;
		else if((leftPower < 0) != (rightPower < 0))
			sharpTurn = true;
		else {
			int diff = Math.abs(leftPower - rightPower);
			int ma = Math.max(Math.abs(leftPower), Math.abs(rightPower));
			sharpTurn = diff / (float) ma > 0.15f;
		}
	}
	
	protected static int scalePower(int power) {
		return Math.max(-100, Math.min(100, (int) Math.round(power * Movement.powerMultiplier * 1.3)));
	}
	
	public boolean turning() {
		return sharpTurn;
	}
}

class MovementNode extends OrderNode {
	private static final float[] pastAngle = new float[50];
	private static int anglePos = 0;
	private static int lastPower = 0;
	private static long lastPowerChange = 0;
	
	static {
		for(int i = 0; i < pastAngle.length; ++i)
			pastAngle[i] = 5;
	}
	
	private static boolean stable() {
		for(int i = 0; i < pastAngle.length; ++i)
			if(!(pastAngle[i] < 0.2 || pastAngle[i] > 6.1))
				return false;
		return true;
	}
	
	private float x, y;
	private boolean stop, allowReversing, turnHard = false;
	
	MovementNode(float x, float y, boolean stop, boolean allowReversing) {
		this.x = x;
		this.y = y;
		this.stop = stop;
		this.allowReversing = allowReversing;
		
		long now = System.currentTimeMillis();
		if(lastPower < scalePower(Movement.initStraightPower) || now - lastPowerChange > 1000) {
			lastPower = scalePower(Movement.initStraightPower);
			lastPowerChange = System.currentTimeMillis();
		}
	}
	
	public boolean execute(Location state) {
		float dist = (float) Math.sqrt(Math.pow((state.x - this.x), 2.0) + Math.pow(state.y - this.y, 2.0));
		if(stop) {
			if(dist < 2)
				return true;
		} else {
			if(dist < 3)
				return true;
		}
		
		final long now = System.currentTimeMillis();
		
		float targetRotation = Utility.normalizeRotation((float) Math.atan2(this.x - state.x, this.y - state.y));
		float angle = Utility.normalizeRotation(targetRotation - state.rotation);
		float difference = (float) Math.min(angle, 2 * Math.PI - angle);
		boolean backwardsMovement = false;
		
		if(((state.x - this.x > 3) || allowReversing) && difference > (3 * Math.PI) / 4) {
			angle = Utility.normalizeRotation((float) (angle + Math.PI));
			difference = (float) Math.min(angle, 2 * Math.PI - angle);
			backwardsMovement = true;
		}
		
		pastAngle[anglePos] = angle;
		++anglePos;
		if(anglePos == pastAngle.length)
			anglePos = 0;
		
		if(turnHard || difference > Movement.maxSoftTurn) {
			if(difference < 0.05) {
				turnHard = false;
				return execute(state);
			}
			final int power = scalePower(Movement.initMidStraightTurnPower);
			turnHard = true;
			lastPowerChange = now;
			lastPower = power;
			if(angle < Math.PI)
				changePower(power, -power, backwardsMovement);
			else
				changePower(-power, power, backwardsMovement);
		} else {
			lastPower = Math.max(lastPower, scalePower(Movement.initStraightPower));
			int maxPower = (int) Math.round(scalePower(Movement.initStraightPower) + Math.max(0, dist - Movement.powerLimitZone)
					* Movement.maxPowerLimiterConstant);
			maxPower = Math.max(scalePower(Movement.initStraightPower), Math.min(100, maxPower));
			
			if(stable()) {
				if(now - lastPowerChange >= Movement.accelerationInterval && lastPower + 1 <= maxPower) {
					lastPowerChange = now;
					++lastPower;
				} else if(lastPower > maxPower) {
					lastPowerChange = now;
					lastPower = maxPower;
				}
			} else {
				lastPowerChange = now;
				lastPower = scalePower(Movement.initStraightPower);
			}
			
			// slow down one side only
			final int diff = (int) Math.floor(lastPower * Movement.maxHeadingStabilizer * difference / Movement.maxSoftTurn);
			
			if(angle < Math.PI)
				changePower(lastPower, lastPower - diff, backwardsMovement);
			else
				changePower(lastPower - diff, lastPower, backwardsMovement);
		}
		
		state.sharpTurn = turning();
		return false;
	}
}

class TurningNode extends OrderNode {
	private final float rotation;
	
	TurningNode(float rotation) {
		this.rotation = rotation;
	}
	
	public boolean execute(Location state) {
		float angle = Utility.normalizeRotation(this.rotation - state.rotation);
		float difference = Math.min(angle, (float) (2 * Math.PI - angle));
		if(difference < 0.05)
			return true;
		
		int power = scalePower(Movement.initTurnPower);
		if(angle < Math.PI)
			changePower(power, -power, false);
		else
			changePower(-power, power, false);
		
		state.sharpTurn = turning();
		return false;
	}
}

class StopNode extends OrderNode {
	protected boolean done = false;
	
	public boolean execute(Location state) throws InterruptedException {
		state.sharpTurn = false;
		if(done)
			return true;
		brake();
		done = true;
		return false;
	}
}

public class Movement extends Thread {
	static float powerMultiplier;
	static float maxSoftTurn;
	static float maxHeadingStabilizer;
	static float maxPowerLimiterConstant;
	static int powerLimitZone;
	static int accelerationInterval;
	static int initStraightPower;
	static int initMidStraightTurnPower;
	static int initTurnPower;
	
	private static void updateConstants() {
		powerMultiplier = DataContainer.powerMultiplier;
		maxSoftTurn = DataContainer.maxSoftTurn;
		maxHeadingStabilizer = DataContainer.maxHeadingStabilizer;
		maxPowerLimiterConstant = DataContainer.maxPowerLimiterConstant;
		powerLimitZone = DataContainer.powerLimitZone;
		accelerationInterval = DataContainer.accelerationInterval;
		initStraightPower = DataContainer.initStraightPower;
		initMidStraightTurnPower = DataContainer.initMidStraightTurnPower;
		initTurnPower = DataContainer.initTurnPower;
	}
	
	private static TouchSensor touchFrontLeft = new TouchSensor(SensorPort.S1);
	private static TouchSensor touchFrontRight = new TouchSensor(SensorPort.S2);
	private static TouchSensor touchRearLeft = new TouchSensor(SensorPort.S3);
	private static TouchSensor touchRearRight = new TouchSensor(SensorPort.S4);
	private static SimpleMotor left = SimpleMotor.B;
	private static SimpleMotor right = SimpleMotor.C;
	
	private final Location state;
	private int orderNumber = 0;
	private int touchSpeed = 65;
	private MoveCommand cmd = null;
	private OrderNode cur = null;
	private int movePos = 0;
	
	public Movement(Location state) {
		super();
		this.state = state;
	}
	
	private boolean handleTouch() throws InterruptedException {
		if(!touchFrontLeft.isPressed() && !touchFrontRight.isPressed() && !touchRearLeft.isPressed() && !touchRearRight.isPressed())
			return false;
		Thread.sleep(50);
		
		if((touchFrontLeft.isPressed() || touchFrontRight.isPressed()) && (touchRearLeft.isPressed() || touchRearRight.isPressed())) {
			left.stop();
			right.stop();
		} else if(touchFrontLeft.isPressed() && touchFrontRight.isPressed()) {
			left.run(-touchSpeed);
			right.run(-touchSpeed);
		} else if(touchFrontLeft.isPressed()) {
			left.run(touchSpeed);
			right.run(-touchSpeed);
		} else if(touchFrontRight.isPressed()) {
			left.run(-touchSpeed);
			right.run(touchSpeed);
		} else if(touchRearLeft.isPressed() && touchRearRight.isPressed()) {
			left.run(touchSpeed);
			right.run(touchSpeed);
		} else if(touchRearLeft.isPressed()) {
			left.run(touchSpeed);
			right.run(-touchSpeed);
		} else if(touchRearRight.isPressed()) {
			left.run(-touchSpeed);
			right.run(touchSpeed);
		}
		Thread.sleep(50);
		return true;
	}
	
	private void loadNextNode() {
		if(movePos < cmd.getRoute().size()) {
			cur = new MovementNode(cmd.getRoute().get(movePos).x, cmd.getRoute().get(movePos).y, movePos + 1 == cmd.getRoute().size(), cmd.reversingAllowed());
			++movePos;
		} else if(cmd.getRoute().size() == movePos) {
			if(cmd.getFinalRotation() != null)
				cur = new TurningNode(cmd.getFinalRotation());
			else
				cur = new StopNode();
			++movePos;
		} else {
			if(cur == null || !(cur instanceof StopNode))
				cur = new StopNode();
		}
	}
	
	public void run() {
		final VisionLocationTracker vision = new VisionLocationTracker(state);
		final LocationTracker tracker = new LocationTracker(state);
		
		int lastFrequencySent = (int) System.currentTimeMillis(), lastVoltageSent = 0, lastTouch = 0;
		int iterationCounter = 0, now;
		boolean inTouchState = false;
		
		try {
			while(true) {
				now = (int) System.currentTimeMillis();
				++iterationCounter;
				
				if(now - lastVoltageSent >= 30000) {
					if(BrickSender.haveConnection())
						BrickSender.add("/brick/info/battery " + Battery.getVoltage());
					lastVoltageSent = now;
				}
				
				if(now - lastFrequencySent >= 500) {
					if(BrickSender.haveConnection())
						BrickSender.add("/brick/info/frequency " + (iterationCounter * 1000 / (now - lastFrequencySent)));
					lastFrequencySent = now;
					iterationCounter = 0;
				}
				
				if(DataContainer.move != null) {
					synchronized(DataContainer.lock) {
						cmd = DataContainer.move;
						DataContainer.move = null;
						updateConstants();
					}
					movePos = 0;
					loadNextNode();
					++orderNumber;
				}
				
				tracker.updateLocation();
				vision.updateLocation(state);
				
				if(handleTouch()) {
					inTouchState = true;
					lastTouch = now;
					continue;
				} else if(inTouchState) {
					if(now - lastTouch <= 400) {
						Thread.sleep(1);
						continue;
					}
					left.stop();
					right.stop();
					if(now - lastTouch <= 500) {
						Thread.sleep(1);
						continue;
					}
					inTouchState = false;
					continue;
				}
				
				if(cur.execute(state))
					loadNextNode();
				
				Thread.sleep(1);
			}
		} catch(InterruptedException e) {
			return;
		}
	}
}
