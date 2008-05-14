#ifndef XBE_XBELIBUTILS_HPP
#define XBE_XBELIBUTILS_HPP 1

#include <xbe/XbeException.hpp>
#include <xbe/xbe-msg.hpp>

namespace xbe {
    class XbeLibUtils {
    public:
        ~XbeLibUtils() {}

        static void initialise() throw(xbe::XbeException);
        static void terminate() throw();

        static xml_schema::namespace_infomap& namespace_infomap();
        static xml_schema::properties& schema_properties();
    
    private:
        XbeLibUtils() {}
    };
}

#endif // !XBE_XBELIBUTILS_HPP
