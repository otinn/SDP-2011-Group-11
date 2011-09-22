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

#include <boost/thread.hpp>
#include <iostream>

#include "synchronized_print.hpp"
#include "kicker_planner.hpp"
#include "main_planner.hpp"
#include "input_reader.hpp"
#include "utility.hpp"

using namespace std;
using namespace boost;

int main() {
	ios_base::sync_with_stdio(false);
	cout << "/general/identify planner primary " << get_datetime() << " planner" << endl;
	
	input_reader_pointer input_reader;
	thread t(input_reader);
	thread kicker(kicker_planner(input_reader.reader));

	main_planner ai(input_reader.reader);
	
	ai();
	return 0;
}
