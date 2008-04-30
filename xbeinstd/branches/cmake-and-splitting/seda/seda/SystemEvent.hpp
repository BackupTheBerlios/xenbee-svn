#ifndef SEDA_SYSTEM_EVENT_HPP
#define SEDA_SYSTEM_EVENT_HPP

#include <seda/IEvent.hpp>

namespace seda {
    /**
     * SystemEvents are special events that should be forwarded from stage
     * to stage until they can be handled.
     * 
     * Strategies must not attempt to transform them in any way, a special
     * stage may be  registered to handle SystemEvents (the  stage must be
     * called  "seda.system.stage", if  such  a stage  is registered,  the
     * event should be passed to that stage.
     */
    class SystemEvent : public IEvent {
    public:
        typedef std::tr1::shared_ptr<SystemEvent> Ptr;
    
        virtual ~SystemEvent() {}
    protected:
        SystemEvent() {}
    };
}

#endif // !SEDA_SYSTEM_EVENT_HPP
