#ifndef OPERATOR_H
#define OPERATOR_H

#include <memory>
#include <future>
#include <string>
#include <vector>

#include "Mutant.h"

#include "boost/core/noncopyable.hpp"
#include "boost/optional.hpp"
#include "boost/log/expressions.hpp"
#include "boost/log/sources/severity_logger.hpp"
#include "boost/log/trivial.hpp"
#include "boost/log/utility/setup/file.hpp"
#include "boost/property_tree/ptree.hpp"

using namespace clang::ast_matchers;
using namespace boost::log::trivial;
namespace pt = boost::property_tree;

class Operator : private boost::noncopyable {
    public:
        Operator(const pt::ptree &config) : config_(config),
        oprtName_(config.get<std::string>("<xmlattr>.name")) {
            candidates_.reserve(1024);
        }
        virtual ~Operator() = default;

        using MutationOpTy = std::future<std::shared_ptr<Mutant>>;
        using MutationPoolTy = std::vector<std::unique_ptr<MutationOpTy>>;
        using MutationPoolOpIterTy = MutationPoolTy::iterator;
        using MutationPoolOpConstIterTy = MutationPoolTy::const_iterator;
        using MutantPoolTy = std::vector<std::shared_ptr<Mutant>>;

        bool candidatePoolEmpty() const { return candidates_.empty(); }

        // FIXME Not sure how much overheads futures cause
        void addCandidate(std::unique_ptr<MutationOpTy> Op) {
            if (Op)
                this->candidates_.push_back(std::move(Op));
        }

        virtual std::unique_ptr<MutantPoolTy> mutate();

    protected:
        std::string oprtName_;
        MutationPoolTy candidates_;
        boost::log::sources::severity_logger<boost::log::trivial::severity_level> lg_;
        const pt::ptree &config_;
};
#endif
