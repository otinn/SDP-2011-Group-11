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

#ifndef main_planner_h__
#define main_planner_h__

#include <sstream>

#include "synchronized_print.hpp"
#include "basic_planner.hpp"
#include "input_reader.hpp"
#include "path_finder.hpp"

using namespace std;

class main_planner: public basic_planner {
	mutable vector <point> last_coords;
	mutable float last_rotation;
	mutable char last_cmd_type;
	mutable int last_state;
	mutable long long last_state_change;
	mutable bool going_to_goal;
	mutable bool caught_ball;
	mutable int goalie_x;
	mutable bool penalty_seen_ball_move;
	STATE_TYPE old_state;

public:
	main_planner(input_reader *reader): basic_planner(reader, "planner"), last_rotation(-1), last_state(-1), last_state_change(0), going_to_goal(false), old_state(WAIT), last_cmd_type('-'), caught_ball(false), goalie_x(scale(9)), penalty_seen_ball_move(false) {}

private:
	void set_data(sptr<object> ball, sptr<robot> us, sptr<robot> enemy, STATE_TYPE forced_state) {
		old_state = this->forced_state;
		basic_planner::set_data(ball, us, enemy, forced_state);
	}

	void send_cmd(const vector <point> &coords, const float rotation, bool allow_reversing) const {
		if(last_coords == coords && fabs(last_rotation - rotation) < 1e-3 && last_cmd_type == 'm')
			return;
		last_coords = coords;
		last_rotation = rotation;
		last_cmd_type = 'm';

		ostringstream stream;
		stream << "/planner/move" << (allow_reversing? "_rev": "") << " " << coords.size();

		for(int i = 0; i < coords.size(); ++i)
			stream << " " << reverse_scale(coords[i].x) << " " << reverse_scale(coords[i].y);
		if(fabs(rotation + 1) < 1e-3)
			stream << " not_important";
		else
			stream << " " << rotation;

		cout << stream.str() << endl;
	}

	void move_to_location(int x, int y, float rotation, bool push_ball, bool allow_reversing) const {
		path_finder finder(ball, us, enemy, push_ball, true, 0.0f);
		if(us && us->known()) {
			finder.find_paths(*us);
			if(finder.reachable(x, y))
				send_cmd(finder.get_path(*us, x, y), rotation, allow_reversing);
			else
				send_cmd(vector <point>(1, point(x, y)), rotation, allow_reversing);
		}
	}

	void move_to_location_extra(int x, int y, int mid_x, int mid_y, float rotation, bool push_ball, bool allow_reversing) const {
		vector <point> path;
		path.push_back(point(mid_x, mid_y));
		path.push_back(point(x, y));
		send_cmd(path, rotation, allow_reversing);
	}

	void stop() const {
		if(last_cmd_type == 's')
			return;
		last_cmd_type = 's';

		cout << "/planner/move 0 not_important" << endl;
	}

	bool run_to_goal(bool ram_enemy) {
		const static Line line(Point(pitch_width, 0), Point(pitch_width, pitch_height));
		const static float safety = 3 * scale_factor;
		const float rotation_goal_lower = -atan2(float(us->x - pitch_width), float(us->y - min_goal_y + robot_width / 4));
		const float rotation_goal_upper = -atan2(float(us->x - pitch_width), float(us->y - max_goal_y - robot_width / 4));
		const float difference = rotation_goal_lower - rotation_goal_upper;

		obstacle_collection obstacles(0, enemy);
		CGAL::Object result;
		Point p;
		vector <pair <double, pair <double, point> > > good;

		for(int i = 0; i < 50; ++i) {
			float rotation = normalize_rotation(rotation_goal_upper + i * difference / 49);
			Ray robot_ray(Point(us->x, us->y), Vector(sin(rotation), cos(rotation)));
			Ray ball_ray(Point(ball->x, ball->y), Vector(sin(rotation), cos(rotation)));
			double ball_dist, robot_dist, dist_to_goal_center = 1e10;

			// would the ball get to the goal?
			result = intersection(line, ball_ray);
			if(CGAL::assign(p, result)) {
				if(p.y() < min_goal_y - ball_radius || p.y() > max_goal_y + ball_radius)
					goto not_suitable;
				dist_to_goal_center = fabs(pitch_height / 2 - p.y());
				if(euclidean_distance(pitch_width, min_goal_y, p.x(), p.y()) < ball_radius)
					goto not_suitable;
				if(euclidean_distance(pitch_width, max_goal_y, p.x(), p.y()) < ball_radius)
					goto not_suitable;
				ball_dist = euclidean_distance(ball->x, ball->y, p.x(), p.y());
			} else
				goto not_suitable;

			if(!ram_enemy) {
				// would the robot get to the goal?
				result = intersection(line, robot_ray);
				if(CGAL::assign(p, result)) {
					if(p.y() <= min_goal_y - robot_width / 2 || p.y() >= max_goal_y + robot_width / 2)
						goto not_suitable;
					if(euclidean_distance(pitch_width, min_goal_y, p.x(), p.y()) <= robot_width / 2)
						goto not_suitable;
					if(euclidean_distance(pitch_width, max_goal_y, p.x(), p.y()) <= robot_width / 2)
						goto not_suitable;
					robot_dist = euclidean_distance(us->x, us->y, p.x(), p.y());
					if(ball_dist + robot_height / 2 > robot_dist)
						goto not_suitable;
				} else
					goto not_suitable;
			}

			{
				// p contains the middle point of the robot in the goal
				Segment s(Point(us->x, us->y), p);

				// would the enemy be in the way?
				if(ram_enemy) {
					if(enemy && !obstacles.far_enough(s, float(scale(6))))
						goto not_suitable;
				} else {
					if(enemy && !obstacles.far_enough(s, robot_height / 2 + safety))
						goto not_suitable;
				}

				// can we actually catch the ball?
				// TODO: change back to a more permissive constant once the vision or the movement gets better
				if(point_distance(s, Point(ball->x, ball->y)) > robot_width / 3)
					goto not_suitable;

				// life is good
				good.push_back(make_pair(dist_to_goal_center, make_pair(normalize_rotation(rotation), point(int(floor(p.x())), int(floor(p.y()))))));
			}
not_suitable:;
		}

		if(good.empty())
			return false;
		pair <double, pair <double, point> > res = *min_element(good.begin(), good.end());
		send_cmd(vector <point>(1, res.second.second), res.second.first, us->x >= scale(180));
		return true;
	}

	bool two_point_run(bool straight_lines) {
		if(!ball || !ball->known() || !us || !us->known() || (straight_lines && ball->x - scale(5) < us->x))
			return false;

		const static Line line(Point(pitch_width, 0), Point(pitch_width, pitch_height));
		const static float safety = 3 * scale_factor;
		const float rotation_goal_lower = -atan2(float(us->x - pitch_width), float(us->y - min_goal_y + robot_width / 4));
		const float rotation_goal_upper = -atan2(float(us->x - pitch_width), float(us->y - max_goal_y - robot_width / 4));
		const float difference = rotation_goal_lower - rotation_goal_upper;

		obstacle_collection obstacles(0, enemy);
		CGAL::Object result;
		Point p;
		vector <pair <pair <double, float>, pair <point, point> > > good;

		const int NUM = 40;
		const float MID = 1.5 * pi;
		const float range = pi / 2 - 0.2;
		const int radius = scale(20);

		sptr<path_finder> distances(straight_lines? 0: new path_finder(ball, us, enemy, false, true, 0));
		if(distances)
			distances->find_paths(*us);
		
		for(int rot_num = 0; rot_num < NUM; ++rot_num)
			for(int dir = -1; dir <= 1; dir += 2) {
				const float rotation = normalize_rotation(MID - dir * rot_num * range / (NUM - 1) + pi);
				const Point entry = rotate_point(ball->x, ball->y, 0, radius, MID + dir * rot_num * range / (NUM - 1));
				const int entry_x = int(round(entry.x()));
				const int entry_y = int(round(entry.y()));
				
				if(!safe_on_pitch(entry_x, entry_y))
					continue;
				if(!straight_lines && !distances->reachable(entry_x, entry_y))
					continue;
				
				// would the enemy be in the way? (straight lines only)
				if(straight_lines && !obstacles.far_enough(Segment(*us, entry), robot_height / 2.0 + (straight_lines? 0: safety))) // this is risky on purpose
					continue;
				Ray ball_ray(Point(ball->x, ball->y), Vector(sin(rotation), cos(rotation)));
				
				// would the ball get to the goal?
				result = intersection(line, ball_ray);
				if(CGAL::assign(p, result)) {
					if(p.y() < min_goal_y - ball_radius || p.y() > max_goal_y + ball_radius)
						continue;
					if(euclidean_distance(pitch_width, min_goal_y, p.x(), p.y()) < ball_radius)
						continue;
					if(euclidean_distance(pitch_width, max_goal_y, p.x(), p.y()) < ball_radius)
						continue;
				} else
					continue;
				
				// would the robot get to the goal?
				if(p.y() <= min_goal_y - robot_width / 2 || p.y() >= max_goal_y + robot_width / 2)
					continue;
				if(euclidean_distance(pitch_width, min_goal_y, p.x(), p.y()) <= robot_width / 2)
					continue;
				if(euclidean_distance(pitch_width, max_goal_y, p.x(), p.y()) <= robot_width / 2)
					continue;
				
				// p contains the middle point of the ball/robot in the goal
				Segment s(Point(ball->x, ball->y), p);
				
				// would the enemy be in the way?
				if(enemy && !obstacles.far_enough(s, robot_height / 2 + safety))
					continue;
				
				// life is good
				const double dist_from_goal_center = fabs(pitch_height / 2 - p.y());
				const double dist_to_entry = straight_lines? euclidean_distance(us->x, us->y, entry_x, entry_y): distances->get_cost(entry_x, entry_y);
				const double value = dist_from_goal_center / 20 + dist_to_entry;
				good.push_back(make_pair(make_pair(value, normalize_rotation(rotation)), make_pair(point(int(floor(entry.x())), int(floor(entry.y()))), point(int(floor(p.x())), int(floor(p.y()))))));
			}
	
		if(good.empty())
			return false;
		pair <pair <double, float>, pair <point, point> > res = *min_element(good.begin(), good.end());
		vector <point> path;

		if(straight_lines) {
			path.push_back(res.second.first);
		} else {
			path = distances->get_path(*us, res.second.first.x, res.second.first.y);
			if(!path.empty())
				path.erase(path.begin());
		}

		path.push_back(res.second.second);
		if(point_distance(Segment(Point(path[0].x, path[0].y), Point(path[1].x, path[1].y)), *us) < robot_width / 3)
			path.erase(path.begin());
		send_cmd(path, res.first.second, us->x >= scale(180));
		return true;
	}

	float expected_time(const point &begin, const vector <point> &path, const point &end) const {
		const float speed = 15 * scale_factor; // cm/s

		if(path.empty())
			return euclidean_distance(begin.x, begin.y, end.x, end.y) / speed;
		float res = euclidean_distance(begin.x, begin.y, path[0].x, path[0].y);
		for(int i = 1; i < path.size(); ++i)
			res += euclidean_distance(path[i - 1].x, path[i - 1].y, path[i].x, path[i].y);
		res += euclidean_distance(path.back().x, path.back().y, end.x, end.y);
		return res / speed;
	}

	float max_ball_rolling_time() const {
		return 5; // seconds
	}

	void plan_play_default() {
		sptr<path_finder> from_ball, from_target, from_us;
		sptr<vector<point> > path;
		float max_time = max_ball_rolling_time(), min_time = 0, time = 0;
		sptr<point> target, ball_departure_point, start_push_point;
		sptr<object> new_ball;

		//for(int i = 0; i < 10 && max_time - min_time > 0.05; ++i) {
		time = 0;//(min_time + max_time) / 2;
		new_ball = sptr<object>(new object(int(round(ball->x + time * ball->vx)), int(round(ball->y + time * ball->vy)), ball->last_seen));
		force_into_bounds(new_ball.get());

		//cout << "time: " << time << endl;
		from_ball = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, true, false, time));
		from_ball->find_paths(*new_ball);
		target = sptr<point>(new point(from_ball->choose_destination_point_goal()));
		//cout << "target: " << *target << endl;

		from_target = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, true, false, time));
		from_target->find_paths(*target);
		ball_departure_point = sptr<point>(new point(from_target->choose_ball_departure_point()));
		//cout << "ball departure point: " << *ball_departure_point << endl;

		from_us = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, false, true, time));
		from_us->find_paths(*us);
		start_push_point = sptr<point>(new point(from_us->choose_start_push_point(*ball_departure_point)));
		//cout << "start push point: " << *start_push_point << endl;

		path = sptr<vector<point> >(new vector<point>(from_us->get_path(*us, start_push_point->x, start_push_point->y)));
		//	float time_taken = expected_time(*us, *path, *new_ball);
		//	if(time_taken < time)
		//		max_time = time;
		//	else
		//		min_time = time;
		//}

		vector <point> path2 = from_ball->get_path(*new_ball, target->x, target->y);
		path2.insert(path2.begin(), *new_ball);
		path2.insert(path2.begin(), *ball_departure_point);
		path2 = from_ball->simplify_path2(path2);
		if(euclidean_distance(us->x, us->y, new_ball->x, new_ball->y) < robot_height / 2 + scale(4))
			path2.erase(path2.begin());
		for(int i = 0; i < path2.size(); ++i)
			path->push_back(path2[i]);

		// make sure we don't try to go outside the boundaries to catch a ball going toward our goal
		for(int i = 0; i < path->size(); ++i) {
			(*path)[i].x = max((*path)[i].x, robot_height / 2 + scale(2));
		}

		// eliminate useless segments in the beginning
		while(path->size() > 1) {
			if(point_distance(Segment(Point((*path)[0]), Point((*path)[1])), Point(*us)) < scale(3))
				path->erase(path->begin());
			else
				break;
		}

		const int goal_y = (min_goal_y + max_goal_y) / 2;
		const float final_angle = atan2(float(pitch_width - target->x), float(goal_y - target->y));
		send_cmd(*path, final_angle, false);
	}

	void plan_play_default_timed() {
		sptr<path_finder> from_ball, from_target, from_us;
		sptr<vector<point> > path;
		float max_time = max_ball_rolling_time(), min_time = 0, time = 0;
		sptr<point> target, ball_departure_point, start_push_point;
		sptr<object> new_ball;

		for(int i = 0; i < 10 && max_time - min_time > 0.05; ++i) {
			time = (min_time + max_time) / 2;
			new_ball = sptr<object>(new object(int(round(ball->x + time * ball->vx)), int(round(ball->y + time * ball->vy)), ball->last_seen));
			force_into_bounds(new_ball.get());

			//cout << "time: " << time << endl;
			from_ball = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, true, false, time));
			from_ball->find_paths(*new_ball);
			target = sptr<point>(new point(from_ball->choose_destination_point_goal()));
			//cout << "target: " << *target << endl;

			from_target = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, true, false, time));
			from_target->find_paths(*target);
			ball_departure_point = sptr<point>(new point(from_target->choose_ball_departure_point()));
			//cout << "ball departure point: " << *ball_departure_point << endl;

			from_us = sptr<path_finder>(new path_finder(new_ball.get(), us, enemy, false, true, time));
			from_us->find_paths(*us);
			start_push_point = sptr<point>(new point(from_us->choose_start_push_point(*ball_departure_point)));
			//cout << "start push point: " << *start_push_point << endl;

			path = sptr<vector<point> >(new vector<point>(from_us->get_path(*us, start_push_point->x, start_push_point->y)));
				float time_taken = expected_time(*us, *path, *new_ball);
				if(time_taken < time)
					max_time = time;
				else
					min_time = time;
		}

		vector <point> path2 = from_ball->get_path(*new_ball, target->x, target->y);
		path2.insert(path2.begin(), *new_ball);
		path2.insert(path2.begin(), *ball_departure_point);
		path2 = from_ball->simplify_path2(path2);
		path2.erase(path2.begin());
		for(int i = 0; i < path2.size(); ++i)
			path->push_back(path2[i]);

		// make sure we don't try to go outside the boundaries to catch a ball going toward our goal
		for(int i = 0; i < path->size(); ++i) {
			(*path)[i].x = max((*path)[i].x, robot_height / 2 + scale(2));
		}

		// eliminate useless segments in the beginning
		while(path->size() > 1) {
			if(point_distance(Segment(Point((*path)[0]), Point((*path)[1])), Point(*us)) < scale(3))
				path->erase(path->begin());
			else
				break;
		}

		const int goal_y = (min_goal_y + max_goal_y) / 2;
		const float final_angle = atan2(float(pitch_width - target->x), float(goal_y - target->y));
		send_cmd(*path, final_angle, false);
	}

	void plan_play_old() {
		const int goal_y = (min_goal_y + max_goal_y) / 2;
		float ball_goal_angle = atan2(float(pitch_width - ball->x), float(goal_y - ball->y));
		const int extra_space = scale(23);
		int target_x = 0, target_y = 0;
		bool changed_angle = false;

		float h_min_offset = float((robot_width + 1) / 2 + scale(3));
		while(true) {
			assert(ball);
			target_x = int(round(ball->x - extra_space * sin(ball_goal_angle)));
			target_y = int(round(ball->y - extra_space * cos(ball_goal_angle)));

			if(target_y < pitch_height / 2) {
				if(target_y >= h_min_offset)
					break;
				ball_goal_angle += 0.02f;
				changed_angle = true;
			} else {
				if(target_y <= pitch_height - h_min_offset)
					break;
				ball_goal_angle -= 0.02f;
				changed_angle = true;
			}
		}
		if(changed_angle && target_y < pitch_height / 2) {
			ball_goal_angle = min(ball_goal_angle, float(pi / 2));
		} else if(changed_angle) {
			ball_goal_angle = max(ball_goal_angle, float(pi / 2));
		}

		const float dist = sqrt(float((target_x - us->x) * (target_x - us->x) + (target_y - us->y) * (target_y - us->y)));
		const float dist_ball = sqrt(float((ball->x - us->x) * (ball->x - us->x) + (ball->y - us->y) * (ball->y - us->y)));

		if(dist > scale(7.0f) && dist_ball > scale(15.0f)) {
			if(target_x < robot_height * 3 / 2) {
				going_to_goal = false;
				plan_play_default();
				return;
			}
			move_to_location(target_x, target_y, normalize_rotation(ball_goal_angle), false, true);
			going_to_goal = false;
		} else {
			if(changed_angle)
				move_to_location_extra(pitch_width - scale(30), (ball->y < pitch_height / 2? min_goal_y: max_goal_y), ball->x - robot_height / 2, target_y + (ball->y < pitch_height / 2? scale(3): -scale(3)), normalize_rotation(ball_goal_angle), true, false);
			else
				move_to_location(pitch_width, goal_y, normalize_rotation(ball_goal_angle), true, false);
			if(!going_to_goal)
				sleep_ms(400);
			going_to_goal = true;
		}
	}

	bool enemy_in_control() {
		if(!enemy || !enemy->known() || !ball || !ball->known() || !us || !us->known())
			return false;
		if(ball->vx < -20)
			return true;
		float enemy_to_ball = euclidean_distance(enemy->x, enemy->y, ball->x, ball->y);
		if(enemy_to_ball > scale(50))
			return false;
		if(ball->x - scale(5) >= enemy->x)
			return false;
		return true;
	}

	mutable Segment enemy_sides[4];
	void init_enemy_segments() const {
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

	bool enemy_in_the_way(float rotation) const {
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

	bool possible_goal(float rotation) const {
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

	float best_rotation() const {
		init_enemy_segments();
		const float RANGE = (pi - 0.4) / 2;
		const float MID = pi / 2;
		for(int i = 0; i < 50; ++i)
			for(int dir = -1; dir <= 1; dir += 2) {
				float f = MID + dir * i * RANGE / 49;
				if(possible_goal(f) && !enemy_in_the_way(f))
					return f;
			}
		return MID;
	}

	bool plan_defence() {
		if(!us || !us->known() || !enemy || !enemy->known() || !ball || !ball->known())
			return false;
		if(ball->vx <= -20)
			return false;
		
		const int x = max(scale(15), ball->x - scale(50));
		int y = ball->y;
		
		vector <point> path;
		path.push_back(point(x, y));
		path.push_back(point(ball->x - scale(12), y));

		if(point_distance(Segment(Point(path[0].x, path[0].y), Point(path[1].x, path[1].y)), *us) < robot_width / 3)
			path.erase(path.begin());
		send_cmd(path, best_rotation(), true);
		return true;
	}

	bool plan_catch_ball() {
		if(!us || !us->known() || !ball || !ball->known())
			return false;
		const float speed = sqrt(ball->vx * ball->vx + ball->vy * ball->vy);

		const int x = max(scale(15), int(round(ball->x + 3 * ball->vx)));
		int y = ball->y;
		
		path_finder paths(ball, us, enemy, false, true, 3);
		paths.find_paths(*us);
		if(!paths.reachable(x, y))
			return false;
		vector <point> path = paths.get_path(*us, x, y);
		if(!path.empty())
			path.erase(path.begin());
		send_cmd(path, best_rotation(), true);
		return true;
	}

	void plan_play() {
		if(!ball->known()) {
			if(!going_to_goal)
				stop();
			return;
		}
		going_to_goal = false;

		if(run_to_goal(false)) {
			going_to_goal = true;
			return;
		}
		
		if(enemy_in_control()) {
			if(run_to_goal(true)) {
				going_to_goal = true;
				return;
			}
			if(plan_defence())
				return;
		}

		if(ball && ball->known() && ball->vx <= -20) {
			if(plan_catch_ball())
				return;
			else
				plan_play_default_timed();
		}

		if(two_point_run(true))
			return;
		if(two_point_run(false))
			return;
		
		Segment s(Point(ball->x, ball->y), Point(pitch_width, pitch_height / 2));
		if(enemy && enemy->known())
			if(point_distance(s, *enemy) < robot_height / 1.5) {
				plan_play_default();
				return;
			}

		plan_play_old();
	}

	bool penalty_taken() const {
		if(penalty_seen_ball_move)
			return true;
		if(!ball || !ball->known())
			return false;
		if(sqrt(ball->vx * ball->vx + ball->vy * ball->vy) > 3 || (enemy && enemy->known() && ball->x + scale(20) < enemy->x))
			penalty_seen_ball_move = true;
		return penalty_seen_ball_move;
	}

	void plan_defend_penalty() {
		if(old_state != DEFEND_PENALTY) {
			goalie_x = max(scale(9), us->x);
			penalty_seen_ball_move = false;
		}
		
		if(enemy && enemy->known() && !penalty_taken()) {
			float penalty_angle = enemy->rotation + pi / 2;
			float goal_intersection_y = tan(penalty_angle) * (enemy->x - robot_width / 2) + enemy->y;
			
			// Within goal line?
			goal_intersection_y = max(goal_intersection_y, float(min_goal_y + robot_height - scale(2)));
			goal_intersection_y = min(goal_intersection_y, float(max_goal_y - robot_height + scale(2)));
			send_cmd(vector <point>(1, point(goalie_x, int(round(goal_intersection_y)))), 0, true);
		} else if(penalty_taken() && (ball && ball->known() && ball->vx < -10)) {
			Segment s(Point(goalie_x, 0), Point(goalie_x, pitch_height));
			Ray ray(*ball, Vector(ball->vx, ball->vy));

			// the ball is already very near the goal or headed for the wall
			if(!do_intersect(s, ray)) {
				if(ball->vy < 0) {
					// bounce from the bottom
					send_cmd(vector <point>(1, point(goalie_x, min_goal_y + robot_height - scale(3))), 0, true);
				} else {
					// bounce from the top
					send_cmd(vector <point>(1, point(goalie_x, max_goal_y - robot_height + scale(3))), 0, true);
				}
				return;
			}
			
			CGAL::Object result = intersection(s, ray);
			Point p;
			CGAL::assign(p, result);
			float goal_intersection_y = p.y();
			// Within goal line?
			goal_intersection_y = max(goal_intersection_y, float(min_goal_y + robot_height));
			goal_intersection_y = min(goal_intersection_y, float(max_goal_y - robot_height));
			send_cmd(vector<point>(1, point(goalie_x, int(round(goal_intersection_y)))), 0, true);
		} else {
			send_cmd(vector <point>(1, point(goalie_x, pitch_height / 2)), 0, true);
		}
	}

	int last_decision;
	double last_rotation_decision;

	void plan_kick_penalty() {
		if(old_state != forced_state)
			last_decision = -1;

		if(last_decision == -1) {
			sleep_ms(300);
			last_decision = rand() % 2;
			float want;

			if(last_decision == 0) {
				want = 0.5 * pi - 0.25;
			} else {
				want = 0.5 * pi + 0.25;
			}
			cout << "/planner/move 0 " << want << endl;
			long now = now_in_nanoseconds();
			while(us && us->known() && fabs(us->rotation - want) > 0.05 && now_in_nanoseconds() - now <= seconds_in_nanoseconds(0.6f))
				sleep_ms(10);
			sleep_ms(200);
			cout << "/planner/kick" << endl;
			last_decision = -2;
		}
	}

public:
	void plan() {
		if(!us || !ball || ball_in_goal() || !us->known() || forced_state == WAIT) {
			stop();
			return;
		}

		if(old_state != forced_state) {
			if(forced_state == DEFEND_PENALTY || forced_state == KICK_PENALTY)
				stop();
			caught_ball = false;
			cout << "/planner/lower_kicker" << endl;
		}

		if(forced_state == PLAY) {
			plan_play();
		} else if(forced_state == DEFEND_PENALTY)
			plan_defend_penalty();
		else
			plan_kick_penalty();
	}
};

#endif // main_planner_h__
