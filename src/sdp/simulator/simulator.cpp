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

#include <boost/date_time.hpp>
#include <boost/thread.hpp>
#include <boost/regex.hpp>
#include <Box2D/Box2D.h>
#include <iostream>
#include <sstream>
#include <cstdio>
#include <queue>

using namespace std;
using namespace boost;

// pitch
const float pitch_height = 122;
const float pitch_width = 244;
const float goal_height = 60;
const float wall_thickness = 1;

const float scale_factor = 0.04;
const float pi = 3.14159265;

class physics_info {
	struct body_info {
		float density;
		float friction;
		float restitution;
		float angular_damping;
		float linear_damping;
		
		body_info() {
			density = -1e100;
			friction = -1e100;
			restitution = -1e100;
			angular_damping = -1e100;
			linear_damping = -1e100;
		}
	};
	
	struct init_pos {
		float init_x;
		float init_y;
		int parts;
		
		init_pos() {
			init_x = -1e100;
			init_y = -1e100;
			parts = 0;
		}
		
		bool enabled() const {
			return (parts & 3) == 3;
		}
	};
	
	struct ball_info: public body_info, public init_pos {};
	
	struct robot_info: public init_pos {
		float init_rotation;
		
		robot_info() {
			init_rotation = -1e100;
		}
		
		bool enabled() const {
			return (parts & 7) == 7;
		}
	};
	
	struct motor_info {
		float scale;
		float force[128];
		
		motor_info() {
			scale = -1e100;
			for(int i = 0; i < 128; ++i)
				force[i] = -1e100;
		}
		
		float get_force(int input) const {
			int dir = input < 0? -1: 1;
			input = abs(input);
			if(input > 127)
				input = 127;
			return dir * force[input] * scale;
		}
	};
	
	struct kicker_info {
		float scale;
		float force[128];
		
		kicker_info() {
			scale = -1e100;
			for(int i = 0; i < 128; ++i)
				force[i] = -1e100;
		}
		
		float get_force(int input) const {
			int dir = input < 0? -1: 1;
			input = abs(input);
			if(input > 127)
				input = 127;
			return dir * force[input] * scale;
		}
	};
	
public:
	ball_info ball;
	body_info robot;
	robot_info us;
	robot_info enemy;
	motor_info motor;
	kicker_info kicker;
	float max_frames_per_second;
	int velocity_iterations;
	int position_iterations;
	
	physics_info() {
		max_frames_per_second = 15;
		velocity_iterations = 10;
		position_iterations = 10;
	}
	
	void read_info(const string &filename) {
		ifstream fin(filename.c_str());
		string s, name;
		float value;
		
		while(getline(fin, s)) {
			if(s.empty() || s[0] == '#')
				continue;
			istringstream ss(s);
			if(ss >> name >> value) {
				if(name == "ball.density") {
					ball.density = value;
				} else if(name == "ball.friction") {
					ball.friction = value;
				} else if(name == "ball.restitution") {
					ball.restitution = value;
				} else if(name == "ball.angular_damping") {
					ball.angular_damping = value;
				} else if(name == "ball.linear_damping") {
					ball.linear_damping = value;
				} else if(name == "robot.density") {
					robot.density = value;
				} else if(name == "robot.friction") {
					robot.friction = value;
				} else if(name == "robot.restitution") {
					robot.restitution = value;
				} else if(name == "robot.angular_damping") {
					robot.angular_damping = value;
				} else if(name == "robot.linear_damping") {
					robot.linear_damping = value;
				} else if(name == "ball.init_x") {
					ball.init_x = value;
					ball.parts |= (1 << 0);
				} else if(name == "ball.init_y") {
					ball.init_y = value;
					ball.parts |= (1 << 1);
				} else if(name == "us.init_x") {
					us.init_x = value;
					us.parts |= (1 << 0);
				} else if(name == "us.init_y") {
					us.init_y = value;
					us.parts |= (1 << 1);
				} else if(name == "us.init_rotation") {
					us.init_rotation = value;
					us.parts |= (1 << 2);
				} else if(name == "enemy.init_x") {
					enemy.init_x = value;
					enemy.parts |= (1 << 0);
				} else if(name == "enemy.init_y") {
					enemy.init_y = value;
					enemy.parts |= (1 << 1);
				} else if(name == "enemy.init_rotation") {
					enemy.init_rotation = value;
					enemy.parts |= (1 << 2);
				} else if(name == "max_frames_per_second") {
					max_frames_per_second = value;
				} else if(name == "velocity_iterations") {
					velocity_iterations = max(min(int(round(value)), 30), 1);
				} else if(name == "position_iterations") {
					position_iterations = max(min(int(round(value)), 30), 1);
				} else if(name == "motor_scale") {
					motor.scale = value;
				} else if(s.substr(0, string("motor.force_").size()) == "motor.force_") {
					s = s.substr(string("motor.force_").size());
					int num;
					if(sscanf(s.c_str(), "%d%f", &num, &value) == 2) {
						num = max(0, min(127, num));
						motor.force[num] = kicker.force[num] = value;
					}
				} else if(name == "kicker_scale") {
					kicker.scale = value;
				} else {
					cout << "invalid config line in file " << filename << ": " << s << endl;
				}
			}
		}
		
		fin.close();
	}
	
	void show_data() const {
		cout << "ball.density " << ball.density << endl;
		cout << "ball.friction " << ball.friction << endl;
		cout << "ball.restitution " << ball.angular_damping << endl;
		cout << "ball.linear_damping " << ball.linear_damping << endl;
		cout << endl;
		cout << "robot.density " << robot.density << endl;
		cout << "robot.friction " << robot.friction << endl;
		cout << "robot.restitution " << robot.restitution << endl;
		cout << "robot.angular_damping " << robot.angular_damping << endl;
		cout << "robot.linear_damping " << robot.linear_damping << endl;
		cout << endl;
		cout << "# if any of the parameters are missing then it won't be shown" << endl;
		if(ball.parts & 1)
			cout << "ball.init_x " << ball.init_x << endl;
		if(ball.parts & 2)
			cout << "ball.init_y " << ball.init_y << endl;
		cout << endl;
		cout << "# if any of the parameters are missing then it won't be shown" << endl;
		if(us.parts & 1)
			cout << "us.init_x " << us.init_x << endl;
		if(us.parts & 2)
			cout << "us.init_y " << us.init_y << endl;
		if(us.parts & 4)
			cout << "us.init_rotation " << us.init_rotation << endl;
		cout << endl;
		cout << "# if any of the parameters are missing then it won't be shown" << endl;
		if(enemy.parts & 1)
			cout << "enemy.init_x " << enemy.init_x << endl;
		if(enemy.parts & 2)
			cout << "enemy.init_y " << enemy.init_y << endl;
		if(enemy.parts & 4)
			cout << "enemy.init_rotation " << enemy.init_rotation << endl;
		cout << endl;
		cout << "# affects only the output, not the simulation" << endl;
		cout << "max_frames_per_second " << max_frames_per_second << endl;
		cout << endl;
		cout << "# larger values -> more accurate" << endl;
		cout << "velocity_iterations " << velocity_iterations << endl;
		cout << "position_iterations " << position_iterations << endl;
		cout << endl;
		cout << "# every motor force will be multiplied by this factor" << endl;
		cout << "motor_scale " << motor.scale << endl;
		for(int i = 0; i < 128; ++i)
			cout << "motor.force_" << i << " " << motor.force[i] << endl;
	}
};
static physics_info physics;

const float scale(const float f) {
	return f * scale_factor;
}

const float reverse_scale(const float f) {
	return f / scale_factor;
}

const string get_datetime() {
	return to_iso_extended_string(boost::posix_time::microsec_clock::local_time());
}

class wall {
	b2BodyDef wall_def;
	b2Body* wall_body;
	b2PolygonShape wall_box;
	
public:
	wall(b2World &world, float pos_x, float pos_y, float wall_width, float wall_height) {
		wall_def.position.Set(pos_x, pos_y);
		wall_body = world.CreateBody(&wall_def);
		wall_box.SetAsBox(wall_width / 2, wall_height / 2);
		wall_body->CreateFixture(&wall_box, 0);
	}
};

class ball {
	const static float radius = 2.1;
	b2BodyDef ball_def;
	b2Body* ball_body;
	b2FixtureDef ball_fixture_def;
	b2CircleShape ball_shape;
	b2Fixture *ball_fixture;
	
public:
	ball(b2World &world, float pos_x, float pos_y) {
		ball_def.type = b2_dynamicBody;
		ball_def.angularDamping = physics.ball.angular_damping;
		ball_def.linearDamping = physics.ball.linear_damping;
		ball_def.position.Set(pos_x, pos_y);
		ball_body = world.CreateBody(&ball_def);
		ball_shape.m_radius = scale(radius);
		
		ball_fixture_def.shape = &ball_shape;
		ball_fixture_def.density = physics.ball.density;
		ball_fixture_def.friction = physics.ball.friction;
		ball_fixture_def.restitution = physics.ball.restitution;
		ball_fixture = ball_body->CreateFixture(&ball_fixture_def);
	}
	
	void show(const string &frame_time) const {
		b2Vec2 pos = ball_body->GetWorldPoint(ball_shape.m_p);
		printf("/vision/xy ball %.1f %.1f %s\n", reverse_scale(pos.x), reverse_scale(pos.y), frame_time.c_str());
		fflush(stdout);
	}
	
	void apply_force(float force_x, float force_y) {
		b2Vec2 force(force_x, force_y);
		ball_body->ApplyForce(force, ball_body->GetWorldPoint(ball_shape.m_p));
	}
	
	void set_xy(float x, float y) {
		ball_body->SetTransform(b2Vec2(x, y), ball_body->GetAngle());
		ball_body->SetAngularVelocity(0);
		ball_body->SetLinearVelocity(b2Vec2(0, 0));
	}
	
	friend class robot;
};

class robot: public b2ContactListener {
	const static float height = 20;
	const static float width = 18;
	const static float offset_wheel_x = 1;
	const static float offset_wheel_y = 10;
	const static float tooth_width = 0.5;
	const static float tooth_height = 1;
	const static float kicker_height = 4.5;
	
	ball *the_ball;
	bool ball_in_kicker_area;
	int kicker_ready;
	
	b2BodyDef robot_def;
	b2Body *robot_body;
	b2FixtureDef robot_fixture_def;
	b2PolygonShape robot_shape;
	b2FixtureDef left_tooth_fixture_def;
	b2PolygonShape left_tooth_shape;
	b2FixtureDef right_tooth_fixture_def;
	b2PolygonShape right_tooth_shape;
	b2FixtureDef kicker_fixture_def;
	b2PolygonShape kicker_shape;
	b2Fixture *kicker_fixture;
	
	float normalize_angle(float angle) const {
		while(angle < 0)
			angle += 2 * pi;
		while(angle > 2 * pi)
			angle -= 2 * pi;
		return angle;
	}
	
public:
	robot(b2World &world, float pos_x, float pos_y, float rotation, ball *the_ball) {
		ball_in_kicker_area = false;
		kicker_ready = true;
		this->the_ball = the_ball;
		
		robot_def.type = b2_dynamicBody;
		robot_def.angularDamping = physics.robot.angular_damping;
		robot_def.linearDamping = physics.robot.linear_damping;
		robot_def.angle = 0;
		robot_def.position.Set(pos_x, pos_y);
		robot_body = world.CreateBody(&robot_def);
		
		robot_shape.SetAsBox(scale(width / 2), scale(height / 2));
		robot_fixture_def.shape = &robot_shape;
		robot_fixture_def.density = physics.robot.density;
		robot_fixture_def.friction = physics.robot.friction;
		robot_fixture_def.restitution = physics.robot.restitution;
		robot_body->CreateFixture(&robot_fixture_def);
		
		left_tooth_shape.SetAsBox(scale(tooth_width / 2), scale(tooth_height / 2), b2Vec2(scale(tooth_width / 2 - width / 2), scale(height / 2 + tooth_height / 2)), 0);
		left_tooth_fixture_def.shape = &left_tooth_shape;
		left_tooth_fixture_def.density = physics.robot.density;
		left_tooth_fixture_def.friction = physics.robot.friction;
		left_tooth_fixture_def.restitution = physics.robot.restitution;
		robot_body->CreateFixture(&left_tooth_fixture_def);
		
		right_tooth_shape.SetAsBox(scale(tooth_width / 2), scale(tooth_height / 2), b2Vec2(scale(width / 2 - tooth_width / 2), scale(height / 2 + tooth_height / 2)), 0);
		right_tooth_fixture_def.shape = &right_tooth_shape;
		right_tooth_fixture_def.density = physics.robot.density;
		right_tooth_fixture_def.friction = physics.robot.friction;
		right_tooth_fixture_def.restitution = physics.robot.restitution;
		robot_body->CreateFixture(&right_tooth_fixture_def);
		
		kicker_shape.SetAsBox(scale((width - 2 * tooth_width) / 2), scale(kicker_height / 2), b2Vec2(0, scale(height / 2 + kicker_height / 2)), 0);
		kicker_fixture_def.shape = &kicker_shape;
		kicker_fixture_def.isSensor = true;
		kicker_fixture = robot_body->CreateFixture(&kicker_fixture_def);
		
		set_rotation(rotation);
	}
	
	void show(const string &name, const string &frame_time) const {
		b2Vec2 pos = robot_body->GetWorldPoint(robot_shape.m_centroid);
		printf("/vision/xy %s %.1f %.1f %s\n", name.c_str(), reverse_scale(pos.x), reverse_scale(pos.y), frame_time.c_str());
		b2Vec2 pos2 = robot_body->GetWorldPoint(kicker_shape.m_centroid);
		printf("/vision/kicker/xy %s %.1f %.1f %s\n", name.c_str(), reverse_scale(pos2.x), reverse_scale(pos2.y), frame_time.c_str());
		printf("/vision/rotation %s %.4f %s\n", name.c_str(), normalize_angle(-robot_body->GetAngle()), frame_time.c_str());
		fflush(stdout);
	}
	
	void apply_force(float force_size, bool left) {
		b2Vec2 point = robot_body->GetWorldPoint(b2Vec2(scale(left? offset_wheel_x - width / 2: width / 2 - offset_wheel_x), scale(offset_wheel_y - height / 2)));
		b2Vec2 force = robot_body->GetWorldVector(b2Vec2(0, force_size));
		robot_body->ApplyForce(force, point);
	}
	
	void set_xy(float x, float y) {
		b2Vec2 robot_pos = robot_body->GetWorldPoint(robot_shape.m_centroid);
		robot_body->SetTransform(b2Vec2(x, y), robot_body->GetAngle());
		robot_body->SetAngularVelocity(0);
		robot_body->SetLinearVelocity(b2Vec2(0, 0));
		robot_pos = robot_body->GetWorldPoint(robot_shape.m_centroid);
	}
	
	void set_rotation(float rotation) {
		b2Vec2 robot_pos = robot_body->GetWorldPoint(robot_shape.m_centroid);
		const float x = robot_pos.x;
		const float y = robot_pos.y;
		robot_body->SetTransform(b2Vec2(x, y), -rotation);
		robot_body->SetAngularVelocity(0);
		robot_body->SetLinearVelocity(b2Vec2(0, 0));
		robot_pos = robot_body->GetWorldPoint(robot_shape.m_centroid);
	}
	
	void apply_kicker_force(float force) {
		if(force > 0) {
			if(kicker_ready) {
				kicker_ready = false;
				if(ball_in_kicker_area) {
					float rotation = robot_body->GetAngle();
					the_ball->apply_force(-1 * sin(rotation) * force, cos(rotation) * force);
				}
			}
		} else {
			kicker_ready = true;
		}
	}
	
	void BeginContact(const b2Contact * const contact) {
		if(contact->GetFixtureA() == the_ball->ball_fixture && contact->GetFixtureB() == kicker_fixture) {
			ball_in_kicker_area = true;
		} else if(contact->GetFixtureA() == kicker_fixture && contact->GetFixtureB() == the_ball->ball_fixture) {
			ball_in_kicker_area = true;
		}
	}
	
	void EndContact(const b2Contact * const contact) {
		if(contact->GetFixtureA() == the_ball->ball_fixture && contact->GetFixtureB() == kicker_fixture) {
			ball_in_kicker_area = false;
		} else if(contact->GetFixtureA() == kicker_fixture && contact->GetFixtureB() == the_ball->ball_fixture) {
			ball_in_kicker_area = false;
		}
	}
};

class contact_listener: public b2ContactListener {
	robot *us, *enemy;
	
public:
	contact_listener(robot *us, robot *enemy): us(us), enemy(enemy) {}
	
	void BeginContact(b2Contact * contact) {
		if(us)
			us->BeginContact(contact);
		if(enemy)
			enemy->BeginContact(contact);
	}
	
	void EndContact(b2Contact * contact) {
		if(us)
			us->EndContact(contact);
		if(enemy)
			enemy->EndContact(contact);
	}
};

long long now_in_nanoseconds() {
	xtime t;
	xtime_get(&t, TIME_UTC);
	return t.sec * 1000000000ll + t.nsec;
}

void sleep(long long milliseconds) {
	xtime t;
	xtime_get(&t, TIME_UTC);
	t.sec += milliseconds / 1000;
	milliseconds %= 1000;
	t.nsec += 1000000 * milliseconds;
	thread::sleep(t);
}

class InputReader {
	const static char left_motor;
	const static char right_motor;
	
	mutable mutex input_lock;
	bool restart_sim;
	int speed_left[2];
	int speed_right[2];
	int speed_kicker[2];
	queue <pair <string, pair <float, float> > > xy_msg;
	queue <pair <string, float> > rotation_msg;
	
	string rstrip(const string &s) {
		int end = s.size() - 1;
		while(end >= 0 && s[end] <= 32)
			--end;
		return string(s.begin(), s.begin() + (end + 1));
	}
	
public:
	InputReader() {
		memset(speed_left, 0, sizeof(speed_left));
		memset(speed_right, 0, sizeof(speed_right));
		memset(speed_kicker, 0, sizeof(speed_kicker));
		restart_sim = false;
	}
		
	void work() {
		string s;
		while(true) {
			getline(cin, s);
			s = rstrip(s);
			mutex::scoped_lock m(input_lock);
			
			{
				regex reg("^/movement/order/brake\\s+((enemy)\\s+)?(B|C|left|right)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					bool enemy = matches[2] == "enemy";
					// TODO: do actual braking
					if(left_motor == matches[3] || matches[3] == "left")
						speed_left[enemy] = 0;
					else
						speed_right[enemy] = 0;
					continue;
				}
			}
			
			{
				regex reg("^/movement/order/idle\\s+((enemy)\\s+)?(B|C|left|right)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					bool enemy = matches[2] == "enemy";
					if(left_motor == matches[3] || matches[3] == "left")
						speed_left[enemy] = 0;
					else
						speed_right[enemy] = 0;
					continue;
				}
			}
			
			{
				regex reg("^/movement/order/run_inf\\s+((enemy)\\s+)?(B|C|left|right)\\s+(-?[0-9]+)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					bool enemy = matches[2] == "enemy";
					stringstream ss;
					ss << matches[4];
					int speed;
					ss >> speed;
					if(speed < -128)
						speed = -128;
					if(speed > 127)
						speed = 127;
					if(left_motor == matches[3] || matches[3] == "left")
						speed_left[enemy] = speed;
					else
						speed_right[enemy] = speed;
					continue;
				}
			}
			
			{
				regex reg("^/kicker/order/brake(\\s+(enemy))?$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					bool enemy = matches[2] == "enemy";
					speed_kicker[enemy] = 0;
					continue;
				}
			}
			
			{
				regex reg("^/kicker/order/run_inf\\s+((enemy)\\s+)?(-?[0-9]+)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					bool enemy = matches[2] == "enemy";
					stringstream ss;
					ss << matches[3];
					int speed;
					ss >> speed;
					if(speed < -128)
						speed = -128;
					if(speed > 127)
						speed = 127;
					speed_kicker[enemy] = speed;
					continue;
				}
			}
			
			{
				regex reg("^/manual/simulator/vision/xy\\s+(ball|us|enemy)\\s+(-?[0-9]+(\\.[0-9]+)?)\\s+(-?[0-9]+(\\.[0-9]+)?)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					stringstream ss;
					ss << matches[2] << " " << matches[4];
					float x, y;
					ss >> x >> y;
					x = max(min(x, float(pitch_width)), 0.0f);
					y = max(min(y, float(pitch_height)), 0.0f);
					xy_msg.push(make_pair(string(matches[1]), make_pair(x, y)));
					continue;
				}
			}
			
			{
				regex reg("^/manual/simulator/vision/rotation\\s+(us|enemy)\\s+(-?[0-9]+(\\.[0-9]+)?)$");
				match_results <string::const_iterator> matches; 
				string::const_iterator start = s.begin(), end = s.end();
				if(regex_search(start, end, matches, reg, match_default)) {
					stringstream ss;
					ss << matches[2];
					float rotation;
					ss >> rotation;
					rotation_msg.push(make_pair(string(matches[1]), rotation));
					continue;
				}
			}
			
			if(s == "/manual/simulator/restart")
				restart_sim = true;
		}
	}
	
	int get_left_speed(bool enemy) const {
		mutex::scoped_lock m(input_lock);
		return speed_left[enemy];
	}
	
	int get_right_speed(bool enemy) const {
		mutex::scoped_lock m(input_lock);
		return speed_right[enemy];
	}
	
	int get_kicker_speed(bool enemy) const {
		mutex::scoped_lock m(input_lock);
		return speed_kicker[enemy];
	}
	
	bool have_xy_message() const {
		mutex::scoped_lock m(input_lock);
		return !xy_msg.empty();
	}
	
	pair <string, pair <float, float> > get_xy_message() const {
		mutex::scoped_lock m(input_lock);
		return xy_msg.front();
	}
	
	void pop_xy_message() {
		mutex::scoped_lock m(input_lock);
		xy_msg.pop();
	}
	
	bool have_rotation_message() const {
		mutex::scoped_lock m(input_lock);
		return !rotation_msg.empty();
	}
	
	pair <string, float> get_rotation_message() const {
		mutex::scoped_lock m(input_lock);
		return rotation_msg.front();
	}
	
	void pop_rotation_message() {
		mutex::scoped_lock m(input_lock);
		rotation_msg.pop();
	}
	
	bool restart_simulation() {
		mutex::scoped_lock m(input_lock);
		bool res = restart_sim;
		restart_sim = false;
		return res;
	}
};
const char InputReader::left_motor = 'B';
const char InputReader::right_motor = 'C';

struct InputReaderPointer {
	InputReader *reader;
	
	InputReaderPointer() {
		reader = new InputReader();
	}
	
	int operator()() {
		reader->work();
	}
};

void run_simulation(const InputReaderPointer &input_reader) {
	b2World world(b2Vec2(0, 0), true);
	world.SetAutoClearForces(true);
	wall bottom_wall(world, scale(pitch_width / 2), scale(-wall_thickness / 2), scale(pitch_width + 2 * wall_thickness), scale(wall_thickness));
	wall top_wall(world, scale(pitch_width / 2), scale(pitch_height + wall_thickness / 2), scale(pitch_width + 2 * wall_thickness), scale(wall_thickness));
	
	const float pos_left_x = scale(-wall_thickness / 2);
	const float pos_right_x = scale(pitch_width + wall_thickness / 2);
	const float side_height = scale((pitch_height - goal_height) / 2 + wall_thickness);
	const float pos_side_bottom = scale(((pitch_height - goal_height) / 2 - wall_thickness) / 2);
	const float pos_side_top = scale((pitch_height - goal_height) / 2 + goal_height + ((pitch_height - goal_height) / 2 + wall_thickness) / 2);
	
	wall bottom_left_wall(world, pos_left_x, pos_side_bottom, scale(wall_thickness), side_height);
	wall bottom_right_wall(world, pos_right_x, pos_side_bottom, scale(wall_thickness), side_height);
	wall top_left_wall(world, pos_left_x, pos_side_top, scale(wall_thickness), side_height);
	wall top_right_wall(world, pos_right_x, pos_side_top, scale(wall_thickness), side_height);
	
	ball *the_ball = 0;
	if(physics.ball.enabled())
		the_ball = new ball(world, scale(physics.ball.init_x), scale(physics.ball.init_y));
	
	robot *us = 0;
	if(physics.us.enabled())
		us = new robot(world, scale(physics.us.init_x), scale(physics.us.init_y), physics.us.init_rotation, the_ball);
	
	robot *enemy = 0;
	if(physics.enemy.enabled())
		enemy = new robot(world, scale(physics.enemy.init_x), scale(physics.enemy.init_y), physics.enemy.init_rotation, the_ball);
	
	contact_listener *c_listener = new contact_listener(us, enemy);
	world.SetContactListener(c_listener);
	
	const int simulations_per_second = 100;
	const float timeStep = 1.0f / simulations_per_second;
	
	const long long start = now_in_nanoseconds();
	for(int step = 1, frames_done = 0; true; ++step) {
		if(input_reader.reader->restart_simulation())
			return;
		if(us) {
			us->apply_force(physics.motor.get_force(input_reader.reader->get_left_speed(false)), true);
			us->apply_force(physics.motor.get_force(input_reader.reader->get_right_speed(false)), false);
			us->apply_kicker_force(physics.kicker.get_force(input_reader.reader->get_kicker_speed(false)));
		}
		if(enemy) {
			enemy->apply_force(physics.motor.get_force(input_reader.reader->get_left_speed(true)), true);
			enemy->apply_force(physics.motor.get_force(input_reader.reader->get_right_speed(true)), false);
			enemy->apply_kicker_force(physics.kicker.get_force(input_reader.reader->get_kicker_speed(true)));
		}
		
		while(input_reader.reader->have_xy_message()) {
			pair <string, pair <float, float> > msg = input_reader.reader->get_xy_message();
			if(us && msg.first == "us")
				us->set_xy(scale(msg.second.first), scale(msg.second.second));
			else if(enemy && msg.first == "enemy")
				enemy->set_xy(scale(msg.second.first), scale(msg.second.second));
			else if(the_ball && msg.first == "ball")
				the_ball->set_xy(scale(msg.second.first), scale(msg.second.second));
			input_reader.reader->pop_xy_message();
		}
		
		while(input_reader.reader->have_rotation_message()) {
			pair <string, float> msg = input_reader.reader->get_rotation_message();
			if(us && msg.first == "us")
				us->set_rotation(msg.second);
			if(enemy && msg.first == "enemy")
				enemy->set_rotation(msg.second);
			input_reader.reader->pop_rotation_message();
		}
		
		world.Step(timeStep, physics.velocity_iterations, physics.position_iterations);
		
		const long long want = start + step * 1000000000ll / simulations_per_second;
		const long long now = now_in_nanoseconds();
		
		long long expected_frames = (long long) ((now - start) * double(physics.max_frames_per_second) / 1e9);
		if(frames_done < expected_frames) {
			const string &frame_time = get_datetime();
			if(the_ball)
				the_ball->show(frame_time);
			if(us)
				us->show("us", frame_time);
			if(enemy)
				enemy->show("enemy", frame_time);
			++frames_done;
		}
		
		const long long left = (want - now) / 1000000;
		if(left > 0)
			sleep(left);
		else if(now < want)
			cout << "/simulator/error/falling_behind " << (want - now) / 1e9 << endl;
	}
}

int main(int argc, char **argv) {
	ios_base::sync_with_stdio(false);
	cout << "/general/identify robot primary " << get_datetime() << " simulator" << endl;
	if(string(argv[0]).find("simulator/") != -1)
		physics.read_info("simulator/default.conf");
	else
		physics.read_info("default.conf");
	for(int i = 1; i < argc; ++i)
		physics.read_info(argv[i]);
	physics.show_data();
	
	InputReaderPointer input_reader;
	thread t(input_reader);
	
	while(true)
		run_simulation(input_reader);
	return 0;
}
