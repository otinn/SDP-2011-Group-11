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

#ifndef geometry_h__
#define geometry_h__

#include <CGAL/Cartesian.h>
#include <CGAL/Polygon_2.h>
#include <cmath>

#include "utility.hpp"

using namespace std;

typedef CGAL::Cartesian<double> Kernel;
typedef Kernel::Ray_2 Ray;
typedef Kernel::Line_2 Line;
typedef Kernel::Point_2 Point;
typedef Kernel::Vector_2 Vector;
typedef Kernel::Segment_2 Segment;

double euclidean_distance(double x1, double y1, double x2, double y2) {
	return sqrt(double((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)));
}

float point_distance(const Segment &a, const Point &p) {
	double up = (p.x() - a.source().x()) * (a.target().x() - a.source().x()) + (p.y() - a.source().y()) * (a.target().y() - a.source().y());
	double down = a.squared_length();
	if(fabs(down) < 1e-3)
		return euclidean_distance(p.x(), p.y(), a.source().x(), a.source().y());
	double u = up / down;
	if(u < 0 || u > 1)
		return 1e10;
	double x = a.source().x() + u * (a.target().x() - a.source().x());
	double y = a.source().y() + u * (a.target().y() - a.source().y());
	return euclidean_distance(p.x(), p.y(), x, y);
}

float segment_distance(const Segment &a, const Segment &b) {
	if(do_intersect(a, b))
		return 0;
	return min(min(point_distance(a, b.source()), point_distance(a, b.target())), min(point_distance(b, a.source()), point_distance(b, a.target())));
}

Point rotate_point(int vx, int vy, int x, int y, float rotation) {
	rotation = -rotation - pi / 2;
	return Point(vx + x * sin(rotation) - y * cos(rotation), vy + y * sin(rotation) + x * cos(rotation));
}

#endif // geometry_h__