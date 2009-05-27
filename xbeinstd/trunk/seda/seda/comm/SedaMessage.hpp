#ifndef SEDA_COMM_MESSAGE_HPP
#define SEDA_COMM_MESSAGE_HPP 1

#include <seda/UserEvent.hpp>
#include <seda/comm/Decodeable.hpp>
#include <seda/comm/Encodeable.hpp>

#include <string>

namespace seda {
namespace comm {
    class SedaMessage : public seda::UserEvent, public seda::comm::Encodeable, public seda::comm::Decodeable {
    public:
        typedef std::tr1::shared_ptr<SedaMessage> Ptr;

        typedef std::string payload_type;
        typedef std::string address_type;

        explicit
        SedaMessage()
            : from_(""), to_(""), payload_(""), valid_(false) {}
        SedaMessage(const address_type & from, const address_type & to, const payload_type & payload)
            : from_(from), to_(to), payload_(payload), valid_(true) { }

        virtual ~SedaMessage() {}

        virtual void decode(const std::string&) throw(DecodingError);
        virtual std::string encode() const throw(EncodingError);

        const address_type & from() const { return from_; }
        const address_type & to() const { return to_; }
        const payload_type & payload() const { return payload_; }
        bool is_valid() const { return valid_; }
    private:
        address_type from_;
        address_type to_;
        payload_type payload_;
        bool valid_;
    };    
}}

#endif
