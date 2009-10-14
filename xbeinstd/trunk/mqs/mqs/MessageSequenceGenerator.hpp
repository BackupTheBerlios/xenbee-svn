#ifndef MQS_MESSAGE_SEQUENCE_GENERATOR_HPP
#define MQS_MESSAGE_SEQUENCE_GENERATOR_HPP 1

#include <string>
#include <boost/thread.hpp>
#include <mqs/memory.hpp>

namespace mqs {
    class MessageSequenceGenerator { 
        public:
            typedef shared_ptr<MessageSequenceGenerator> Ptr;

            static Ptr newInstance();

            std::string next();

            std::string operator()() {
                return next();
            }

            ~MessageSequenceGenerator() {}
        private:
            MessageSequenceGenerator(std::size_t globalId, std::size_t generatorId, const std::string &hostId);
            MessageSequenceGenerator(const MessageSequenceGenerator &);

            std::size_t _globalId;
            std::size_t _generatorId;
            std::string _hostId;
            std::size_t _counter;

            boost::mutex _mtx;
    };
}

#endif // ! MQS_MESSAGE_SEQUENCE_GENERATOR_HPP
