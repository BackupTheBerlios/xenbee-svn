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
    Task task(TaskData("not-existing-executable"));
    task.run();
    task.wait();
    CPPUNIT_ASSERT_EQUAL(task.status(), Task::FAILED);
    CPPUNIT_ASSERT(task.exitcode() == 127);
}

void
TaskTest::testSignal() {
    TaskData td("/bin/sleep");
    td.params().push_back("60");

    Task task(td);

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
    TaskData td("/bin/sleep");
    td.params().push_back("1");

    Task task(td);

    task.run();
    task.wait();

    CPPUNIT_ASSERT_EQUAL(Task::FINISHED, task.status());
    CPPUNIT_ASSERT_EQUAL(0, task.exitcode());
}

