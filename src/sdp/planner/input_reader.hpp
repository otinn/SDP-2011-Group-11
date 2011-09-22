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

#ifndef input_reader_h__
#define input_reader_h__

#include <boost/shared_ptr.hpp>
#include <boost/date_time.hpp>
#include <boost/thread.hpp>
#include <boost/regex.hpp>
#include <iostream>
#include <sstream>
#include <cmath>
#include <cstdio>
#include <queue>
#include <deque>

#include "utility.hpp"
#include "pitch.hpp"

using namespace std;
using namespace boost;

class input_reader {
	mutable mutex input_lock;
	const static int max_location_messages = 100;
	deque <pair <long long, pair <float, float> > > xy_msg[3];
	deque <pair <long long, float> > rotation_msg[2];
	STATE_TYPE forced_state;

	static string rstrip(const string &s) {
		int end = s.size() - 1;
		while(end >= 0 && s[end] <= 32)
			--end;
		return string(s.begin(), s.begin() + (end + 1));
	}

public:
	input_reader(): forced_state(PLAY) {}

	void work() {
		const string time_format = "([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\\.([0-9]+)"; // 7 groups
		const string real_format = "-?[0-9]+(\\.[0-9]+)?([eE]-?[0-9]+)?"; // # 2 groups
		const regex vision_xy("^/vision/xy\\s+(us|ball|enemy)\\s+(" + real_format + ")\\s+(" + real_format + ")\\s+(" + time_format + ")$");
		const regex vision_rotation("^/vision/rotation\\s+(us|enemy)\\s+(" + real_format + ")\\s+(" + time_format + ")$");
		const regex forced_state_format("^/general/state/(play|wait|kick_penalty|defend_penalty)$");

		float x, y, rotation;
		OBJECT_TYPE type;
		string s;

		while(true) {
			getline(cin, s);
			s = rstrip(s);
			match_results <string::const_iterator> matches; 
			string::const_iterator start = s.begin(), end = s.end();
			mutex::scoped_lock m(input_lock);

			if(regex_search(start, end, matches, vision_xy, match_default)) {
				type = (matches[1] == "us"? US: matches[1] == "ball"? BALL: ENEMY);
				sscanf(matches[2].str().c_str(), "%f", &x);
				sscanf(matches[5].str().c_str(), "%f", &y);
				// TODO: use the actual frame time (need to know the system clock difference first)
				xy_msg[type].push_back(make_pair(now_in_nanoseconds(), make_pair(x, y)));

				if(xy_msg[type].size() > max_location_messages)
					xy_msg[type].pop_front();
				continue;
			} else if(regex_search(start, end, matches, vision_rotation, match_default)) {
				type = (matches[1] == "us"? US: ENEMY);
				sscanf(matches[2].str().c_str(), "%f", &rotation);
				// TODO: use the actual frame time (need to know the system clock difference first)
				rotation_msg[type].push_back(make_pair(now_in_nanoseconds(), rotation));

				if(rotation_msg[type].size() > max_location_messages)
					rotation_msg[type].pop_front();
				continue;
			} else if(regex_search(start, end, matches, forced_state_format, match_default)) {
				if(matches[1] == "play")
					forced_state = PLAY;
				else if(matches[1] == "wait")
					forced_state = WAIT;
				else if(matches[1] == "kick_penalty")
					forced_state = KICK_PENALTY;
				else if(matches[1] == "defend_penalty")
					forced_state = DEFEND_PENALTY;
				continue;
			} else if(s == "/central/exit") {
				cout << "/general/exiting obeying exit message" << endl;
				exit(0);
			} else if(s == "") {
				cout << "/general/exiting received empty message" << endl;
				exit(0);
			}
		}
	}

	bool have_xy_message(const OBJECT_TYPE type) const {
		mutex::scoped_lock m(input_lock);
		return !xy_msg[type].empty();
	}

	pair <long long, pair <int, int> > get_last_xy_message(const OBJECT_TYPE type) const {
		mutex::scoped_lock m(input_lock);
		return make_pair(xy_msg[type].back().first, make_pair(scale(xy_msg[type].back().second.first), scale(xy_msg[type].back().second.second)));
	}

	bool have_rotation_message(const OBJECT_TYPE type) const {
		mutex::scoped_lock m(input_lock);
		return !rotation_msg[type].empty();
	}

	pair <long long, float> get_last_rotation_message(const OBJECT_TYPE type) const {
		mutex::scoped_lock m(input_lock);
		return rotation_msg[type].back();
	}

	object* get_ball() const {
		if(!have_xy_message(BALL))
			return 0;
		mutex::scoped_lock m(input_lock);
		return new object(xy_msg[BALL]);
	}

	robot* get_robot(const OBJECT_TYPE type) const {
		if(!have_xy_message(type) || !have_rotation_message(type))
			return 0;
		pair <long long, pair <int, int> > msg1 = get_last_xy_message(type);
		pair <long long, float> msg2 = get_last_rotation_message(type);
		return new robot(msg1.second.first, msg1.second.second, max(msg1.first, msg2.first), msg2.second);
	}

	STATE_TYPE get_forced_state() const {
		mutex::scoped_lock m(input_lock);
		return forced_state;
	}

	void set_forced_state(STATE_TYPE new_state) {
		mutex::scoped_lock m(input_lock);
		forced_state = new_state;
	}
};

struct input_reader_pointer {
	input_reader *reader;

	input_reader_pointer() {
		reader = new input_reader();
	}

	int operator()() {
		reader->work();
		return 0;
	}
};

#endif // input_reader_h__