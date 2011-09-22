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

import java.math.BigInteger;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.concurrent.LinkedBlockingQueue;

public class Synchronizer extends Thread {
	private static class SyncMsg {
		public final long t0, t1, t2, t3;
		
		SyncMsg(long t0, long t1, long t2, long t3) {
			this.t0 = t0;
			this.t1 = t1;
			this.t2 = t2;
			this.t3 = t3;
		}
	}
	
	private final static LinkedBlockingQueue<SyncMsg> brickQueue = new LinkedBlockingQueue<SyncMsg>();
	private final static LinkedBlockingQueue<SyncMsg> visionQueue = new LinkedBlockingQueue<SyncMsg>();
	private final static ArrayList<Long> brickList = new ArrayList<Long>();
	private final static ArrayList<Long> visionList = new ArrayList<Long>();
	private final static int numPings = 200;
	private static boolean brickMeasured = false;
	
	private long lastVisionPing = 0;
	
	Synchronizer() {
		super();
		setDaemon(true);
	}
	
	private void sendBrickPing() {
		synchronized(DataContainer.lock) {
			DataContainer.brickPing = new BrickPingCommand();
		}
	}
	
	private void sendVisionPing() {
		lastVisionPing = System.currentTimeMillis();
		OutputSender.add("/general/vision/ping " + lastVisionPing);
	}
	
	private static long calculateOffset(SyncMsg msg) {
		return ((msg.t1 - msg.t0) + (msg.t2 - msg.t3)) / 2;
	}
	
	public void run() {
		brickQueue.clear();
		visionQueue.clear();
		sendVisionPing();
		sendBrickPing();
		SyncMsg msg;
		boolean any, vision_done = false;
		
		try {
			while(!interrupted() && (!brickMeasured || !vision_done)) {
				any = false;
				
				if(!brickMeasured && brickQueue.size() != 0) {
					any = true;
					synchronized(brickList) {
						SyncMsg t = brickQueue.take();
						OutputSender.add("brick offset: " + t.t0 + " " + t.t1 + " " + t.t2 + " " + t.t3 + " (" + calculateOffset(t) + ")");
						brickList.add(calculateOffset(t));
					}
					if(brickList.size() < numPings)
						sendBrickPing();
					else {
						brickMeasured = true;
						OutputSender.add("Brick done: " + getBrickOffset());
					}
				}
				
				if(!vision_done && visionQueue.size() != 0) {
					any = true;
					msg = visionQueue.take();
					if(msg.t0 == lastVisionPing) {
						synchronized(visionList) {
							OutputSender.add("vision offset: " + msg.t0 + " " + msg.t1 + " " + msg.t2 + " " + msg.t3 + " (" + calculateOffset(msg) + ")");
							visionList.add(calculateOffset(msg));
						}
						if(visionList.size() < numPings)
							sendVisionPing();
						else {
							vision_done = true;
							OutputSender.add("Vision done: " + getVisionOffset());
						}
					}
				}
				
				if(!any)
					Thread.sleep(1);
			}
		} catch(InterruptedException e) {
			e.printStackTrace();
		}
	}
	
	static void addBrickMessage(long t0, long t1, long t2, long t3) {
		brickQueue.add(new SyncMsg(t0, t1, t2, t3));
	}
	
	static void addVisionMessage(long t0, long t1, long t2, long t3) {
		visionQueue.add(new SyncMsg(t0, t1, t2, t3));
	}
	
	private static long getLikelyOffset(ArrayList<Long> list) {
		ArrayList<Long> values = new ArrayList<Long>();
		for(Long n: list)
			values.add(new Long(n));
		
		Collections.sort(values);
		int tenPercent = (int) Math.round(values.size() / 10.0);
		for(int i = 0; i < tenPercent; ++i)
			values.remove(values.size() - 1);
		for(int i = 0; i < tenPercent; ++i)
			values.remove(0);
		
		BigInteger sum = BigInteger.ZERO;
		for(Long n: values)
			sum = sum.add(new BigInteger("" + n));
		sum = sum.add(new BigInteger("" + (values.size() / 2)));
		return sum.divide(new BigInteger("" + values.size())).longValue();
	}
	
	private static long lastVisionSize = -1;
	private static long lastVisionValue = -1;
	
	private static long getVisionOffset() {
		if(visionList.size() == 0)
			return 0;
		if(visionList.size() == lastVisionSize)
			return lastVisionValue;
		
		synchronized(visionList) {
			lastVisionSize = visionList.size();
			lastVisionValue = getLikelyOffset(visionList);
		}
		
		OutputSender.add("vision offset: " + lastVisionValue);
		return lastVisionValue;
	}
	
	private static long lastBrickSize = -1;
	private static long lastBrickValue = -1;
	
	private static long getBrickOffset() {
		if(brickList.size() == 0)
			return 0;
		if(brickList.size() == lastBrickSize)
			return lastBrickValue;
		
		synchronized(brickList) {
			lastBrickSize = brickList.size();
			lastBrickValue = getLikelyOffset(brickList);
		}
		
		OutputSender.add("brick offset: " + lastBrickValue);
		return lastBrickValue;
	}
	
	private static long parseDate(String s) throws ParseException {
		SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS");
		int pos = s.indexOf('.');
		if(pos == -1) {
			s = s + ".000";
		} else {
			int t = (int) Math.round(Double.parseDouble("0" + s.substring(pos)) * 1000);
			s = s.substring(0, pos + 1);
			s = s + (t / 100);
			t %= 100;
			s = s + (t / 10);
			t %= 10;
			s = s + t;
		}
		return format.parse(s).getTime();
	}
	
	static long getBrickTime(String visionTime) throws ParseException {
		final int magicOffset = DataContainer.magicOffset;
		final long res = parseDate(visionTime) + getBrickOffset() - getVisionOffset() + magicOffset;
		OutputSender.add("offset calc: magic(" + magicOffset + ") " + System.currentTimeMillis() + " " + visionTime + " "
				+ parseDate(visionTime) + ", " + getVisionOffset() + ", " + getBrickOffset());
		return res;
	}
	
	static boolean brickReady() {
		return brickMeasured;
	}
}