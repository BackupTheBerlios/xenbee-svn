#ifndef XBE_CONVERSATION_HPP
#define XBE_CONVERSATION_HPP 1

#include <mqs/Destination.hpp>
#include <xbe/shared_ptr.hpp>

namespace xbe {
    class Conversation {
    public:
        typedef std::tr1::shared_ptr<Conversation> Ptr;
        Conversation(const std::string &id, const mqs::Destination &peer)
        : id_(id), peer_(peer) { }

        const std::string &id() const { return id_; }
        const mqs::Destination &peer() const { return peer_; }

    private:
        std::string id_;
        mqs::Destination peer_;
    };
}

#endif // ! XBE_CONVERSATION
