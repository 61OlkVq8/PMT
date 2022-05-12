#include "FastpathCondOperator.h"

void FastpathCondOperator::run(const MatchFinder::MatchResult& Result) {
    if (!var_) {
        BOOST_LOG_SEV(lg_, error) << "Cannot find variable to be substituted";
        return ;
    }
    if (!value_) {
        BOOST_LOG_SEV(lg_, error) << "Cannot find value to substitute the variable";
        return ;
    }
    auto *caller = Result.Nodes.getNodeAs<clang::FunctionDecl>(callerName_);
    if (this->allowedCaller_ && (*allowedCaller_ != caller->getName())) {
        BOOST_LOG_SEV(lg_, debug) << "Found match in " <<
            std::string(caller->getName()) <<
            " but mutation is only allowed in " << *allowedCaller_;
        return ;
    }
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [oprtName = this->oprtName_,
                    var = Result.Nodes.getNodeAs<clang::DeclRefExpr>(varName_),
                    &val = *value_, &lg = this->lg_]
                    (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(var);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(
                                    std::make_unique<clang::Rewriter>(
                                        *Result.SourceManager,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(
                                        var->getBeginLoc()).str(),
                                    oprtName, rand());

                        clang::SourceRange rng(var->getBeginLoc(), var->getEndLoc());
                        ret->ReplaceText(rng, val);
                        return ret;
                    }, Result)));
}
