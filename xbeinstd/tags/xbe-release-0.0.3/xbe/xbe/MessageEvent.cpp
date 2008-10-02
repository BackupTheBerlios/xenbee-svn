#include "MessageEvent.hpp"
#include <sstream>

using namespace xbe;

MessageEvent::MessageEvent(const std::string& msg)
  : _msg(msg) {}

MessageEvent::MessageEvent(const std::string& msg, const mqs::Destination& to, const mqs::Destination& from)
  : _msg(msg), _id(""), _dst(to), _src(from) {}

MessageEvent::~MessageEvent() {

}

std::string MessageEvent::str() const {
  std::ostringstream os;
  os << "Message ";
  os << ( id().size() ? ("("+id()+"): ") : ": ");
  os << ( source().isValid() ? source().name() : "unknown");
  os << " ---> ";
  os << ( destination().isValid() ? destination().name() : "unknown");
  os << ": " << message();
  return os.str();
}
