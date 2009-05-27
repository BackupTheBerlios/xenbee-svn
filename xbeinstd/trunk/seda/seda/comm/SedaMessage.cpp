#include "SedaMessage.hpp"
#include "seda-msg.pb.h"

using namespace seda::comm;

void SedaMessage::decode(const std::string &s) throw(DecodingError) {
    Message m;
    m.ParseFromString(s);
    if (! m.has_to()) throw DecodingError("the message did not contain the required field 'to'");
    if (! m.has_from()) throw DecodingError("the message did not contain the required field 'from'");
    if (! m.has_payload()) throw DecodingError("the message did not contain the required field 'payload'");

    to_ = m.to();
    from_ = m.from();
    payload_ = m.payload();
    valid_ = true;
}

std::string SedaMessage::encode() const throw(EncodingError) {
    if (! is_valid()) throw EncodingError("trying to encode an invalid message!");

    Message m;
    m.set_to(to());
    m.set_from(from());
    m.set_payload(payload());
    std::string serializedMessage;
    m.SerializeToString(&serializedMessage);
    return serializedMessage;
}
