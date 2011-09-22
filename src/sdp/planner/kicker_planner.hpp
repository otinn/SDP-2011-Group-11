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

#ifndef kicker_planner_h__
#define kicker_planner_h__

#include <CGAL/Polygon_2.h>

#include "synchronized_print.hpp"
#include "basic_planner.hpp"
#include "geometry.hpp"
#include "utility.hpp"
#include "pitch.hpp"

class kicker_planner: public basic_planner {
	bool had_ball;
	sptr<robot> old_us;

	void set_data(sptr<object> ball, sptr<robot> us, sptr<robot> enemy, STATE_TYPE forced_state) {
		old_us = us;
		basic_planner::set_data(ball, us, enemy, forced_state);
	}

	void kick() const {
		long long now = now_in_nanoseconds();
		cout << "/planner/kick" << endl;
		sleep_ms(800);
	}

	Segment enemy_sides[4];
	void init_enemy_segments() {
		// TODO: the ball might also bounce off the enemy in the right direction thus not being a problem after all
		static sptr<robot> last_enemy;
		if(!enemy || (last_enemy && enemy->x == last_enemy->x && enemy->y == last_enemy->y))
			return;
		last_enemy = sptr<robot>(new robot(*enemy));

		const int safety = scale(3) + ball_radius;
		Point points[] = {rotate_point(enemy->x, enemy->y, -robot_width / 2 - safety, -robot_height / 2 - safety, enemy->rotation),
			rotate_point(enemy->x, enemy->y, robot_width / 2 + safety, -robot_height / 2 - safety, enemy->rotation),
			rotate_point(enemy->x, enemy->y, robot_width / 2 + safety, robot_height / 2 + safety, enemy->rotation),
			rotate_point(enemy->x, enemy->y, -robot_width / 2 - safety, robot_height / 2 + safety, enemy->rotation)};
		for(int i = 0; i < 4; ++i)
			enemy_sides[i] = Segment(points[i], points[(i + 1) % 4]);
	}

	bool enemy_in_the_way(float rotation) {
		if(!enemy)
			return false;
		Ray ray(Point(ball->x, ball->y), Vector(sin(rotation), cos(rotation)));
		for(int i = 0; i < 4; ++i) {
			if(do_intersect(enemy_sides[i], ray))
				return true;
		}
		return false;
	}

	bool ball_in_kicker_area(float rotation) {
		Point points[] = {rotate_point(us->x, us->y, -robot_width / 2, -robot_height / 2, rotation), rotate_point(us->x, us->y, robot_width / 2, -robot_height / 2, rotation),
			rotate_point(us->x, us->y, robot_width / 2, robot_height / 2 + kicker_reach, rotation), rotate_point(us->x, us->y, -robot_width / 2, robot_height / 2 + kicker_reach, rotation)};
		return CGAL::bounded_side_2(points, points + 4, Point(ball->x, ball->y), Kernel()) != CGAL::ON_UNBOUNDED_SIDE;
	}

	bool possible_goal(float rotation) {
		const static Line line(Point(pitch_width, 0), Point(pitch_width, pitch_height));
		Ray ray(Point(ball->x, ball->y), Vector(sin(rotation), cos(rotation)));

		CGAL::Object result = intersection(line, ray);
		Point p;
		if(CGAL::assign(p, result)) {
			if(p.y() < min_goal_y - ball_radius || p.y() > max_goal_y + ball_radius)
				return false;
			if(euclidean_distance(pitch_width, min_goal_y, p.x(), p.y()) < ball_radius)
				return false;
			if(euclidean_distance(pitch_width, max_goal_y, p.x(), p.y()) < ball_radius)
				return false;
			return true;
		}
		return false;
	}

	bool better_to_kick() {
		if(!enemy || !enemy->known() || !ball || !ball->known() || !us || !us->known())
			return false;
		float enemy_to_ball = euclidean_distance(enemy->x, enemy->y, ball->x, ball->y);
		if(enemy_to_ball > scale(50))
			return false;
		if(euclidean_distance(us->x, us->y, ball->x, ball->y) > scale(20))
			return false;

		float error = 0.03f;
		float dir = 0;
		if(old_us) {
			double difference = normalize_rotation(us->rotation - old_us->rotation);
			difference = std::min(difference, 2 * pi - difference);
			error += difference / 2;
			dir = us->rotation - old_us->rotation;
		}

		int good = 0;
		float a = us->rotation - error + dir;
		float b = us->rotation + error + dir;
		init_enemy_segments();
		for(int i = 0; i < 50; ++i) {
			float f = a + (b - a) * i / 49;
			if(f < 0.2 || f > pi - 0.2)
				continue;
			if((us->rotation > 0.2 && us->rotation < pi - 0.2) && (enemy_to_ball <= scale(30) || !enemy_in_the_way(f)))
				++good;
		}

		if(good >= 2)
			return true;
		return false;
	}

public:
	kicker_planner(input_reader *reader): basic_planner(reader, "kicker planner"), had_ball(false) {}

	void plan() {
		if(!us || !ball || ball_in_goal() || !us->known() || forced_state == WAIT) {
			return;
		} else if(!ball->known()) {
			if(had_ball)
				kick();
			had_ball = false;
			return;
		} else {
			had_ball = true;
		}
		//cout << "ball: " << *ball << endl;

		float error = 0.03f;
		float dir = 0;
		if(old_us) {
			double difference = normalize_rotation(us->rotation - old_us->rotation);
			difference = std::min(difference, 2 * pi - difference);
			error += difference / 2;
			dir = us->rotation - old_us->rotation;
		}

		int good = 0;
		float a = us->rotation - error + dir;
		float b = us->rotation + error + dir;
		init_enemy_segments();
		for(int i = 0; i < 50; ++i) {
			float f = a + (b - a) * i / 49;
			if(ball_in_kicker_area(f) && possible_goal(f) && !enemy_in_the_way(f))
				++good;
		}

		if(good > 1)
			cout << "/planner/info/kicker_prob " << good / 50.0 << endl;
		if(good >= 30)
			kick();
		else if(better_to_kick()) {
			cout << "/planner/info/better_to_kick" << endl;
			kick();
		}
	}
};

#endif // kicker_planner_h__