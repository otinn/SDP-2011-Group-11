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

#ifndef pitch_h__
#define pitch_h__

#include <deque>
#include <cmath>

#include "utility.hpp"
#include "geometry.hpp"

using namespace std;

// pitch
const float scale_factor = 1;
const int pitch_height = int(ceil(122 * scale_factor));
const int pitch_width = int(ceil(244 * scale_factor));
const int ball_radius = int(ceil(2.5 * scale_factor));
const float goal_error = 1.5 * scale_factor;
const float goal_height = 60 * scale_factor - goal_error;
const int min_goal_y = int(ceil((pitch_height - goal_height) / 2.0 + ball_radius));
const int max_goal_y = int(floor((pitch_height - goal_height) / 2.0 + goal_height - ball_radius));
const int robot_height = int(ceil(20 * scale_factor));
const int robot_width = int(ceil(18 * scale_factor));
const int kicker_reach = int(ceil(3 * scale_factor)) + ball_radius;

const int scale(const float f) {
	return int(ceil(f * scale_factor));
}

const float reverse_scale(int x) {
	return x / scale_factor;
}

const float normalize_rotation(float rotation) {
	while(rotation < 0)
		rotation += 2 * pi;
	while(rotation > 2 * pi)
		rotation -= 2 * pi;
	return max(0.0f, rotation);
}

bool point_on_pitch(int x, int y) {
	return 0 <= x && x < pitch_width && 0 <= y && y < pitch_height;
}

bool safe_on_pitch(int x, int y) {
	const int safety_const = robot_height / 2 + scale(1);
	return safety_const <= x && x < pitch_width - safety_const && safety_const <= y && y < pitch_height - safety_const;
}

struct point {
	int x, y;

	point(int x, int y): x(x), y(y) {}

	friend bool operator==(const point &a, const point &b) {
		return a.x == b.x && a.y == b.y;
	}

	friend bool operator!=(const point &a, const point &b) {
		return !(a == b);
	}

	friend bool operator<(const point &a, const point &b) {
		if(a.y != b.y)
			return a.y < b.y;
		return a.x < b.x;
	}

	friend ostream& operator<<(ostream& stream, const point &obj) {
		stream << reverse_scale(obj.x) << ", " << reverse_scale(obj.y);
		return stream;
	}

	operator Point() {
		return Point(x, y);
	}
};

struct object: public point {
	const long long last_seen;
	float vx, vy;

	object(const int x, const int y, const long long last_seen): point(x, y), last_seen(last_seen), vx(0), vy(0) {}

	object(const deque <pair <long long, pair <float, float> > > &xy_msg): point(scale(xy_msg.back().second.first), scale(xy_msg.back().second.second)), last_seen(xy_msg.back().first) {
		float last_x = xy_msg.back().second.first;
		float last_y = xy_msg.back().second.second;
		vx = vy = 0;

		if(xy_msg.back().first + seconds_in_nanoseconds(2) >= now_in_nanoseconds()) {
			for(int k = xy_msg.size() - 2; k >= 0 && last_seen - xy_msg[k].first < seconds_in_nanoseconds(0.3f); --k) {
				float x = xy_msg[k].second.first;
				float y = xy_msg[k].second.second;
				float d = euclidean_distance(last_x, last_y, x, y);
				if((d >= 2) || (last_seen - xy_msg[k].first > seconds_in_nanoseconds(0.2f) && d >= 1)) {
					vx = (last_x - x) / ((last_seen - xy_msg[k].first) / 1e9);
					vy = (last_y - y) / ((last_seen - xy_msg[k].first) / 1e9);
					break;
				}
			}
		}
	}

	bool known() const {
		return now_in_nanoseconds() - last_seen < seconds_in_nanoseconds(15);
	}

	friend bool operator==(const object &a, const object &b) {
		return a.x == b.x && a.y == b.y;
	}

	friend bool operator!=(const object &a, const object &b) {
		return !(a == b);
	}

	friend ostream& operator<<(ostream& stream, const object &obj) {
		stream << point(obj) << " v(" << obj.vx << ", " << obj.vy << "), (" << obj.last_seen << ")";
		return stream;
	}
};

struct robot: public object {
	const float rotation;

	robot(const int x, const int y, const long long last_seen, const float rotation): object(x, y, last_seen), rotation(normalize_rotation(rotation)) {}

	friend bool operator==(const robot &a, const robot &b) {
		return a.x == b.x && a.y == b.y && fabs(a.rotation - b.rotation) < 1e-3;
	}

	friend bool operator!=(const robot &a, const robot &b) {
		return !(a == b);
	}

	friend ostream& operator<<(ostream& stream, const robot &obj) {
		stream << point(obj) << " " << obj.rotation << "(" << obj.last_seen << ")";
		return stream;
	}

	bool known() const {
		return now_in_nanoseconds() - last_seen < seconds_in_nanoseconds(5);
	}
};

#endif // pitch_h__