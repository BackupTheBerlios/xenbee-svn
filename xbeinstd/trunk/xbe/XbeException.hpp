#ifndef XBE_XBE_EXCEPTION_HPP
#define XBE_XBE_EXCEPTION_HPP 1

#include <string>
#include <exception>

namespace xbe {
  class XbeException : public std::exception {
  public:
    explicit
    XbeException(const std::string& reason) :
      _reason(reason) {}
    virtual ~XbeException() throw() {}
    virtual const char* what() const throw() { return reason().c_str(); }
    virtual const std::string& reason() const { return _reason; }

  protected:
    std::string _reason;
  };
}

#endif // !XBE_XBE_EXCEPTION_HPP
