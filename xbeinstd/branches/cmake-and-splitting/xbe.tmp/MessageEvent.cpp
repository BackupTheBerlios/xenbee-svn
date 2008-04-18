#include "MessageEvent.hpp"
#include <sstream>

using namespace xbe;

MessageEvent::MessageEvent(const std::string& msg)
  : _msg(msg) {}

MessageEvent::MessageEvent(const std::string& msg, const mqs::Destination& src)
  : _msg(msg), _src(src) {}

MessageEvent::MessageEvent(const std::string& msg, const mqs::Destination& src, const mqs::Destination& dst)
  : _msg(msg), _src(src), _dst(dst) {}

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
