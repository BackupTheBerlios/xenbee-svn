#include <string>
#include <iostream>

#include <vector>
#include <mqs/MessageSequenceGenerator.hpp>

#include "MessageSequenceGeneratorTest.hpp"
#include "testsconfig.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( MessageSequenceGeneratorTest );

MessageSequenceGeneratorTest::MessageSequenceGeneratorTest() : MQS_INIT_LOGGER("tests.mqs.msgseqgen") {}

void MessageSequenceGeneratorTest::setUp() { }

void MessageSequenceGeneratorTest::tearDown() { }

void MessageSequenceGeneratorTest::testUniqueness() {
    MQS_LOG_INFO("**** TEST: " << __func__);

    mqs::MessageSequenceGenerator::Ptr idgen(mqs::MessageSequenceGenerator::newInstance());
    std::vector<std::string> msgIds;

    for (std::size_t i(0); i < 1000; i++) {
        msgIds.push_back(idgen->next());
    }

    std::string id("");
    for (std::vector<std::string>::iterator it(msgIds.begin()); it != msgIds.end(); it++) {
        CPPUNIT_ASSERT(id != *it);
        id = *it;
    }
}
