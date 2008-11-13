#ifndef XBE_OBJECT_EVENT_HPP
#define XBE_OBJECT_EVENT_HPP 1

#include <seda/UserEvent.hpp>
#include <memory>

namespace xbe {
    namespace event {
        template <class T>
            class ObjectEvent : public seda::UserEvent {
                public:
                    ObjectEvent(const std::string& to,
                            const std::string& from,
                            ::std::auto_ptr< T > obj)
                        : _to(to), _from(from), _obj(obj) {

                        } 

                    virtual ~ObjectEvent() {}

                    const std::string& to() const { return _to; }
                    const std::string& from() const { return _from; }

                    const std::auto_ptr<T> const_object() const { return _obj; }
                    std::auto_ptr<T> object() { return _obj; }

                    const T& const_payload() const { return *_obj; }
                    T& payload() { return *_obj; }

                    virtual std::string str() const {
                        return "Object-Message: " + from() + " --> " + to();
                    }
                private:
                    std::string _to;
                    std::string _from;
                    ::std::auto_ptr< T > _obj;
            };
    }
}

#endif // !XBE_OBJECT_EVENT_HPP
