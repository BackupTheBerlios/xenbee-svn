#include <iostream>
#include <fstream>
#include <xbe/XbeLibUtils.hpp>

void usage(const std::string& progname) {
    std::cout << "usage: " << progname << std::endl;
}

int main (int argc, char** argv) {
    // read from stdin
    try {
        xbe::XbeLibUtils::initialise();
        xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(xbe::XbeLibUtils::parse(std::cin));
        xbe::XbeLibUtils::terminate();
    } catch (xml_schema::exception& e) {
        std::cerr << "parsing failed: " << e << std::endl;
        exit(1);
    } catch (std::exception& ex) {
        std::cerr << "parsing failed: " << ex.what() << std::endl;
        exit(1);
    }
}
