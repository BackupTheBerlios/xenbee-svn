#ifndef XBE_XBE_XML_MESSAGE_HANDLING_HPP
#define XBE_XBE_XML_MESSAGE_HANDLING_HPP 1

#include <xbe/XbeLibUtils.hpp>
#include <xbe/ObjectEvent.hpp>
#include <xbe/xbe-msg.hpp>
#include <xbe/XMLDataBinder.hpp>
#include <xbe/XMLDataUnbinder.hpp>

namespace xbe {
    struct XbeXMLObjectParser {
        ::std::auto_ptr< ::xbemsg::message_t > operator()(::xml_schema::dom::auto_ptr< ::xercesc::DOMDocument >& d,
                ::xml_schema::flags f = 0,
                const ::xml_schema::properties& p = ::xml_schema::properties ()) {
            return ::xbemsg::message(d, f, p);
        }
        ::std::auto_ptr< ::xbemsg::message_t > operator()(const ::xercesc::DOMDocument& d,
                ::xml_schema::flags f = 0,
                const ::xml_schema::properties& p = ::xml_schema::properties ()) {
            return ::xbemsg::message(d, f, p);
        }
    };

    struct XbeXMLObjectSerializer {
        ::xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > operator()(const ::xbemsg::message_t& xml_object,
                const ::xml_schema::namespace_infomap& m = XbeLibUtils::namespace_infomap(), ::xml_schema::flags f = 0) {
            return ::xbemsg::message(xml_object, m, f);
        }
        ::xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > operator()(const std::auto_ptr< ::xbemsg::message_t > xml_object,
                const ::xml_schema::namespace_infomap& m = XbeLibUtils::namespace_infomap(), ::xml_schema::flags f = 0) {
            return ::xbemsg::message(*(xml_object), m, f);
        }
    };

    typedef ObjectEvent< xbemsg::message_t > XbeMessageEvent;
    typedef XMLDataBinder< xbemsg::message_t, XbeXMLObjectParser > XbeXMLDataBinder;
    typedef XMLDataUnbinder< xbemsg::message_t, XbeXMLObjectSerializer > XbeXMLDataUnbinder;
}

#endif // !XBE_XBE_XML_MESSAGE_HANDLING_HPP
