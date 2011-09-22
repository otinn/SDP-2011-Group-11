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

#ifndef basic_planner_h__
#define basic_planner_h__

#include <string>

#include "input_reader.hpp"
#include "utility.hpp"
#include "pitch.hpp"

using namespace std;

class basic_planner {
	input_reader *reader;
	string name;

protected:
	object *ball;
	robot *us, *enemy;
	STATE_TYPE forced_state;

public:
	basic_planner(input_reader *reader, string name): reader(reader), name(name), ball(0), us(0), enemy(0), forced_state(WAIT) {}

	virtual void set_data(sptr<object> ball, sptr<robot> us, sptr<robot> enemy, STATE_TYPE forced_state) {
		if(this->ball)
			delete this->ball;
		this->ball = ball? new object(*ball): 0;

		if(this->us)
			delete this->us;
		this->us = us? new robot(*us): 0;

		if(this->enemy)
			delete this->enemy;
		this->enemy = enemy? new robot(*enemy): 0;

		this->forced_state = forced_state;
	}

protected:
	bool near_wall(int x, int y) const {
		if(x < scale(11) || x + scale(11) > pitch_width)
			return true;
		if(y < scale(11) || y + scale(11) > pitch_height)
			return true;
		return false;
	}

	bool ball_in_goal() const {
		if(!ball)
			return false;
		if(ball->y < scale_factor * -5 || ball->y > pitch_height + scale_factor * 5)
			return true;
		if(ball->x < scale_factor * -0.5 || ball->x > pitch_width + scale_factor * 0.5)
			return true;
		return false;
	}

	static void force_into_bounds(object *obj) {
		if(obj->x < 2)
			obj->x = 2;
		if(obj->y < 2)
			obj->y = 2;
		if(obj->x > pitch_width - 2)
			obj->x = pitch_width - 2;
		if(obj->y > pitch_height - 2)
			obj->y = pitch_height - 2;
	}

public:
	virtual void plan() = 0;

	int operator()() {
		sptr<object> old_ball;
		sptr<robot> old_us, old_enemy;
		STATE_TYPE forced_state = WAIT;

		while(true) {
			sptr<object> ball(reader->get_ball());
			sptr<robot> us(reader->get_robot(US)), enemy(reader->get_robot(ENEMY));
			STATE_TYPE new_state = reader->get_forced_state();
			if(us)
				force_into_bounds(us.get());
			if(enemy)
				force_into_bounds(enemy.get());

			bool same = true;
			if((old_ball == 0) != (ball == 0))
				same = false;
			else if(old_ball && *old_ball != *ball)
				same = false;
			else if((old_us == 0) != (us == 0))
				same = false;
			else if(old_us && *old_us != *us)
				same = false;
			else if((old_enemy == 0) != (enemy == 0))
				same = false;
			else if(old_enemy && *old_enemy != *enemy)
				same = false;
			else if(forced_state != new_state)
				same = false;

			if(!same) {
				if(ball)
					old_ball = ball;

				if(us)
					old_us = us;

				if(enemy)
					old_enemy = enemy;

				forced_state = new_state;

				set_data(ball, us, enemy, forced_state);
				long long start = now_in_nanoseconds();
				plan();
				//if(name == "planner") {
				//cout << name << " " << (now_in_nanoseconds() - start) / 1e9 << " seconds" << endl;
				//}
			} else
				sleep_ms(1);
		}
	}
};

#endif // basic_planner_h__
