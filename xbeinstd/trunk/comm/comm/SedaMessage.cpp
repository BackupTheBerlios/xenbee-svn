#include "SedaMessage.hpp"
#include "seda-msg.pb.h"

using namespace seda::comm;

void SedaMessage::decode(const std::string &s) {
    Message m;
    m.ParseFromString(s);

}

std::string SedaMessage::encode() const {

}
