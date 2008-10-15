#include "Observable.hpp"

using namespace mqs;

void
Observable::attach(Observer *o) {
    _observers.push_back(o);
}

void
Observable::detach(Observer *o) {
    for (std::list<Observer*>::iterator it(_observers.begin()); it != _observers.end(); ++it) {
        if (*it == o) {
            it = _observers.erase(it);
        }
    }
}

void
Observable::notify() {
    for (std::list<Observer*>::iterator it(_observers.begin()); it != _observers.end(); ++it) {
        (*it)->update();
    }
}
