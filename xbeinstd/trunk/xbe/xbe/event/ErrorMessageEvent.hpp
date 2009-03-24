#ifndef XBE_EVENT_ERROR_MESSAGE_EVENT_HPP
#define XBE_EVENT_ERROR_MESSAGE_EVENT_HPP 1

#include <xbe/common/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
namespace event {
    class ErrorMessageEvent : public xbe::event::DecodedMessageEvent {
    public:
        typedef std::tr1::shared_ptr<ErrorMessageEvent> Ptr;
        typedef int ErrorCode;

        ErrorMessageEvent(const std::string &conversation_id,
                          const mqs::Destination &dst = "",
                          const mqs::Destination &src = "")
            : DecodedMessageEvent(conversation_id, "ErrorMessageEvent", dst, src),
              XBE_INIT_LOGGER("xbe.event.ErrorMessageEvent"),
              error_code_(0), error_msg_("") {}

        virtual ~ErrorMessageEvent() {}

        const std::string &error_msg() const { return error_msg_; }
        ErrorMessageEvent *error_msg(const std::string &msg) { error_msg_ = msg; return this; }

        const ErrorCode &error_code() const { return error_code_; }
        ErrorMessageEvent *error_code(ErrorCode code) { error_code_ = code; return this; }

        std::string str() const;
        std::string serialize() const;
        static ErrorMessageEvent::Ptr deserialize(const std::string &s);

    private:
        XBE_DECLARE_LOGGER();
        ErrorCode error_code_;
        std::string error_msg_;
    };
}
}

#endif // ! XBE_EVENT_ERROR_MESSAGE_EVENT_HPP


