#include "LoopUnbreakOperator.h"

using namespace clang::ast_matchers;

template <typename StmtTy>
void LoopUnbreakOperator::handleStmt(const MatchFinder::MatchResult& Result) {
    // The loop statement
    const StmtTy* Stmt = Result.Nodes.getNodeAs<StmtTy>(this->oprtName_);
    // Sanity check
    assert(Stmt);

    const clang::IfStmt *exitCond = Result.Nodes.getNodeAs<clang::IfStmt>(this->exitCondition_);

    this->addCandidate(std::make_unique<Operator::MutationOpTy>(std::async(
                    std::launch::deferred,
                    [& oprtName = this->oprtName_, Stmt, exitCond](
                        const MatchFinder::MatchResult& Result) -> std::shared_ptr<Mutant> {
                        const clang::CompoundStmt* Body =
                            llvm::dyn_cast_or_null<clang::CompoundStmt>(Stmt->getBody());
                        std::shared_ptr<Mutant> ret = std::make_shared<Mutant>(
                                std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                    Result.Context->getLangOpts()),
                                Result.SourceManager->getFilename(Stmt->getBeginLoc()).str(),
                                oprtName, rand());

                        // Though unlikely, it is possible that there could be an else statement
                        // to exit conditions
                        assert(exitCond);
                        const clang::Stmt *elseStmt = exitCond->getElse();
                        if (elseStmt) {
                            const clang::SourceRange ifThenBlk(
                                    Result.SourceManager->getExpansionLoc(exitCond->getBeginLoc()),
                                    Result.SourceManager->getExpansionLoc(exitCond->getElse()->getBeginLoc()));
                            ret->ReplaceText(ifThenBlk, "/* Removed exit condition */");
                        } else {
                            clang::SourceRange exitCondRng(
                                    Result.SourceManager->getExpansionLoc(exitCond->getBeginLoc()),
                                    Result.SourceManager->getExpansionLoc(exitCond->getThen()->getEndLoc()));
                            ret->ReplaceText(exitCondRng, "{}/* Removed exit condition */");
                        }
                        return ret;
                    }, Result)));
}

void LoopUnbreakOperator::run(const MatchFinder::MatchResult& Result)
{
    const clang::ForStmt* FS = Result.Nodes.getNodeAs<clang::ForStmt>(this->oprtName_);
    const clang::WhileStmt* WS = Result.Nodes.getNodeAs<clang::WhileStmt>(this->oprtName_);
    const clang::DoStmt* DS = Result.Nodes.getNodeAs<clang::DoStmt>(this->oprtName_);
    assert(FS || WS || DS);

    if (FS && this->isRelevant(FS, Result.SourceManager) && !this->isInfinite(FS, Result)) {
        this->handleStmt<clang::ForStmt>(Result);
    } else if (WS && this->isRelevant(WS, Result.SourceManager) && !this->isInfinite(WS, Result)) {
        this->handleStmt<clang::WhileStmt>(Result);
    } else if (DS && this->isRelevant(WS, Result.SourceManager) && !this->isInfinite(DS, Result)) {
        this->handleStmt<clang::DoStmt>(Result);
    } else {
        // Sanity checking: There must be statements matched,
        // but not mutated since they are infinite
        assert(FS || WS || DS);
    }
}
