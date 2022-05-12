#include "RedunOpLoopOperator.h"

using namespace clang::ast_matchers;

template <typename StmtTy>
void RedunOpLoopOperator::handleLoopStmt(const MatchFinder::MatchResult& Result) {
    const StmtTy* stmt = Result.Nodes.getNodeAs<StmtTy>(this->loopName_);
    const clang::FunctionDecl* func = Result.Nodes.getNodeAs<clang::FunctionDecl>(this->funcName_);
    // Sanity check
    assert(stmt && func);

    this->addCandidate(std::make_unique<Operator::MutationOpTy>(std::async(
                    std::launch::deferred,
                    [&oprtName = this->oprtName_, &codeStr_ = this->codeStr_, stmt, func,
                    preprocessor = this->preprocessor_](
                        const MatchFinder::MatchResult& Result) -> std::shared_ptr<Mutant> {
                        const clang::CompoundStmt* body =
                            llvm::dyn_cast_or_null<clang::CompoundStmt>(stmt->getBody());
                        assert(func);
                        std::shared_ptr<Mutant> ret = std::make_shared<Mutant>(
                                std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                    Result.Context->getLangOpts()),
                                Result.SourceManager->getFilename(stmt->getBeginLoc()).str(),
                                oprtName, rand());
                        if (body) {
                            ret->InsertText(clang::Lexer::getLocForEndOfToken(body->getLBracLoc(), 0,
                                        *Result.SourceManager, Result.Context->getLangOpts()),
                                    codeStr_.str(), true, true);
                        } else {
                            std::stringstream toBeInjected;
                            // Need to get the location next to the endLoc
                            // But this loc does not include semicolon
                            clang::SourceRange injectLoc(
                                    Result.SourceManager->getExpansionLoc(stmt->getBody()->getBeginLoc()),
                                    Result.SourceManager->getExpansionLoc(
                                        clang::Lexer::getLocForEndOfToken(stmt->getBody()->getEndLoc(),
                                            0, *Result.SourceManager, Result.Context->getLangOpts())));
                            // Manually add semicolon here
                            toBeInjected << "{\n" << codeStr_.str() << clang::Lexer::getSourceText(
                                    clang::CharSourceRange::getCharRange(injectLoc),
                                    *Result.SourceManager, Result.Context->getLangOpts()).str() << ";\n}";
                            ret->ReplaceText(injectLoc, toBeInjected.str());
                        }
                        // Need to insert header inclusion later than function body mutation
                        // As insert operations changes AST location information
                        // FIXME Format newline in the preprocessor string
                        if (preprocessor)
                            ret->InsertText(func->getBeginLoc(), *preprocessor + '\n', false, true);
                        return ret;
                    }, Result)));
}

void RedunOpLoopOperator::run(const MatchFinder::MatchResult& Result)
{
    const clang::ForStmt* FS = Result.Nodes.getNodeAs<clang::ForStmt>(this->loopName_);
    const clang::WhileStmt* WS = Result.Nodes.getNodeAs<clang::WhileStmt>(this->loopName_);
    const clang::DoStmt* DS = Result.Nodes.getNodeAs<clang::DoStmt>(this->loopName_);
    assert(FS || WS || DS);

    if (FS && this->isRelevant(FS, Result.SourceManager)) {
        this->handleLoopStmt<clang::ForStmt>(Result);
    } else if (WS && this->isRelevant(WS, Result.SourceManager)) {
        this->handleLoopStmt<clang::WhileStmt>(Result);
    } else if (DS && this->isRelevant(DS, Result.SourceManager)) {
        this->handleLoopStmt<clang::DoStmt>(Result);
    } else {
        // Sanity checking: There must be statements matched,
        // but not mutated since they are infinite
        assert(FS || WS || DS);
    }
}
