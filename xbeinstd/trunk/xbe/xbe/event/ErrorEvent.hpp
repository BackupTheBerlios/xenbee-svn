#ifndef XBE_ERROREVENT_HPP
#define XBE_ERROREVENT_HPP 1

#include <seda/SystemEvent.hpp>

namespace xbe {
    namespace event {
        class ErrorEvent : public seda::SystemEvent {
            public:
                ErrorEvent(const std::string& reason, const std::string& additionalData="");
                ~ErrorEvent();

                const std::string& reason() const;
                const std::string& additionalData() const;

                std::string str() const;
            private:
                std::string _reason;
                std::string _additionalData;
        };
    }
}

#endif // !XBE_ERROREVENT_HPP
