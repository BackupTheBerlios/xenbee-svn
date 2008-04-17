#ifndef SEDA_STRING_EVENT_HPP
#define SEDA_STRING_EVENT_HPP 1

#include <string>
#include <seda/IEvent.hpp>

namespace seda {
  class StringEvent : public IEvent {
  public:
    explicit
    StringEvent(const std::string& text="")
      : _text(text) {}

    std::string str() const { return _text; }
    const std::string& text() const { return _text; }
  private:
    std::string _text;
  };
}

#endif // !SEDA_STRING_EVENT_HPP
