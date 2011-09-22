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

import lejos.nxt.LCD;

public class Start {
	public static void main(String[] args) throws InterruptedException {
		BrickListener listener = new BrickListener();
		listener.start();
		
		MotorController motor_controller = new MotorController();
		motor_controller.start();
		
		final Location state = new Location(0, 0, 0, System.currentTimeMillis());
		Movement controller = new Movement(state);
		controller.run(); // ignore the rest of this stuff
		controller.start();
		
		int num = 0;
		while(listener.isAlive()) {
			Thread.sleep(10);
			
			if(++num % 50 == 0) {
				if(DataContainer.print_state)
					LCD.drawString("print      ", 0, 1);
				else
					LCD.drawString("don't print", 0, 1);
				
				LCD.drawString("x: " + state.x, 0, 2);
				LCD.drawString("y: " + state.y, 0, 3);
				LCD.drawString("r: " + state.rotation, 0, 4);
				LCD.refresh();
			}
		}
	}
}