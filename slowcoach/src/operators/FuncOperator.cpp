#include "FuncOperator.h"
void FuncOperator::run(const MatchFinder::MatchResult &Result)
{
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [oprtName = this->oprtName_,
                    call = Result.Nodes.getNodeAs<clang::CallExpr>(callName_),
                    &val = val_, &lg = this->lg_]
                    (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(call);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(
                                    std::make_unique<clang::Rewriter>(
                                        *Result.SourceManager,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(
                                        call->getBeginLoc()).str(),
                                    oprtName, rand());

                        clang::SourceRange rng(call->getBeginLoc(),
                                call->getEndLoc());
                        if (val)
                            ret->ReplaceText(rng, *val);
                        else
                            ret->RemoveText(rng);
                        return ret;
                    }, Result)));
}
