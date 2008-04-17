#include <mqs/Response.hpp>
#include <mqs/Destination.hpp>
#include <iostream>

int main (int argc, char** argv) {
  mqs::Response *r = new mqs::Response("test");
  r->await(1000);
  std::cout << "response is " << r->getResponse() << std::endl;

  try {
    mqs::Destination d("queue:foo.bar?k1=v1&k2=v2");
    std::cout << d << std::endl;
  } catch (const std::exception& e) {
    std::cerr << "exception:" << e.what() << std::endl;
  }
}
