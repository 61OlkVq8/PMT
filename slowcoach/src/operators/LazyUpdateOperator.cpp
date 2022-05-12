#include "LazyUpdateOperator.h"

void LazyUpdateOperator::run(const MatchFinder::MatchResult &Result)
{
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [oprtName = this->oprtName_,
                    assignment = Result.Nodes.getNodeAs<clang::BinaryOperator>(assignmentName_),
                    &lg = this->lg_]
                    (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(assignment);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(
                                    std::make_unique<clang::Rewriter>(
                                        *Result.SourceManager,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(
                                        assignment->getBeginLoc()).str(),
                                    oprtName, rand());

                        clang::SourceRange rng(assignment->getBeginLoc(),
                                assignment->getEndLoc());
                        ret->RemoveText(rng);
                        return ret;
                    }, Result)));
}
