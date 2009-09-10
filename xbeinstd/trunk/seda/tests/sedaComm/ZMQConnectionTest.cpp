#include "ZMQConnectionTest.hpp"

#include <iostream>
#include <string>
#include <stdexcept>
#include <signal.h>
#include <sys/wait.h>

#include <seda/seda-config.hpp>
#include <seda/comm/SedaMessage.hpp>
#include <seda/comm/ZMQConnection.hpp>
#include <seda/comm/ConnectionFactory.hpp>

using namespace seda::comm::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ZMQConnectionTest );

void sighandler(int signal) {
  std::clog << "got signal: " << signal << std::endl;
}

ZMQConnectionTest::ZMQConnectionTest()
  : SEDA_INIT_LOGGER("tests.seda.comm.ZMQConnectionTest")
  , zmq_server_port_(5682)
  , zmq_server_pid_(-1)
{
}

ZMQConnectionTest::~ZMQConnectionTest()
{
}

void
ZMQConnectionTest::setUp() {
  start_zmq_server(&zmq_server_pid_, &zmq_server_port_);
}

void
ZMQConnectionTest::tearDown() {
  stop_zmq_server(&zmq_server_pid_);
}

void
ZMQConnectionTest::testConnectionFactory() {
  seda::comm::ConnectionParameters params("zmq", "localhost", "test");
  params.put("iface_in", "*:5222");
  params.put("iface_out", "*");
  try {
    seda::comm::ConnectionFactory::ptr_t factory(new seda::comm::ConnectionFactory());
    seda::comm::Connection::ptr_t conn = factory->createConnection(params);
    conn->start();
    seda::comm::SedaMessage msg1("test", "test", "foo");
    conn->send(msg1);

    seda::comm::SedaMessage msg2;
    conn->recv(msg2);
    CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());
    conn->stop();
  }
  catch (const std::exception &ex) {
    SEDA_LOG_ERROR("could not create the connection: " << ex.what());
    CPPUNIT_ASSERT_MESSAGE("connection could not be created!", false);
  }
  catch (...)
  {
    CPPUNIT_ASSERT_MESSAGE("connection could not be created: unknown reason!", false);
  }
}

void
ZMQConnectionTest::testSendReceive() {
  seda::comm::ZMQConnection conn("localhost", "test", "*:5222", "*");
  try {
    conn.start();
  } catch (const std::exception &ex) {
    SEDA_LOG_ERROR("could not start the zmq-connection: " << ex.what());
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  } catch(...) {
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  }
  for (std::size_t cnt(0); cnt < 1000; ++cnt)
  {
    std::ostringstream ostr;
    ostr << "foo " << cnt;
    seda::comm::SedaMessage msg1("test", "test", ostr.str());
    conn.send(msg1);
    seda::comm::SedaMessage msg2;
    conn.recv(msg2);
    CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());
  }
  conn.stop();
}

void
ZMQConnectionTest::testStartStop() {
  seda::comm::ZMQConnection conn("localhost", "test", "*:5222", "*");
  try {
    // FIXME: this segfaults for larger loop-counts! problem of libzmq!
    for (std::size_t i(0); i < 3; i++) {
      conn.start();

      seda::comm::SedaMessage msg1("test", "test", "foo");
      conn.send(msg1);
      seda::comm::SedaMessage msg2;
      conn.recv(msg2);
      CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());

      conn.stop();
      sleep(1);
    }
  } catch (const std::exception &ex) {
    SEDA_LOG_ERROR("could not start the zmq-connection: " << ex.what());
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  } catch(...) {
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  }
}


void
ZMQConnectionTest::testAbortException() {
  // register a signal handler for SIGABRT
  signal(SIGABRT, sighandler);
  // and throw an exception
  bool got_exception(false);
  try {
    throw std::runtime_error("42");
  } catch(const std::runtime_error &ex) {
    got_exception = true;
    const std::string expected("42");
    const std::string actual(ex.what());
    CPPUNIT_ASSERT_EQUAL(expected, actual);
  }
  CPPUNIT_ASSERT(got_exception);
}

bool ZMQConnectionTest::start_zmq_server(pid_t *pid, uint32_t *port)
{
  const std::string zmq_server_path(ZMQ_SERVER_PATH);
  if (0 == zmq_server_path.size())
  {
    SEDA_LOG_WARN("I have not path to the zmq_server, please define ZMQ_SERVER_PATH!");
    return false;
  }
  SEDA_LOG_INFO("starting zmq_server (" << zmq_server_path << ") on port " << *port);
  *pid = fork();
  if (0 == *pid)
  {
    if (execl(zmq_server_path.c_str(), "zmq_server", (char*)NULL) < 0)
    {
      exit(errno);
    }
  }
  else
  {
    SEDA_LOG_INFO("forked with pid: " << *pid);
  }
  sleep(0.5);
  int status;
  if (waitpid(*pid, &status, WNOHANG) != 0)
  {
    SEDA_LOG_ERROR("zmq_server could not be started: " << WEXITSTATUS(status));
    return false;
  }
}

bool ZMQConnectionTest::stop_zmq_server(pid_t *pid)
{
  if (*pid <= 0)
  {
    SEDA_LOG_WARN("zmq_server has not been started, but we are trying to stop it.");
    return false;
  }

  if (0 == kill(*pid, 0))
  {
    // process seems to be alive and we are allowed to send signals
    for (std::size_t trial(0); trial < 3; ++trial)
    {
      SEDA_LOG_INFO("sending SIGTERM to " << *pid);
      kill(*pid, SIGTERM);
      sleep(1);
      if (0 != kill(*pid, 0)) break;
    }
  }

  if (0 == kill(*pid, 0))
  {
    SEDA_LOG_WARN("sending SIGKILL to " << *pid);
    kill(*pid, SIGKILL);
  }
  *pid = -1;
  return true;
}
