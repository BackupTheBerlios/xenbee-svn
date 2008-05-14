#include <stdexcept>
#include <cassert>
#include <sstream>
#include <iostream>
#include <cctype>
#include <algorithm>

#include <cms/Destination.h>
#include <cms/Queue.h>
#include <cms/Topic.h>
#include <cms/TemporaryQueue.h>
#include <cms/TemporaryTopic.h>

#include <mqs/DestinationProperties.hpp>
#include <mqs/Destination.hpp>

using namespace mqs;

Destination::Destination(const std::string& descriptor)
    : _isValid(false), _name(""), _type(UNSPECIFIED) {
    reset(descriptor);
}

Destination::Destination(const Destination& dst) throw()
    : _isValid(false), _name(""), _type(UNSPECIFIED) {
    reset(dst);
}

Destination::Destination(const cms::Destination* dst) throw()
    : _isValid(false), _name(""), _type(UNSPECIFIED) {
    reset(dst);
}

Destination::Destination() throw()
    : _isValid(false), _name(""), _type(UNSPECIFIED) {
    _isValid = false;
}

void
Destination::reset(const std::string& newDestination) {
    try {
        parse_destination_descriptor(newDestination);
        _isValid = true;
    } catch(...) {
        reset();
        throw;
    }
}

void
Destination::reset(const cms::Destination* newDestination) throw() {
    try {
        parse_destination_descriptor(build_destination_descriptor(newDestination));
        _isValid = true;
    } catch(...) {
        reset();
    }
}

void
Destination::reset(const mqs::Destination& newDestination) throw() {
    if (newDestination.isValid()) {
        _name = newDestination._name;
        _properties = newDestination._properties;
        _type = newDestination._type;
        _isValid = true;
    } else {
        reset();
    }
}

void
Destination::reset() throw() {
    _isValid = false;
    _properties.clear();
    _name = "";
    _type = UNSPECIFIED;
}

const std::string&
Destination::name() const {
    return _name;
}

bool
Destination::isTopic() const {
    return _type == TOPIC;
}

bool
Destination::isQueue() const {
    return (_type == QUEUE || _type == UNSPECIFIED);
}

bool
Destination::isValid() const {
    return _isValid;
}

const std::string&
Destination::getStringProperty(const std::string& key, const std::string& def) const {
    PropertyMap::const_iterator it = _properties.find(key);
    if (it == _properties.end()) {
        //throw std::invalid_argument("no such property: "+key);
        return def;
    }
    return it->second;
}

int
Destination::getIntProperty(const std::string& key, int def) const {
    std::string val_s = getStringProperty(key);
    bool ok = false;
    int val = fromString<int>(val_s, &ok);
    if (ok)
        return val;
    return def;
}

long long
Destination::getLongLongProperty(const std::string& key, long long def) const {
    std::string val_s = getStringProperty(key);
    bool ok = false;
    long long val = fromString<long long>(val_s, &ok);
    if (ok)
        return val;
    return def;
}

bool
Destination::getBooleanProperty(const std::string& key, bool def) const {
    std::string val_s = getStringProperty(key);
    std::transform(val_s.begin(), val_s.end(), val_s.begin(), tolower);
    if ( (val_s == "false") || (val_s == "no") || (val_s == "0")) {
        return false;
    } else if ( (val_s == "true") || (val_s == "yes") || (val_s == "1")) {
        return true;
    } else {
        return def;
    }
}

bool
Destination::hasProperty(const std::string& key) const {
    PropertyMap::const_iterator it = _properties.find(key);
    if (it == _properties.end()) {
        return false;
    }
    return true;
}

std::string
Destination::build_destination_descriptor(const cms::Destination* cms) const {
    if (cms == 0) {
        return "";
    }
  
    std::string dType(cms_destination_type_to_string(cms->getDestinationType()));
    std::string name(cms_destination_name(cms));
    std::stringstream s;
    s << name;
    s << "?type=" << dType;
    // get the properties
    std::vector<std::pair<std::string, std::string> > properties(cms->getCMSProperties().toArray());
    for (std::vector<std::pair<std::string, std::string> >::const_iterator it(properties.begin());
         it != properties.end();
         it++) {
        s << "&" << it->first << "=" << it->second;
    }
    return s.str();
}

std::string
Destination::cms_destination_type_to_string(const cms::Destination::DestinationType& t) const {
    switch (t) {
    case cms::Destination::TEMPORARY_QUEUE:
    case cms::Destination::QUEUE:
        return "queue";
    case cms::Destination::TEMPORARY_TOPIC:
    case cms::Destination::TOPIC:
        return "topic";
    default:
        throw std::invalid_argument("destination type unknown" + toString<int>(t));
    }
}

std::string
Destination::cms_destination_name(const cms::Destination* d) const {
    switch (d->getDestinationType()) {
    case cms::Destination::TEMPORARY_QUEUE:
        return ((const cms::TemporaryQueue*)d)->getQueueName();
    case cms::Destination::QUEUE:
        return ((const cms::Queue*)d)->getQueueName();
    case cms::Destination::TEMPORARY_TOPIC:
        return ((const cms::TemporaryTopic*)d)->getTopicName();
    case cms::Destination::TOPIC:
        return ((const cms::Topic*)d)->getTopicName();
    default:
        throw std::invalid_argument("destination type unknown" + toString<int>(d->getDestinationType()));
    }
}

void
Destination::parse_destination_descriptor(const std::string& descriptor) {
    std::string descr(descriptor);

  
    /*
    // check for queue or topic start
    if (descr.find("queue:") == 0) { // starts with queue
    _isTopic = false;
    } else if (descr.find("topic:") == 0) { // starts with topic
    _isTopic = true;
    } else {
    throw std::invalid_argument("illegal destination descriptor: " + descriptor);
    }

    // remove everything up to the first ":"
    std::string::size_type typeEndPos = descr.find(":");
    descr.erase(0, typeEndPos+1);
    */
  
    // next part is the queue/topic name followed by the properties: <name>[?[k=v&k=v]...]
    std::string::size_type propertiesStart = descr.find("?");
    if (propertiesStart == std::string::npos) { // no properties -> finished parsing descriptor
        _name = descr;
        _type = UNSPECIFIED;
        if (_name.size() == 0) {
            throw std::invalid_argument("destination name is empty");
        }
    } else {
        // name is the substring up to the "?"
        _name = descr.substr(0, propertiesStart);
        if (_name.size() == 0) {
            throw std::invalid_argument("destination name is empty");
        }
        descr.erase(0, propertiesStart+1);
        parse_properties(descr);
        std::string t(getStringProperty(DestinationProperties::TYPE.name));
        if (t == "queue") {
            _type = QUEUE;
        } else if (t == "topic") {
            _type = TOPIC;
        }
    }
}

void
Destination::parse_properties(const std::string& properties) {
    // property assignments are separated by &
    // key/values are separated by =
    std::string props(properties);
    while (!props.empty()) {
        // extract the first property
        std::string::size_type idxOfAmpersand = props.find("&");
        std::string key_value;
        if (idxOfAmpersand == std::string::npos) {
            key_value = props;
            props.erase();
        } else {
            key_value = props.substr(0, idxOfAmpersand);
            props.erase(0, idxOfAmpersand+1);
        }

        // try to split it into key and value
        std::string::size_type idxOfEqualSign = key_value.find("=");
        if (idxOfEqualSign == 0) {
            throw std::invalid_argument("illegal property (empty key): " + key_value);
        } else if (idxOfEqualSign == std::string::npos) {
            _properties.insert(std::make_pair(key_value, ""));
        } else {
            std::string key = key_value.substr(0, idxOfEqualSign);
            std::string val = key_value.substr(idxOfEqualSign+1);
            _properties.insert(std::make_pair(key,val));
        }
    }
}

std::string
Destination::str() const {
    if (!isValid()) {
        return "";
    }
  
    std::stringstream s;
    //  s << (isTopic() ? "topic:" : "queue:");
    s << name();
    if (!_properties.empty()) {
        s << "?";
        PropertyMap::const_iterator it = _properties.begin();
        for(; it != _properties.end(); it++) {
            if (it != _properties.begin())
                s << "&";
            s << it->first << "=" << it->second;
        }
    }
    return s.str();
}

std::ostream&
operator<<(std::ostream& os, const Destination& dst) {
    return (os << dst.str());
}

template<typename T>
T
Destination::fromString(const std::string& s, bool* ok) const {
    std::stringstream sstr(s);
    T v;
    sstr >> v;
    if (ok != NULL) {
        (*ok) = (sstr.fail() != true);
    }
    return v;
}

template<typename T>
std::string
Destination::toString(T v) const {
    std::stringstream sstr;
    sstr << v;
    return sstr.str();
}
