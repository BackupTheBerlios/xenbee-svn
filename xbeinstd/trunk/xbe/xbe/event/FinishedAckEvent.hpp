#ifndef XBE_FINISHED_ACK_EVENT_HPP
#define XBE_FINISHED_ACK_EVENT_HPP 1

#include <xbe/common/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedAckEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<FinishedAckEvent> Ptr;

                FinishedAckEvent(const std::string &conversationID, const mqs::Destination &dst="", const mqs::Destination &src="")
                : DecodedMessageEvent(conversationID, "FinishedAck", dst, src), XBE_INIT_LOGGER("FinishedAckEvent"), task_id_(-1) {}
                virtual ~FinishedAckEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);

                FinishedAckEvent *task_id(int tid) { task_id_ = tid; return this; }
                int task_id() const { return task_id_; }

            private:
                XBE_DECLARE_LOGGER();
                int task_id_;
        };
    }
}

#endif // !XBE_FINISHED_ACK_EVENT_HPP
