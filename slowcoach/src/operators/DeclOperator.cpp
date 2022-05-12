#include "DeclOperator.h"
void DeclOperator::run(const MatchFinder::MatchResult &Result)
{
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [oprtName = this->oprtName_, &lg = this->lg_,
                    newInit = *(this->initializer_),
                    init = Result.Nodes.getNodeAs<clang::Expr>(initName_)
                    ] (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(init);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(
                                    std::make_unique<clang::Rewriter>(
                                        *Result.SourceManager,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(
                                        init->getBeginLoc()).str(),
                                    oprtName, rand());
                        clang::SourceRange rng(init->getBeginLoc(),
                                init->getEndLoc());
                        ret->ReplaceText(rng, newInit);
                        return ret;
                    }, Result)));
}
