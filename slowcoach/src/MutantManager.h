#ifndef MUTANT_MANAGER_H
#define MUTANT_MANAGER_H
#include "Operator.h"
#include "Mutant.h"

#include "boost/core/noncopyable.hpp"

class MutantManager : private boost::noncopyable {
    public:
        MutantManager() = delete;
        using MutantPoolTy = Operator::MutantPoolTy;
        static std::error_code writeMutants(std::unique_ptr<MutantPoolTy> mutantsP);
    private:
        static MutantPoolTy candidatePool_;
};

#endif
