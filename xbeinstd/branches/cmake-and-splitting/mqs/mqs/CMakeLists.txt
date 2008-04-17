SET(mqs_src common.h common.cpp logging.hpp
  Response.hpp DestinationProperties.hpp DestinationProperties.cpp
  Destination.hpp Destination.cpp
  Channel.hpp Channel.cpp BrokerURI.hpp)

ADD_LIBRARY(mqs ${mqs_src})
