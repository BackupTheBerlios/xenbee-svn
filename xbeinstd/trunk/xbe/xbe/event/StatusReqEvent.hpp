#ifndef XBE_STATUS_REQ_EVENT_HPP
#define XBE_STATUS_REQ_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class StatusReqEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<StatusReqEvent> Ptr;

                StatusReqEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "StatusReqEvent", dst, src),
                  XBE_INIT_LOGGER("StatusReqEvent"), execute_status_task_(true) {}

                virtual ~StatusReqEvent() {}
                bool execute_status_task() const { return execute_status_task_; }
                void execute_status_task(bool exec) { execute_status_task_ = exec; }

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);
            private:
                XBE_DECLARE_LOGGER();
                bool execute_status_task_;
        };
    }
}

#endif // !XBE_STATUS_REQ_EVENT_HPP
