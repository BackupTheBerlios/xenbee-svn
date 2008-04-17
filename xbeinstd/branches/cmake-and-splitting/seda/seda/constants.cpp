#include "constants.hpp"

#include <limits>
namespace seda {
  std::size_t SEDA_MAX_QUEUE_SIZE = std::numeric_limits<std::size_t>::max();
  unsigned long SEDA_DEFAULT_TIMEOUT = 500;
}
