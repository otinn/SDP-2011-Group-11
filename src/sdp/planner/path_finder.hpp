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

#ifndef path_finder_h__
#define path_finder_h__

#include <CGAL/Polygon_2.h>
#include <sstream>
#include <vector>
#include <cmath>
#include <queue>

#include "obstacle_collection.hpp"
#include "geometry.hpp"
#include "utility.hpp"
#include "pitch.hpp"

using namespace std;

class path_finder {
	const static int move[8][2];
	const static float INF;

	const object * const ball;
	const robot * const us;
	const robot * const enemy;
	const bool push_ball;
	vector <vector <float> > cost_multiplier;
	vector <vector <float> > dist;
	const obstacle_collection obstacles;

	void draw_ball(const int middle_x, const int middle_y, const int impassable, const int radius, const float weight) {
		const int r_sq = radius * radius;
		const int impassable_sq = impassable * impassable;
		// discourage moving near the obstacle
		for(int y = -radius; y <= radius; ++y) {
			const int real_y = y + middle_y;
			if(real_y < 0 || real_y >= pitch_height)
				continue;
			for(int x = -radius; x <= radius; ++x) {
				const int real_x = x + middle_x;
				if(real_x < 0 || real_x >= pitch_width)
					continue;
				const int d = y * y + x * x;
				if(impassable && d <= impassable_sq)
					cost_multiplier[real_y][real_x] = INF * 2;
				else if(d <= r_sq)
					cost_multiplier[real_y][real_x] += weight * (sqrt(double(radius - abs(x)) * (radius - abs(x)) + (radius - abs(y)) * (radius - abs(y)))) / scale_factor;
			}
		}
	}

	void draw_enemy(const int radius, const int weight) {
		const int r_sq = radius * radius;
		const Point points[] = {
			rotate_point(enemy->x, enemy->y, -robot_width / 2 - scale(1), -robot_height / 2 - scale(1), enemy->rotation),
			rotate_point(enemy->x, enemy->y, robot_width / 2 + scale(1), -robot_height / 2 - scale(1), enemy->rotation),
			rotate_point(enemy->x, enemy->y, robot_width / 2 + scale(1), robot_height / 2 + scale(1), enemy->rotation),
			rotate_point(enemy->x, enemy->y, -robot_width / 2 - scale(1), robot_height / 2 + scale(1), enemy->rotation)
		};
		// discourage moving near the obstacle
		for(int y = -radius; y <= radius; ++y) {
			const int real_y = y + enemy->y;
			if(real_y < 0 || real_y >= pitch_height)
				continue;
			for(int x = -radius; x <= radius; ++x) {
				const int real_x = x + enemy->x;
				if(real_x < 0 || real_x >= pitch_width)
					continue;
				const int d = y * y + x * x;
				if(CGAL::bounded_side_2(points, points + 4, Point(real_x, real_y), Kernel()) != CGAL::ON_UNBOUNDED_SIDE)
					cost_multiplier[real_y][real_x] = INF * 2;
				else if(d <= r_sq)
					cost_multiplier[real_y][real_x] += weight * (sqrt(double(radius - abs(x)) * (radius - abs(x)) + (radius - abs(y)) * (radius - abs(y)))) / scale_factor;
			}
		}
	}

	void draw_walls() {
		const int safety_const = scale(2);
		const int impassable = (robot_width + 1) / 2 + safety_const;

		for(int y = 0; y < pitch_height; ++y)
			for(int x = 0; x < pitch_width; ++x) {
				int min_dist = min(min(y, pitch_height - y - 1), min(x, pitch_width - x - 1));
				if(min_dist <= impassable)
					cost_multiplier[y][x] = INF * 2;
				else {
					if(x >= pitch_width - robot_width)
						cost_multiplier[y][x] += abs((min_goal_y + max_goal_y) / 2 - y) / 10.0 + min_dist / 30.0;
					else
						cost_multiplier[y][x] += float(pitch_height) / (min_dist + 1) / 100;
				}
			}
	}

	vector <point> simplify_path(const vector <point> path) const {
		if(path.size() < 2)
			return path;
		vector <point> res(1, path[0]);
		int dx = path[1].x - path[0].x;
		int dy = path[1].y - path[0].y;
		for(int i = 1, nx, ny; i < path.size(); ++i) {
			nx = path[i].x - path[i - 1].x;
			ny = path[i].y - path[i - 1].y;
			if(nx == dx && ny == dy)
				res.pop_back();
			else {
				dx = nx;
				dy = ny;
			}
			res.push_back(path[i - 1]);
		}
		return res;
	}

public:
	path_finder(object *ball, robot * us, robot *enemy, bool push_ball, bool impassable_ball, const float time): ball(ball), us(us), enemy(enemy), push_ball(push_ball), obstacles(ball, enemy) {
		cost_multiplier.resize(pitch_height, vector <float>(pitch_width, 1));
		const int safety_const = scale(5);
		const double robot_radius = sqrt(double(robot_width * robot_width / 4 + robot_height * robot_height / 4));

		if(enemy)
			draw_enemy(int(ceil(2 * robot_radius + safety_const)), 20);
		if(ball && !push_ball) {
			int parts = int(ceil(time * 10 + 1e-5)); // roughly 0.1 second intervals
			for(int i = 0; i <= parts; ++i) {
				const float t = i * time / parts;
				const int x = int(round(ball->x + t * ball->vx));
				const int y = int(round(ball->y + t * ball->vy));
				if(impassable_ball)
					draw_ball(x, y, int(ceil(ball_radius + robot_radius)), int(floor(double(robot_radius + ball_radius + safety_const))), 30);
				else
					draw_ball(x, y, 0, int(floor(double(robot_radius + ball_radius + safety_const))), 30);
			}
		}
		draw_walls();
	}

	vector <point> simplify_path2(const vector <point> path) const {
		if(path.size() < 2)
			return path;
		// TODO: make this more permissive once the movement or the vision get better
		const float safety = 12 * scale_factor;

		vector <point> res(1, path[0]);
		res.push_back(path[1]);
		for(int i = 2; i < path.size(); ++i) {
			const Segment s(Point(res[res.size() - 2].x, res[res.size() - 2].y), Point(path[i].x, path[i].y));
			if(obstacles.far_enough(s, robot_height / 2.0 + safety))
				res.pop_back();
			res.push_back(path[i]);
		}
		return res;
	}

	void find_paths(point from) {
		dist.clear();
		dist.resize(pitch_height, vector <float>(pitch_width, INF * 2));

		priority_queue <pair <float, point> > q;
		dist[from.y][from.x] = 0;
		q.push(make_pair(0.0f, from));
		while(!q.empty()) {
			const float dd = -q.top().first;
			const point p = q.top().second;
			q.pop();
			for(int k = 0; k < 8; ++k) {
				const int x = p.x + move[k][0];
				const int y = p.y + move[k][1];
				if(cost_multiplier[y][x] >= INF)
					continue;
				const float d = (move[k][0] && move[k][1]? 1.4142135: 1) * cost_multiplier[y][x];
				if(dist[y][x] >= INF || dist[y][x] > dd + d + 1e-4) {
					dist[y][x] = dd + d;
					q.push(make_pair(-(dd + d), point(x, y)));
				}
			}
		}

	}

	bool reachable(const int target_x, const int target_y) const {
		if(!point_on_pitch(target_x, target_y))
			return false;
		if(dist[target_y][target_x] >= INF)
			return false;
		return true;
	}

	float get_cost(const int target_x, const int target_y) const {
		if(!reachable(target_x, target_y))
			return INF;
		return dist[target_y][target_x];
	}

	vector <point> get_path(point from, const int target_x, const int target_y) const {
		//cout << from << " -> " << target_x << ", " << target_y << " " << dist[target_y][target_x] << endl;
		if(!reachable(target_x, target_y))
			return vector <point>();

		vector <point> path(1, point(target_x, target_y));
		while(path.back().x != from.x || path.back().y != from.y) {
			int next_x = -1, next_y = -1;
			float next_d = dist[path.back().y][path.back().x];
			for(int k = 0; k < 8; ++k) {
				const int x = path.back().x + move[k][0];
				const int y = path.back().y + move[k][1];
				if(dist[y][x] >= INF)
					continue;
				if(next_d > dist[y][x] + 1e-5) {
					next_x = x;
					next_y = y;
					next_d = dist[y][x];
				}
			}
			path.push_back(point(next_x, next_y));
		}
		path.push_back(from);

		reverse(path.begin(), path.end());
		path = simplify_path(path);
		path = simplify_path2(path);
		path.erase(path.begin());
		//cout << "res: " << path[0] << " " << path.back() << endl;
		return path;
	}

	friend ostream& operator<<(ostream& stream, const path_finder &obj) {
		stream << "map cost" << endl;
		for(int i = obj.dist.size() - 1; i >= 0; --i) {
			for(int j = 0; j < obj.cost_multiplier[i].size(); ++j) {
				if(obj.cost_multiplier[i][j] >= INF)
					stream << '#';
				else
					stream << char('0' + log(obj.cost_multiplier[i][j] + 1));
			}
			stream << endl;
		}
		stream << "map dist" << endl;
		for(int i = obj.dist.size() - 1; i >= 0; --i) {
			for(int j = 0; j < obj.dist[i].size(); ++j) {
				if(obj.dist[i][j] >= INF)
					stream << '#';
				else
					stream << char('0' + log(obj.dist[i][j] + 1));
			}
			stream << endl;
		}
		stream << "cost_multiplier" << endl;
		for(int i = obj.cost_multiplier.size() - 1; i >= 0; --i) {
			for(int j = 0; j < obj.cost_multiplier[i].size(); ++j)
				stream << obj.cost_multiplier[i][j] << " ";
			stream << endl;
		}
		stream << "dist" << endl;
		for(int i = obj.dist.size() - 1; i >= 0; --i) {
			for(int j = 0; j < obj.dist[i].size(); ++j)
				stream << obj.dist[i][j] << " ";
			stream << endl;
		}
		return stream;
	}

	// chooses the point where the robot should be to score by pushing the ball; the search must have begun from the ball
	point choose_destination_point_goal() const {
		for(int x = pitch_width - 1; x >= 0; --x) {
			int res_y = pitch_height / 2;
			float min_dist = 2 * INF;
			for(int y = 0; y < pitch_height; ++y)
				if(min_dist > dist[y][x]) {
					min_dist = dist[y][x];
					res_y = y;
				}
				if(min_dist < INF) {
					//cout << "chosen value: " << min_dist << endl;
					// direct the point a bit more to the centre (needed because of the huge robot radius)
					//int d_y = int(round((pitch_height / 2 - res_y) * 0.8));
					return point(x, res_y);
				}
		}
		// we must have returned a point by now so this should never happen
		return point(pitch_width - 2, pitch_height / 2);
	}

	// chooses the point through which the ball should be pushed towards the goal; the search must have begun from the target
	// the function takes into account the departure and the arrival point with constant weights
	point choose_ball_departure_point() const {
		int departure_radius = ball_radius + scale(15);
		int arrival_radius = scale(23);
		int res_x = ball->x, res_y = ball->y;
		float min_dist = 10 * INF, d;

		const int NUM_CHOICES = 300;
		for(int i = 0; i < 500; ++i) {
			Point p1 = rotate_point(ball->x, ball->y, departure_radius, 0, i * 2 * pi / NUM_CHOICES);
			Point p2 = rotate_point(ball->x, ball->y, arrival_radius, 0, (i + NUM_CHOICES / 2) * 2 * pi / NUM_CHOICES);
			int x1 = int(round(p1.x()));
			int y1 = int(round(p1.y()));
			int x2 = int(round(p2.x()));
			int y2 = int(round(p2.y()));

			if(safe_on_pitch(x1, y1) && safe_on_pitch(x2, y2)) {
				d = dist[y1][x1] * 5 + 0.5 * dist[y2][x2]; // it we actually be more useful to use the distance from us for the second part
				if(d < min_dist) {
					res_x = x1;
					res_y = y1;
					min_dist = d;
				}
			}
		}

		return point(res_x, res_y);
	}

	point choose_start_push_point(const point &ball_departure_point) const {
		float start_angle = atan2(float(ball_departure_point.x - ball->x), float(ball_departure_point.y - ball->y));
		const int extra_space = scale(23);
		int target_x = 0, target_y = 0;

		float h_min_offset = float((robot_width + 1) / 2 + scale(3));
		for(int offset = 0; offset < 180; offset += 2) {
			for(int dir = -1; dir <= 1; dir += 2) {
				target_x = int(round(ball->x - extra_space * sin(start_angle + dir * offset * pi / 180)));
				target_y = int(round(ball->y - extra_space * cos(start_angle + dir * offset * pi / 180)));
				if(!point_on_pitch(target_x, target_y))
					continue;
				if(dist[target_y][target_x] >= INF)
					continue;
				return point(target_x, target_y);
			}
		}
		// if we get here, it must be pretty bad
		return *ball;
	}
};
const int path_finder::move[8][2] = {{-1, -1}, {-1, 0}, {-1, 1}, {0, -1}, {0, 1}, {1, -1}, {1, 0}, {1, 1}};
const float path_finder::INF = 1e10;

#endif // path_finder_h__
