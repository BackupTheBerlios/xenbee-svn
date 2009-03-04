#include "MessageSequenceGenerator.hpp"

#include <mqs/common.hpp>
#include <boost/random.hpp>
#include <sstream>

using namespace mqs;

MessageSequenceGenerator::MessageSequenceGenerator(std::size_t globalId, std::size_t generatorId, const std::string &hostId)
    : _globalId(globalId), _generatorId(generatorId), _hostId(hostId), _counter(0)
{ }

MessageSequenceGenerator::Ptr MessageSequenceGenerator::newInstance() {
    static std::size_t GENERATOR_ID(0);

    // TODO: has to be atomic
    std::size_t generatorId(GENERATOR_ID++);

    // get the hostname
    char hostId[HOST_NAME_MAX+1];
    gethostname(hostId, sizeof(hostId)); hostId[HOST_NAME_MAX] = (char)0;

    // get a random ID for this generator to be unique between different adress spaces
    boost::minstd_rand rng((std::size_t)getpid());
//    boost::uniform_int<std::size_t> ints(1, std::numeric_limits<std::size_t>::max());
    boost::uniform_int<std::size_t> ints(1, 9999);
    boost::variate_generator<boost::minstd_rand&, boost::uniform_int<std::size_t> > randomNumber(rng, ints);
    std::size_t globalId(randomNumber());

    return MessageSequenceGenerator::Ptr(new MessageSequenceGenerator(globalId, generatorId, std::string(hostId)));
}

std::string MessageSequenceGenerator::next() {
    std::size_t count;
    {
        boost::unique_lock<boost::mutex> lock(_mtx);
        count = _counter++;
    } 

    time_t tstamp(time(NULL));
    std::stringstream sstr;
    sstr << _hostId << ":" << tstamp << ":" << _globalId << ":" << _generatorId << ":" << count;
    return sstr.str();
}

