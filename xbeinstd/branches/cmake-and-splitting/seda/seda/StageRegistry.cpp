#include "StageRegistry.hpp"

using namespace seda;

StageRegistry::StageRegistry() {}
StageRegistry::~StageRegistry() {}

StageRegistry& StageRegistry::instance() {
    static StageRegistry _instance;
    return _instance;
}

void StageRegistry::insert(const std::string& name, const Stage::Ptr& stage) {
    _stages.insert(std::make_pair(name, stage));
}

void StageRegistry::insert(const Stage::Ptr& stage) {
    insert(stage->name(), stage);
}

const Stage::Ptr StageRegistry::lookup(const std::string& name) const throw (StageNotFound) {
    std::map<std::string, Stage::Ptr>::const_iterator it(_stages.find(name));
    if (it == _stages.end()) {
        throw StageNotFound(name);
    } else {
        return it->second;
    }        
}

void StageRegistry::clear() {
    _stages.clear();
}
