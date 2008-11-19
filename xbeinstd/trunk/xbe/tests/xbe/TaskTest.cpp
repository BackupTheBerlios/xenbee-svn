#include "testsconfig.hpp"
#include "TaskTest.hpp"

#include <string>
#include <xbe/Task.hpp>
#include <signal.h>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( TaskTest );

TaskTest::TaskTest()
  : XBE_INIT_LOGGER("tests.xbe.task")
{}

void
TaskTest::setUp() {
}

void
TaskTest::tearDown() {
}

void
TaskTest::testNoExecutable() {
    Task task("not-existing-executable");
    task.run();
    task.wait();
    CPPUNIT_ASSERT_EQUAL(task.status(), Task::FINISHED);
    CPPUNIT_ASSERT(task.exitcode() == 127);
}

void
TaskTest::testSignal() {
    Task task("/bin/sleep");
    task.params().push_back("60");

    task.run();
    task.kill(SIGTERM);
    task.wait();
    CPPUNIT_ASSERT_EQUAL(Task::SIGNALED, task.status());
    CPPUNIT_ASSERT_EQUAL(15, task.exitcode());

    task.run();
    task.kill(SIGKILL);
    task.wait();
    CPPUNIT_ASSERT_EQUAL(Task::SIGNALED, task.status());
    CPPUNIT_ASSERT_EQUAL(9, task.exitcode());
}

void
TaskTest::testRun() {
    Task task("/bin/sleep");
    task.params().push_back("1");
    task.run();
    task.wait();

    CPPUNIT_ASSERT_EQUAL(Task::FINISHED, task.status());
    CPPUNIT_ASSERT_EQUAL(0, task.exitcode());
}

