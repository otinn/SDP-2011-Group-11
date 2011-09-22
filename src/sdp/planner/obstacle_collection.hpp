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

#ifndef obstacle_collection_h__
#define obstacle_collection_h__

#include "geometry.hpp"
#include "pitch.hpp"

class obstacle_collection {
	Segment enemy_sides[4];
	object *ball;
	robot *enemy;

public:
	obstacle_collection(object *ball, robot *enemy): ball(ball), enemy(enemy) {
		if(enemy) {
			const Point points[] = {
				rotate_point(enemy->x, enemy->y, -robot_width / 2, -robot_height / 2, enemy->rotation),
				rotate_point(enemy->x, enemy->y, robot_width / 2, -robot_height / 2, enemy->rotation),
				rotate_point(enemy->x, enemy->y, robot_width / 2, robot_height / 2, enemy->rotation),
				rotate_point(enemy->x, enemy->y, -robot_width / 2, robot_height / 2, enemy->rotation)
			};
			for(int i = 0; i < 4; ++i)
				enemy_sides[i] = Segment(points[i], points[(i + 1) % 4]);
		}
	}

	bool far_enough(const Segment &segment, const float min_dist) const {
		if(ball) {
			if(point_distance(segment, Point(ball->x, ball->y)) - ball_radius < min_dist)
				return false;
		}
		if(enemy) {
			for(int i = 0; i < 4; ++i)
				if(segment_distance(segment, enemy_sides[i]) < min_dist)
					return false;
		}
		return true;
	}

	const Segment& get_enemy_side(int id) const {
		return enemy_sides[id];
	}
};

#endif // obstacle_collection_h__