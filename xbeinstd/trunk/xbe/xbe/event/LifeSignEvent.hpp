#ifndef XBE_LIFE_SIGN_EVENT_HPP
#define XBE_LIFE_SIGN_EVENT_HPP 1

#include <xbe/common.hpp>
#include <sys/time.h>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class LifeSignEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<LifeSignEvent> Ptr;

                LifeSignEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : DecodedMessageEvent(conversation_id, "LifeSign", dst, src),
                  XBE_INIT_LOGGER("LifeSignEvent"), tstamp_(time(NULL)) {}
                virtual ~LifeSignEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &s);

                LifeSignEvent *tstamp(int tstamp) { tstamp_ = tstamp; return this; }
                int tstamp() const { return tstamp_; }
            private:
                XBE_DECLARE_LOGGER();
                int tstamp_;
        };
    }
}

#endif // !XBE_LIFE_SIGN_EVENT_HPP
