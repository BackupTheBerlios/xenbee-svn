#include "testsconfig.hpp"
#include "MessageTranslatorTest.hpp"

#include <string>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#include <xbe/XbeLibUtils.hpp>
#include <xbe/MessageTranslatorStrategy.hpp>
#include <xbe/event/ObjectEvent.hpp>

#include <xbe/xbe-msg.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( MessageTranslatorTest );

MessageTranslatorTest::MessageTranslatorTest()
  : XBE_INIT_LOGGER("tests.xbe.message-translator")
{}

void
MessageTranslatorTest::setUp() {
  XbeLibUtils::initialise();
}

void
MessageTranslatorTest::tearDown() {
  seda::StageRegistry::instance().clear();
  XbeLibUtils::terminate();
}

void
MessageTranslatorTest::testXMLExecute() {
    xbemsg::body_t body;
    xbemsg::execute_t exec;
    body.execute(exec);
    xbemsg::header_t hdr("","","");
    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(hdr, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy("translate", discard));
    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("","",msg));
    translate->perform(obj);
}

