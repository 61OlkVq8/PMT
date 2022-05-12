#include "FastpathOperator.h"

void FastpathOperator::run(const MatchFinder::MatchResult& Result)
{
    auto *caller = Result.Nodes.getNodeAs<clang::FunctionDecl>(callerName_);
    auto *if1 = Result.Nodes.getNodeAs<clang::IfStmt>(fpCondName1_);
    auto *if2 = Result.Nodes.getNodeAs<clang::IfStmt>(fpCondName2_);
    assert(if1 && if2);
    if (if1 != if2) return;
    if (this->allowedCaller_ && (*allowedCaller_ != caller->getName())) {
        BOOST_LOG_SEV(lg_, debug) << "Found match in " <<
            std::string(caller->getName()) <<
            " but mutation is only allowed in " << *allowedCaller_;
        return ;
    }
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [&oprtName = this->oprtName_,
                    ifstmt = if1, &lg = this->lg_]
                    (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(ifstmt);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(
                                    std::make_unique<clang::Rewriter>(
                                        *Result.SourceManager,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(
                                        ifstmt->getBeginLoc()).str(),
                                    oprtName, rand());

                        clang::SourceRange rng(ifstmt->getBeginLoc(), ifstmt->getEndLoc());
                        ret->RemoveText(rng);
                        return ret;
                    }, Result)));
}
