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

#ifndef synchronized_print_h__
#define synchronized_print_h__

#include <boost/thread.hpp>
#include <iostream>
#include <sstream>

using namespace std;
using namespace boost;

namespace std {
	class synchronized_print {
		static mutex output_lock;
		mutable stringstream ss;

	public:
		synchronized_print(): ss() {

		}

		template <typename T>
		const synchronized_print& operator<<(const T &x) const {
			ss << x;
			return *this;
		}

		const synchronized_print& operator<<(ostream& (*x)(ostream&)) const {
			ss << "\n";
			mutex::scoped_lock(output_lock);
			cout << ss.str();
			cout.flush();
			ss.str("");
			return *this;
		}

		~synchronized_print() {
			string s = ss.str();
			if(s.empty())
				return;
			if(s[s.size() - 1] != '\n')
				s += "\n";
			mutex::scoped_lock(output_lock);
			cout << s;
			cout.flush();
			ss.str("");
		}
	};
	#define cout synchronized_print()
}

#endif // synchronized_print_h__
