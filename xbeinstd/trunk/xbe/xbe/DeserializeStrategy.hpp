#ifndef XBE_DESERIALIZE_STRATEGY_HPP
#define XBE_DESERIALIZE_STRATEGY_HPP 1

#include <seda/ForwardStrategy.hpp>
#include <xbe/common/common.hpp>

namespace xbe {
    class DeserializeStrategy : public seda::ForwardStrategy {
    public:
        DeserializeStrategy(const std::string &name, const std::string &next);
        virtual ~DeserializeStrategy() {}

        void perform(const seda::IEvent::Ptr &e);
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // ! XBE_DESERIALIZE_STRATEGY_HPP
