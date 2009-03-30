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
