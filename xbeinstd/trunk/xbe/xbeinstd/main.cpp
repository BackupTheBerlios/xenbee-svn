#include <fstream>
#include <boost/program_options.hpp>
#include <signal.h>

#include <xbe/common.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/XbeLibUtils.hpp>
#include <xbe/XbeInstd.hpp>
#include <xbe/MessageTranslatorStrategy.hpp>
#include <xbe/XMLSerializeStrategy.hpp>
#include <xbe/XMLDeserializeStrategy.hpp>
#include <xbe/XMLDataBinder.hpp>
#include <xbe/XMLDataUnbinder.hpp>
#include <xbe/XbeXMLMessageHandling.hpp>

#include <seda/StageFactory.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#if ENABLE_LOGGING
#include <log4cpp/BasicConfigurator.hh>
#include <log4cpp/Priority.hh>
#endif

namespace po = boost::program_options;

bool done(false);
void signalHandler(int signal) {
    done = true;
}

int
main(int argc, char **argv) {
    po::options_description desc("Allowed Options");
    desc.add_options()
        ("help,h", "show this information")
        ("broker", po::value<std::string>(), "URI to the MQS broker")
        ("xbed", po::value<std::string>(), "Queue name of the XenBEE daemon")
        ("name", po::value<std::string>(), "Queue name of this instance daemon")
        ("verbose,v", po::value<int>()->implicit_value(1), "verbosity level")
        ("config", po::value<std::string>()->default_value(std::string(INSTALL_PREFIX) + "/etc/xbe/xbeinstd.rc"), "path to configuration file")
        ;

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    std::ifstream configIFS(vm["config"].as<std::string>().c_str());
    if (configIFS) {
        std::cerr << "Reading configuration from " << vm["config"].as<std::string>() << std::endl;
        po::store(po::parse_config_file(configIFS, desc), vm);
    } else {
        std::cerr << "configuration file " << vm["config"].as<std::string>() << " does not exist!" << std::endl;
    }
    po::notify(vm);

    if (vm.count("help")) {
        std::cerr << desc << std::endl;
        return 1;
    }
    if (! vm.count("broker")) {
        std::cerr << "Sorry, a broker is required!" << std::endl;
        return 1;
    }
    if (! vm.count("xbed")) {
        std::cerr << "Sorry, i require a name for the xbe-daemon queue!" << std::endl;
        return 1;
    }
    if (! vm.count("name")) {
        std::cerr << "Sorry, i require a name for my own queue!" << std::endl;
        return 1;
    }


    // setup logging
#if ENABLE_LOGGING
    ::log4cpp::BasicConfigurator::configure();
    ::log4cpp::Category::setRootPriority(::log4cpp::Priority::FATAL);
    if (vm.count("verbose")) {
        int level(vm["verbose"].as<int>());
        if      (level > 4) ::log4cpp::Category::setRootPriority(::log4cpp::Priority::DEBUG);
        else if (level > 3) ::log4cpp::Category::setRootPriority(::log4cpp::Priority::INFO);
        else if (level > 2) ::log4cpp::Category::setRootPriority(::log4cpp::Priority::WARN);
        else if (level > 1) ::log4cpp::Category::setRootPriority(::log4cpp::Priority::ERROR);
        else if (level > 0) ::log4cpp::Category::setRootPriority(::log4cpp::Priority::CRIT);
    }
#endif

    // set up the whole application environment
    try {
        xbe::XbeLibUtils::initialise();
        seda::StageFactory::Ptr factory(new seda::StageFactory());

        // channel
        mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(vm["broker"].as<std::string>()), vm["name"].as<std::string>()));
        seda::Strategy::Ptr chan2xml(new seda::ForwardStrategy("xbe.xml-parse"));
        chan2xml = seda::Strategy::Ptr(new seda::LoggingStrategy(chan2xml));
        chan2xml = seda::Strategy::Ptr(new xbe::ChannelAdapterStrategy("xbe.channeladapter", chan2xml, channel));
        factory->createStage("xbe.net", chan2xml);

        // parse and bind text to xsd-objects
        seda::Strategy::Ptr txt2obj(new seda::ForwardStrategy("xbe.obj-to-evt"));
        txt2obj = seda::Strategy::Ptr(new xbe::XbeXMLDataBinder(txt2obj));
        txt2obj = seda::Strategy::Ptr(new seda::LoggingStrategy(txt2obj));
        txt2obj = seda::Strategy::Ptr(new xbe::XMLDeserializeStrategy(txt2obj));
        factory->createStage("xbe.xml-parse", txt2obj);
 
        // transform objects into events
        seda::Strategy::Ptr obj2evt(new seda::ForwardStrategy("xbe.xbeinstd"));
        obj2evt = seda::Strategy::Ptr(new xbe::MessageTranslatorStrategy(obj2evt));
        factory->createStage("xbe.obj-to-evt", obj2evt);

        xbe::XbeInstd::Ptr xbeinstd(new xbe::XbeInstd("xbe.xbeinstd",
                                                 seda::Strategy::Ptr(new seda::ForwardStrategy("xbe.evt-to-obj")),
                                                 vm["xbed"].as<std::string>(),
                                                 vm["name"].as<std::string>()
                                                 ));
        factory->createStage("xbe.xbeinstd", xbeinstd);
 
        // transform events into objects
        seda::Strategy::Ptr evt2obj(new seda::ForwardStrategy("xbe.obj-to-xml"));
        evt2obj = seda::Strategy::Ptr(new xbe::MessageTranslatorStrategy(evt2obj));
        factory->createStage("xbe.evt-to-obj", evt2obj);

        // transform xsd-objects to text
        seda::Strategy::Ptr obj2txt(new seda::ForwardStrategy("xbe.net"));
        obj2txt = seda::Strategy::Ptr(new xbe::XMLSerializeStrategy(obj2txt));
        obj2txt = seda::Strategy::Ptr(new seda::LoggingStrategy(obj2txt));
        obj2txt = seda::Strategy::Ptr(new xbe::XbeXMLDataUnbinder(obj2txt));
        factory->createStage("xbe.obj-to-xml", obj2txt);

        // register signal handler
        signal(SIGINT, signalHandler);

        std::cerr << "starting stages..." << std::endl;
        seda::StageRegistry::instance().startAll();

        // wait ...
        while (! done ) {
            
            xbeinstd->wait(500);
        }

        std::cerr << "shutting down..." << std::endl;
        seda::StageRegistry::instance().stopAll();
     } catch (...) {

    }    

    return 0;
}
