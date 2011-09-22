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
import java.io.DataOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import lejos.pc.comm.NXTComm;
import lejos.pc.comm.NXTCommException;
import lejos.pc.comm.NXTCommFactory;
import lejos.pc.comm.NXTInfo;

public class RobotCommunication {
	public static void main(String args[]) throws NXTCommException, IOException, InterruptedException {
		final SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS");
		System.out.println("/general/identify robot primary " + format.format(new Date()) + " lejos controller");
		
		NXTComm nxtComm = NXTCommFactory.createNXTComm(NXTCommFactory.BLUETOOTH);
		NXTInfo nxtInfo = new NXTInfo(NXTCommFactory.BLUETOOTH, "Group_11", "00:16:53:0e:be:f0");
		nxtComm.open(nxtInfo);
		
		DataInputStream input = new DataInputStream(nxtComm.getInputStream());
		DataOutputStream output = new DataOutputStream(nxtComm.getOutputStream());
		
		BluetoothListener bluetoothListener = new BluetoothListener(input);
		bluetoothListener.start();
		
		InputListener inputListener = new InputListener();
		inputListener.start();
		
		BluetoothSender bluetoothSender = new BluetoothSender(output);
		bluetoothSender.start();
		
		OutputSender outputSender = new OutputSender();
		outputSender.start();
		
		Synchronizer sync = new Synchronizer();
		sync.start();
		
		while(bluetoothListener.isAlive() && inputListener.isAlive() && bluetoothSender.isAlive() && outputSender.isAlive())
			Thread.sleep(100);
		
		System.out.println("/general/crashing thread state blisten " + bluetoothListener.isAlive() + ", ilisten " + inputListener.isAlive()
				+ ", bsender " + bluetoothSender.isAlive() + ", osender " + outputSender.isAlive());
		System.out.flush();
		
		nxtComm.close();
	}
}
