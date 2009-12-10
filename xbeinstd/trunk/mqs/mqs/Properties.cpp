/* 
   Copyright (C) 2009 Alexander Petry <alexander.petry@itwm.fraunhofer.de>.

   This file is part of seda.

   seda is free software; you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation; either version 2, or (at your option) any
   later version.

   seda is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
   for more details.

   You should have received a copy of the GNU General Public License
   along with seda; see the file COPYING.  If not, write to
   the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  

*/

#include "Properties.hpp"

void mqs::Properties::put(const std::string &key, const std::string &val) {
    del(key);
    _properties.insert(std::make_pair(key, val));
}

std::size_t mqs::Properties::del(const std::string &key) {
    return _properties.erase(key);
}

bool mqs::Properties::has_key(const std::string &key) const {
    std::map<std::string, std::string>::const_iterator it(_properties.find(key));
    return (it != _properties.end());
}

const std::string &mqs::Properties::get(const std::string &key) const throw(PropertyLookupFailed) {
    std::map<std::string, std::string>::const_iterator it(_properties.find(key));
    if (it != _properties.end()) {
        return it->second;
    } else {
        throw PropertyLookupFailed(key);
    }
}

const std::string &mqs::Properties::get(const std::string &key, const std::string &def) const throw() {
    try {
        return get(key);
    } catch(...) {
        return def;
    }
}

void mqs::Properties::clear() {
    _properties.clear();
}

bool mqs::Properties::empty() const {
    return _properties.empty();
}
