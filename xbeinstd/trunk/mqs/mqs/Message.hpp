#ifndef MQS_MESSAGE_HPP
#define MQS_MESSAGE_HPP 1

#include <string>
#include <mqs/memory.hpp>
#include <mqs/MQSException.hpp>
#include <mqs/Destination.hpp>

namespace mqs {
    class Message {
        public:
            typedef shared_ptr<Message> Ptr;

            Message(const std::string &body, const mqs::Destination &from, const mqs::Destination &to)
                : _id(""),
                  _correlation(""),
                  _body(body),
                  _from(from),
                  _to(to),
                  _size(body.size()),
                  _ttl(to.getIntProperty("timeToLive", 0)),
                  _priority(to.getIntProperty("priority", 0)),
                  _deliveryMode(1) {
                std::string mode(to.getStringProperty("deliveryMode", "non-persistent"));
                if (mode == "persistent") {
                    _deliveryMode = 0;
                } else if (mode == "non-persistent") {
                    _deliveryMode = 1;
                } else {
                    throw MQSException("unsupported delivery mode: " + mode);
                }
            }

            Message(const Message &m)
                : _id(m.id()),
                  _correlation(m.correlation()),
                  _body(m.body()),
                  _from(m.from()),
                  _to(m.to()),
                  _size(m.size()),
                  _ttl(m.ttl()),
                  _priority(m.priority()),
                  _deliveryMode(m.deliveryMode()) { }

            ~Message() {}

            const std::string &body() const { return _body; }
            const std::size_t size() const { return _size; }
            const std::string &id() const { return _id; }
            const std::string &correlation() const { return _correlation; }

            void body(const std::string &body) { _body = body; }
            void id(const std::string &id) { _id = id; }
            void correlation(const std::string &cid) { _correlation = cid; }

            const mqs::Destination &from() const { return _from; }
            const mqs::Destination &to() const { return _to; }
            long long ttl() const { return _ttl; }
            int priority() const { return _priority; }
            int deliveryMode() const { return _deliveryMode; }

            void from(const mqs::Destination &d) { _from = d; }
            void to(const mqs::Destination &d) { _to = d; }
            void ttl(long long ttl) { _ttl = ttl; }
            void priority(int priority) { _priority = priority; }
            void deliveryMode(int mode) { _deliveryMode = mode; }

        private:
            std::string _id;
            std::string _correlation;
            std::string _body;
            mqs::Destination _from;
            mqs::Destination _to;
            std::size_t _size;

            long long _ttl;
            int _priority;
            int _deliveryMode;
    };

    /*
    class MessageFactory {
        public:
            MessageFactory() {}

            Message::Ptr createMessage(cms::Message *msg);
    };
    */
}

#endif // !MQS_MESSAGE_HPP
