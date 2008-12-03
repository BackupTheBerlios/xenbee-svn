#include "LossyDaemonStrategy.hpp"

#include <stdlib.h>

using namespace seda;

LossyDaemonStrategy::LossyDaemonStrategy(const Strategy::Ptr &s, double probability, unsigned int seed)
  : StrategyDecorator(s->name()+".lossy-daemon", s),
    probability_(probability),
    seed_(seed) 
{
        srand(seed_);
}

void
LossyDaemonStrategy::perform(const IEvent::Ptr &evt) {
    if ((rand_r(&seed_) / (RAND_MAX + 1.0)) <= probability_) {
        SEDA_LOG_DEBUG("lossy-daemon lost event: " << evt->str());
    } else {
        StrategyDecorator::perform(evt);
    } 
}
