#ifndef MQS_DESTINATION_HPP
#define MQS_DESTINATION_HPP

#include <map>
#include <list>
#include <string>
#include <stdexcept>
#include <ostream>
#include <tr1/memory>
#include <cms/Destination.h>
#include <cms/Session.h>

namespace mqs {
    /**
       This  class provides a  simple wrapper  around queues  and topics
       naming.

       simple encoding:
       Queue: queue:foo.bar.baz?opt1=val1&opt2=val2
       Topic: topic:foo.bar.baz?opt1=val1&opt2=val2

       Default: queue

       Specified   properties   can  be   retrieved   via   a  call   to
       getProperty(std::string).
    */
    class Destination {
    public:
        Destination(const std::string &descriptor);
        Destination(const char *descriptor);
        Destination(const cms::Destination *d) throw();
        Destination(const Destination &dst) throw();
        Destination() throw();

        enum Type {
            UNSPECIFIED = 0,
            QUEUE,
            TOPIC
        };
      
        typedef std::pair<std::string, std::string> PropertyItem;
        typedef std::map<std::string, std::string> PropertyMap;
    public:
        const std::string& name() const;
        const Type type() const { return _type; }
        const std::string& getStringProperty(const std::string& key, const std::string& def = "") const;
        int getIntProperty(const std::string& key, int def = 0) const;
        long long getLongLongProperty(const std::string& key, long long def = 0) const;
        bool getBooleanProperty(const std::string& key, bool def = false) const;
    
        std::tr1::shared_ptr<cms::Destination> toCMSDestination(cms::Session &session) const;
        bool hasProperty(const std::string& key) const;
        bool isTopic() const;
        bool isQueue() const;
        bool isValid() const;

        void reset(const std::string& newDestination);
        void reset(const cms::Destination* newDestination) throw();
        void reset(const mqs::Destination& newDestination) throw();
        void reset() throw();
 
        std::string str() const;

        std::ostream& operator<<(std::ostream& os) {
            os << str();
            return os;
        }
    
    private:
        bool _isValid;
        std::string _name;
        enum Type _type;
        PropertyMap _properties;

        void parse_destination_descriptor(const std::string& descriptor);
        void parse_properties(const std::string& properties);
        std::string build_destination_descriptor(const cms::Destination*) const;
        std::string cms_destination_type_to_string(const cms::Destination::DestinationType&) const;
        std::string cms_destination_name(const cms::Destination*) const;

        template<typename T>
        T fromString(const std::string&, bool* ok = NULL) const;
        template<typename T>
        std::string toString(T val) const;
    };
}

std::ostream& operator<<(std::ostream& os, const mqs::Destination& dst);

#endif // !MQS_DESTINATION_HPP
