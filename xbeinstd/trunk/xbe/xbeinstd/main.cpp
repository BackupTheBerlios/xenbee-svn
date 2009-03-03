#include <fstream>
#include <boost/program_options.hpp>
#include <signal.h>

#include <xbe/common.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/SerializeStrategy.hpp>
#include <xbe/DeserializeStrategy.hpp>
#include <xbe/XbeInstd.hpp>

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
    std::cerr << "done" << std::endl;
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
        seda::StageFactory::Ptr factory(new seda::StageFactory());

        // channel
        mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(vm["broker"].as<std::string>()), vm["name"].as<std::string>()));
        seda::Strategy::Ptr net(new seda::ForwardStrategy("xbe.decode"));
        net = seda::Strategy::Ptr(new seda::LoggingStrategy(net));
        net = seda::Strategy::Ptr(new xbe::ChannelAdapterStrategy("xbe.channeladapter", net, channel));
        factory->createStage("xbe.net", net);
        std::cerr << "created stage xbe.net" << std::endl;

        // decode messages stage
        seda::Strategy::Ptr decode(new xbe::DeserializeStrategy("xbe.decode.strategy", "xbe.xbeinstd"));
        decode = seda::Strategy::Ptr(new seda::LoggingStrategy(decode));
        factory->createStage("xbe.decode", decode);
        std::cerr << "created stage xbe.decode" << std::endl;

        // encode messages stage
        seda::Strategy::Ptr encode(new xbe::SerializeStrategy("xbe.encode.strategy", "xbe.net"));
        encode = seda::Strategy::Ptr(new seda::LoggingStrategy(encode));
        factory->createStage("xbe.encode", encode);
        std::cerr << "created stage xbe.encode" << std::endl;

        xbe::XbeInstd::Ptr xbeinstd(new xbe::XbeInstd("xbe.xbeinstd",
                    seda::Strategy::Ptr(new seda::ForwardStrategy("xbe.encode")),
                    vm["xbed"].as<std::string>(),
                    vm["name"].as<std::string>(),
                    "conv-id:1234"
                    ));
        factory->createStage("xbe.xbeinstd", xbeinstd);
        std::cerr << "created stage xbe.xbeinstd" << std::endl;

        // register signal handler
        signal(SIGINT, signalHandler);

        std::cerr << "starting stages..." << std::endl;
        seda::StageRegistry::instance().startAll();

        // wait ...
        std::cerr << "waiting..." << std::endl;
        while (! done ) {
            xbeinstd->wait(500);
        }

        std::cerr << "shutting down..." << std::endl;
        seda::StageRegistry::instance().stopAll();
        seda::StageRegistry::instance().clear();
    } catch (...) {
        std::cerr << "an unknown error occured" << std::endl;
    }    

    return 0;
}
