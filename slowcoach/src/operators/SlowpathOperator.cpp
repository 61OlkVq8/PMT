#include "SlowpathOperator.h"

void SlowpathOperator::run(const MatchFinder::MatchResult& Result)
{
    const auto *ifStmt = Result.Nodes.getNodeAs<clang::IfStmt>(this->ifName1_);
    const auto *ifStmt2 = Result.Nodes.getNodeAs<clang::IfStmt>(this->ifName2_);
    assert(ifStmt && ifStmt2);
    if (ifStmt != ifStmt2) return;
    const auto *then = llvm::dyn_cast_or_null<clang::CompoundStmt>(ifStmt->getThen());
    const auto *el = llvm::dyn_cast_or_null<clang::CompoundStmt>(ifStmt->getElse());
    const auto *call = Result.Nodes.getNodeAs<clang::CallExpr>(this->callName_);
    assert(call);
    if (!ifStmt->getElse()) {
        this->addCandidate(
                std::make_unique<Operator::MutationOpTy>(
                    std::async(std::launch::deferred,
                        [oprtName = this->oprtName_, ifStmt,
                        then, call, &lg = this->lg_] (const MatchFinder::MatchResult &Result) ->
                        std::shared_ptr<Mutant> {
                            std::shared_ptr<Mutant> ret =
                                std::make_shared<Mutant>(
                                        std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                            Result.Context->getLangOpts()),
                                        Result.SourceManager->getFilename(
                                            ifStmt->getBeginLoc()).str(),
                                        oprtName, rand());
                            // If it's not a compound statement
                            if (!then) {
                                clang::Token Tok;
                                clang::Lexer::getRawToken(ifStmt->getCond()->getEndLoc(), Tok,
                                        Result.Context->getSourceManager(),
                                        Result.Context->getLangOpts(), true);
                                clang::SourceRange ifItself(ifStmt->getIfLoc(),
                                        Tok.getEndLoc());
                                ret->RemoveText(ifItself);
                                return ret;
                            } else {
                                clang::SourceRange ifFsrHalfRng(ifStmt->getBeginLoc(),
                                        then->getLBracLoc());
                                ret->RemoveText(ifFsrHalfRng);
                                ret->RemoveText(then->getRBracLoc(), 1UL);
                                return ret;
                            }
                        }, Result)));
    } else {
        // Has else
        this->addCandidate(
                std::make_unique<Operator::MutationOpTy>(
                    std::async(std::launch::deferred,
                        [oprtName = this->oprtName_, ifStmt,
                        el, call, &lg = this->lg_] (const MatchFinder::MatchResult &Result) ->
                        std::shared_ptr<Mutant> {
                            std::shared_ptr<Mutant> ret =
                                std::make_shared<Mutant>(
                                        std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                            Result.Context->getLangOpts()),
                                        Result.SourceManager->getFilename(
                                            ifStmt->getBeginLoc()).str(),
                                        oprtName, rand());
                            clang::Token Tok;
                            clang::Lexer::getRawToken(ifStmt->getElseLoc(), Tok,
                                    Result.Context->getSourceManager(),
                                    Result.Context->getLangOpts(), true);
                            clang::SourceRange rng(ifStmt->getBeginLoc(),
                                    Tok.getEndLoc());
                            ret->RemoveText(rng);
                            return ret;
                        }, Result)));
    }
}
