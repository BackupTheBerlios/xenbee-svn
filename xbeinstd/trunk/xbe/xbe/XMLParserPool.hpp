#ifndef XBE_PARSER_POOL_HPP
#define XBE_PARSER_POOL_HPP 1

#include <xbe/common.hpp>

#include <list>
#include <iostream>
#include <string>

#include <boost/thread.hpp>

#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xercesc/dom/DOM.hpp>

namespace xbe {
    class XMLParser {
        public:
            XMLParser();
            ~XMLParser();

            xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> parse (std::istream& is, const std::string& id = "", bool validate = true);
        private:
            xercesc::MemoryManager* _memMgr;
            xercesc::XMLGrammarPool* _grammarPool;
            xercesc::DOMBuilder* parser;
    };

    class XMLParserPool;
    class XMLParserManager {
        public:
            XMLParserManager(XMLParser* parser, XMLParserPool* pool)
                : _parser(parser), _pool(pool) {}

            ~XMLParserManager();

            xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> parse (std::istream& is, const std::string& id = "", bool validate = true) {
                return _parser->parse(is, id, validate);
            }
        private:
            XMLParser* _parser;
            XMLParserPool* _pool;
    };

    class XMLParserPool {
        public:

            typedef XMLParser parser_type;
            typedef std::list<parser_type*> container_type;

            explicit XMLParserPool(std::size_t maxPoolSize=5);
            ~XMLParserPool();

            std::auto_ptr<XMLParserManager> allocate();
            void release(XMLParser* parser);

        private:
            XBE_DECLARE_LOGGER();
            std::size_t _poolSize;
            std::size_t _maxPoolSize;
            boost::mutex _mtx;
            boost::condition_variable _free;
            container_type _pool;

            XMLParser* initializeNewParser() const;
    };
}

#endif // !XBE_PARSER_POOL_HPP
