#ifndef XBE_XBELIBUTILS_HPP
#define XBE_XBELIBUTILS_HPP 1

#include <xbe/XbeException.hpp>
#include <xbe/xbe-schema.hpp>

namespace xbe {
  class XbeLibUtils {
  public:
    ~XbeLibUtils() {}

    static void initialise() throw(xbe::XbeException);
    static void terminate() throw();

    static const xml_schema::namespace_infomap& namespace_infomap();
    
  private:
    XbeLibUtils() {}
  };
}

#endif // !XBE_XBELIBUTILS_HPP
