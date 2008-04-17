#include "XbeLibUtils.hpp"

#include <xercesc/util/PlatformUtils.hpp>
#include <xsec/utils/XSECPlatformUtils.hpp>
#ifndef XSEC_NO_XALAN
#include <xalanc/XalanTransformer/XalanTransformer.hpp>
#endif

using namespace xbe;

#ifdef XALAN_CPP_NAMESPACE_USE
XALAN_CPP_NAMESPACE_USE
#endif

#ifdef XERCES_CPP_NAMESPACE_USE
XERCES_CPP_NAMESPACE_USE
#endif

void XbeLibUtils::initialise() throw (xbe::XbeException) {
  XMLPlatformUtils::Initialize();
#ifndef XSEC_NO_XALAN
  XalanTransformer::initialize();
#endif
  XSECPlatformUtils::Initialise(/*XSECCryptoProvider = NULL*/);

  // TODO: make this configurable
  // initalize namespace map
  xml_schema::namespace_infomap& map = const_cast<xml_schema::namespace_infomap&>(namespace_infomap());
  map["xbe"].name = "http://www.xenbee.net/schema/2008/02/xbe";
  map["jsdl"].name = "http://schemas.ggf.org/jsdl/2005/11/jsdl";
  map["jsdl-posix"].name = "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix";
  map["dsig"].name = "http://www.w3.org/2000/09/xmldsig#";
  map["xenc"].name = "http://www.w3.org/2001/04/xmlenc#";
}

void XbeLibUtils::terminate() throw () {
  try {
    XSECPlatformUtils::Terminate();
  } catch(...) {
    // ignore
  }

#ifndef XSEC_NO_XALAN
  XalanTransformer::terminate();
#endif

  try {
    XMLPlatformUtils::Terminate();
  } catch (...) {
    // ignore!
  }
}

const xml_schema::namespace_infomap& XbeLibUtils::namespace_infomap() {
  static xml_schema::namespace_infomap map;
  return map;
}
