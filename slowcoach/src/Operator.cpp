#include "Operator.h"

std::unique_ptr<Operator::MutantPoolTy> Operator::mutate() {
    std::unique_ptr<MutantPoolTy> ret = std::make_unique<Operator::MutantPoolTy>();
    for (auto i = this->candidates_.begin();
            i != this->candidates_.end(); i++) {
        // FIXME Do not ignore error code here
        ret->push_back((*i)->get());
    }
    return ret;
}
