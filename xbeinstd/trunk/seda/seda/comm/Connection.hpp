/*
 * =====================================================================================
 *
 *       Filename:  Connection.hpp
 *
 *    Description:  defines the interface to a generic connection
 *
 *        Version:  1.0
 *        Created:  09/08/2009 02:34:26 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Alexander Petry (petry), alexander.petry@itwm.fraunhofer.de
 *        Company:  Fraunhofer ITWM
 *
 * =====================================================================================
 */

#ifndef SEDA_COMM_CONNECTION_HPP
#define SEDA_COMM_CONNECTION_HPP

#include <seda/comm/SedaMessage.hpp>

namespace seda { namespace comm {
  class Connection {
  public:
    virtual void start() = 0;
    virtual void stop() = 0;

    virtual void send(const seda::comm::SedaMessage::Ptr &m) = 0;
    virtual bool recv(seda::comm::SedaMessage::Ptr &m, bool block = true) = 0;
  };
}}

#endif // SEDA_COMM_CONNECTION_HPP
