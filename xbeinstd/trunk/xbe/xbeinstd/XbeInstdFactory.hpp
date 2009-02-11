#ifndef XBE_XBEINSTD_FACTORY_HPP
#define XBE_XBEINSTD_FACTORY_HPP 1

namespace xbe {
namespace xbeinstd {
    class XbeInstdFactory {
    public:
        /**
         * TODO: handle configuration stuff?
         */
        XbeInstdFactory();
        ~XbeInstdFactory();

        void start();
        void stop();

        void waitForSignals();
        void handleSignal(int signal);
    private:

    };
}}

#endif // ! XBE_XBEINSTD_FACTORY_HPP
