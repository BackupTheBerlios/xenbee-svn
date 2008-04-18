#ifndef XBE_XML_DESERIALIZE_STRATEGY_HPP
#define XBE_XML_DESERIALIZE_STRATEGY_HPP 1

#include <seda/StrategyDecorator.hpp>

namespace xbe {
  /** Decodes  text messages  that contain  an XML  document  into XML
      messages.
   */
  class XMLDeserializeStrategy : public seda::StrategyDecorator {
  public:
    XMLDeserializeStrategy(const seda::Strategy::Ptr& s)
      : seda::StrategyDecorator(s->name()+".xml-deserialize", s) {}
    virtual ~XMLDeserializeStrategy() {}

    virtual void perform(const seda::IEvent::Ptr&) const;
  };
}

#endif // !XBE_XML_DESERIALIZE_STRATEGY_HPP
