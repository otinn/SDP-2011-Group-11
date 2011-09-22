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

#ifndef utility_h__
#define utility_h__

#include <boost/shared_ptr.hpp>
#include <boost/date_time.hpp>
#include <boost/thread.hpp>
#include <cmath>

using namespace std;
using namespace boost;

const double pi = 3.14159265;
#define sptr boost::shared_ptr

enum STATE_TYPE {
	PLAY,
	WAIT,
	KICK_PENALTY,
	DEFEND_PENALTY
};

enum OBJECT_TYPE {
	US = 0,
	ENEMY = 1,
	BALL = 2
};

const string get_datetime() {
	return to_iso_extended_string(boost::posix_time::microsec_clock::local_time());
}

const long long datetime_in_nanoseconds(string s) {
	using namespace boost::gregorian;
	using namespace boost::posix_time;
	const static ptime epoch(date(1970, Jan, 1));
	s[10] = ' ';
	return (time_from_string(s) - epoch).total_nanoseconds();
}

long long now_in_nanoseconds() {
	xtime t;
	xtime_get(&t, TIME_UTC);
	return t.sec * 1000000000ll + t.nsec;
}

void sleep_ms(long long milliseconds) {
	xtime t;
	xtime_get(&t, TIME_UTC);
	t.sec += milliseconds / 1000;
	milliseconds %= 1000;
	t.nsec += 1000000 * milliseconds;
	thread::sleep(t);
}

float round(float f) {
	return floor(f + 0.5);
}

long long seconds_in_nanoseconds(float sec) {
	return (long long) round(sec * 1e9);
}

#endif // utility_h__