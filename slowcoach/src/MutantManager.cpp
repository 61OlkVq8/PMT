#include "MutantManager.h"

std::error_code MutantManager::writeMutants(
        std::unique_ptr<MutantManager::MutantPoolTy> mutantsP) {
    std::error_code ret;
    for (auto mut_i = mutantsP->begin(); mut_i != mutantsP->end(); mut_i ++) {
        // FIXME Handle error_code here
        ret = (*mut_i)->WriteOutput();
    }
    return ret;
}
