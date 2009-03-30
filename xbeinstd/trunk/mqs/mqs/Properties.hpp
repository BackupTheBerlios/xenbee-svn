#ifndef MQS_PROPERTIES_HPP
#define MQS_PROPERTIES_HPP 1

#include <string>
#include <map>
#include <mqs/MQSException.hpp>
#include <sstream>

namespace mqs {
    class PropertyLookupFailed : public mqs::MQSException {
    public:
        PropertyLookupFailed(const std::string &key)
            : mqs::MQSException(std::string("property not found: ") + key), _key(key) {}
        virtual ~PropertyLookupFailed() throw() {}

        const std::string &key() const { return _key; }
    private:
        std::string _key;
    };

    class PropertyConversionFailed : public mqs::MQSException {
    public:
        PropertyConversionFailed(const std::string &key, const std::string &value)
            : mqs::MQSException(std::string("property {"+key+","+value+"} could not be converted!")), _key(key), _value(value) {}
        virtual ~PropertyConversionFailed() throw() {}

        const std::string &key() const { return _key; }
        const std::string &value() const { return _value; }
    private:
        std::string _key;
        std::string _value;
    };

    /**
     * Holds a key-value store.
     *
     * warn: this class is not thread-safe.
     */
    class Properties {
    public:
        Properties() {}
        virtual ~Properties() {}

        void put(const std::string &key, const std::string &value);
        template <typename T> void put(const std::string &key, const T &value) throw(PropertyConversionFailed) {
            std::stringstream sstr;
            sstr << value;
            put(key, sstr.str());
        }
        std::size_t del(const std::string &key);

        bool has_key(const std::string &key) const;
        const std::string &get(const std::string &key) const throw(PropertyLookupFailed);
        const std::string &get(const std::string &key, const std::string &def) const throw();

        template <typename T> const T get(const std::string &key) const throw(PropertyConversionFailed, PropertyLookupFailed) {
            const std::string val(get(key));
            std::stringstream sstr(val);
            T ret;
            sstr >> ret;
            if (!sstr) {
                throw PropertyConversionFailed(key, val);
            } else {
                return ret;
            }
        }
        template <typename T> const T get(const std::string &key, const T &def) const throw(PropertyConversionFailed) {
            std::string val;
            try {
                val = get(key);
            } catch (const PropertyLookupFailed &plf) {
                return def;
            }

            std::stringstream sstr(val);
            T ret;
            sstr >> ret;
            if (!sstr) {
                throw PropertyConversionFailed(key, val);
            } else {
                return ret;
            }
        }

        void clear();
        bool empty() const;
    private:
        std::map<std::string, std::string> _properties;
    };
}

#endif // ! MQS_PROPERTIES_HPP
