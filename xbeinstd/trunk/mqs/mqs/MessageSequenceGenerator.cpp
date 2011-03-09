/* 
   Copyright (C) 2009 Alexander Petry <alexander.petry@itwm.fraunhofer.de>.

   This file is part of seda.

   seda is free software; you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation; either version 2, or (at your option) any
   later version.

   seda is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
   for more details.

   You should have received a copy of the GNU General Public License
   along with seda; see the file COPYING.  If not, write to
   the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  

*/

#include "MessageSequenceGenerator.hpp"

#include <mqs/common.hpp>
#include <boost/random.hpp>
#include <sstream>

using namespace mqs;

MessageSequenceGenerator::MessageSequenceGenerator(std::size_t globalId, std::size_t generatorId, const std::string &hostId)
    : _globalId(globalId), _generatorId(generatorId), _hostId(hostId), _counter(0)
{ }

MessageSequenceGenerator::Ptr MessageSequenceGenerator::newInstance() {
    static std::size_t GENERATOR_ID(0);

    // TODO: has to be atomic
    std::size_t generatorId(GENERATOR_ID++);

    // get the hostname
    char hostId[HOST_NAME_MAX+1];
    gethostname(hostId, sizeof(hostId)); hostId[HOST_NAME_MAX] = (char)0;

    // get a random ID for this generator to be unique between different adress spaces
    boost::minstd_rand rng((std::size_t)getpid());
//    boost::uniform_int<std::size_t> ints(1, std::numeric_limits<std::size_t>::max());
    boost::uniform_int<std::size_t> ints(1, 9999);
    boost::variate_generator<boost::minstd_rand&, boost::uniform_int<std::size_t> > randomNumber(rng, ints);
    std::size_t globalId(randomNumber());

    return MessageSequenceGenerator::Ptr(new MessageSequenceGenerator(globalId, generatorId, std::string(hostId)));
}

std::string MessageSequenceGenerator::next() {
    std::size_t count;
    {
        boost::unique_lock<boost::mutex> lock(_mtx);
        count = _counter++;
    } 

    time_t tstamp(time(NULL));
    std::stringstream sstr;
    const std::string sep(".");
    
    sstr << _hostId << sep << tstamp << sep << _globalId << sep << _generatorId << sep << count;
    return sstr.str();
}

