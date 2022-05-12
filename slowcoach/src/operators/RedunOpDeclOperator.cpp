#include "RedunOpDeclOperator.h"

void RedunOpDeclOperator::run(const MatchFinder::MatchResult& Result)
{
    const clang::CompoundStmt* body = Result.Nodes.getNodeAs<clang::CompoundStmt>(this->funcBodyName_);
    if (!body || !this->isRelevant(body, Result.SourceManager))
        return ;
    const clang::FunctionDecl* func = Result.Nodes.getNodeAs<clang::FunctionDecl>(this->funcName_);
    assert(func);
    this->addCandidate(std::make_unique<Operator::MutationOpTy>(std::async(
                    std::launch::deferred, [&oprtName = this->oprtName_, &codeStr_ = this->codeStr_, body,
                    func, preprocessor = this->preprocessor_]
                    (const MatchFinder::MatchResult& Result) -> std::shared_ptr<Mutant> {
                        std::shared_ptr<Mutant> ret = std::make_shared<Mutant>(
                                std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                    Result.Context->getLangOpts()),
                                Result.SourceManager->getFilename(body->getBeginLoc()).str(),
                                oprtName, rand());
                        ret->InsertText(clang::Lexer::getLocForEndOfToken(body->getLBracLoc(), 0,
                                    *Result.SourceManager, Result.Context->getLangOpts()),
                                codeStr_.str(), true, true);
                        // Need to insert header inclusion later than function body mutation
                        // As insert operations changes AST location information
                        // FIXME Format newline in the preprocessor string
                        if (preprocessor)
                            ret->InsertText(func->getBeginLoc(), *preprocessor + '\n', false, true);
                        return ret;
                    }, Result)));
}
