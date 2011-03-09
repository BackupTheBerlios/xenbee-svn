#include <fstream>
#include <mqs/common.hpp>

#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/CompilerOutputter.h>
#include <cppunit/XmlOutputter.h>
#include <cppunit/TestResult.h>
#include <cppunit/TestResultCollector.h>
#include <cppunit/TextTestRunner.h>
#include <cppunit/ui/text/TestRunner.h>
#include <cppunit/TextTestProgressListener.h>
#include <cppunit/BriefTestProgressListener.h>
#include <cppunit/TestFailure.h>
#include <cppunit/Test.h>

#include <cppunit/XmlOutputterHook.h>
#include <cppunit/tools/XmlElement.h>
#include <cppunit/tools/StringTools.h>
#include <cppunit/tools/XmlDocument.h>
#include <cppunit/TestFailure.h>
#include <cppunit/SourceLine.h>
#include <cppunit/Exception.h>
#include <cppunit/Message.h>

int
main(int argc, char **argv) {
#if ENABLE_LOGGING == 1
    mqscommon::LoggingConfigurator::configure();
#endif
    
  CPPUNIT_NS::TestResult           testresult;
  CPPUNIT_NS::TestResultCollector  collectedresults;
  testresult.addListener (&collectedresults);

#if 0
  CPPUNIT_NS::TestRunner runner;
  CPPUNIT_NS::TestFactoryRegistry &registry = CPPUNIT_NS::TestFactoryRegistry::getRegistry();
  runner.addTest( registry.makeTest() );

  runner.run (testresult);
  std::ofstream outStream("out.xml");
  CPPUNIT_NS::XmlOutputter xmloutputter (&collectedresults, outStream);
  //CPPUNIT_NS::XmlOutputter xmloutputter (&collectedresults, std::cout);
  xmloutputter.write ();
  bool wasSuccessful = collectedresults.wasSuccessful () ;
#else
  CPPUNIT_NS::TextUi::TestRunner runner;
  CPPUNIT_NS::TestFactoryRegistry &registry = CPPUNIT_NS::TestFactoryRegistry::getRegistry();
  runner.addTest( registry.makeTest() );

    CPPUNIT_NS::CompilerOutputter *outputter =
        new CPPUNIT_NS::CompilerOutputter(&runner.result(), std::cout);
    outputter->setLocationFormat("%p(%l) : ");
    //outputter->setWrapColumn(19);
    outputter->setNoWrap();
    runner.setOutputter(outputter);
    bool wasSuccessful = runner.run("",
                                    false, // doWait
                                    true,  // doPrintResult
                                    true   // doPrintProgress
                                    );
#endif
    return !wasSuccessful;  
}
