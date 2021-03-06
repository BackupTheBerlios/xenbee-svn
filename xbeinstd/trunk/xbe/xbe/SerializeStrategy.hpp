#ifndef XBE_SERIALIZE_STRATEGY_HPP
#define XBE_SERIALIZE_STRATEGY_HPP 1

#include <xbe/common/common.hpp>
#include <seda/ForwardStrategy.hpp>

namespace xbe {
    class SerializeStrategy : public seda::ForwardStrategy {
    public:
        SerializeStrategy(const std::string &name, const std::string &next);
        virtual ~SerializeStrategy() {}

        void perform(const seda::IEvent::Ptr &e);
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // ! XBE_SERIALIZE_STRATEGY_HPP
