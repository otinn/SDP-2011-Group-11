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

// This file is based on odometer.c on http://www.seattlerobotics.org/encoder/200010/dead_reckoning_article.html as of 2011-02-27.
/***********************************************************/
/* odometer.c - Copyright (C) 2000, Dafydd Walters         */
/***********************************************************/

import lejos.nxt.MotorPort;

class LocationTracker {
	private final static float wheelDiameter = 8.05f;
	private final static float axleLength = 12.6f;
	private final static int pulsesPerRevolution = 360;
	private final static float MUL_COUNT = (float) (Math.PI * wheelDiameter / pulsesPerRevolution);
	private final static MotorPort left = MotorPort.B;
	private final static MotorPort right = MotorPort.C;

	private float dist_left, dist_right, cos_current, sin_current, expr1, left_minus_right_over_axle;
	private int left_ticks, right_ticks, last_left, last_right, t1, t2;

	public final Location pos;

	LocationTracker(Location pos) {
		last_left = -MotorPort.B.getTachoCount(); // use negative counts if the motors are reversed
		last_right = -MotorPort.C.getTachoCount(); // use negative counts if the motors are reversed
		this.pos = pos;
	}

	public void updateLocation() {
		t1 = -left.getTachoCount(); // use negative counts if the motors are reversed
		t2 = -right.getTachoCount(); // use negative counts if the motors are reversed
		pos.time = System.currentTimeMillis();

		left_ticks = t1 - last_left;
		right_ticks = t2 - last_right;

		last_left = t1;
		last_right = t2;

		dist_left = (float) left_ticks * MUL_COUNT;
		dist_right = (float) right_ticks * MUL_COUNT;

		cos_current = (float) Math.cos(pos.rotation);
		sin_current = (float) Math.sin(pos.rotation);

		if(left_ticks == right_ticks) {
			// Moving in a straight line
			pos.x += dist_left * sin_current;
			pos.y += dist_left * cos_current;
		} else {
			// Moving in an arc
			expr1 = (float) (axleLength * (dist_right + dist_left) / 2.0 / (dist_right - dist_left));
			left_minus_right_over_axle = (dist_left - dist_right) / axleLength;
			pos.x += expr1 * (Math.cos(left_minus_right_over_axle + pos.rotation) - cos_current);
			pos.y -= expr1 * (Math.sin(left_minus_right_over_axle + pos.rotation) - sin_current);
			pos.rotation = Utility.normalizeRotation(pos.rotation + left_minus_right_over_axle);
		}
	}
}