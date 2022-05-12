#include "DummyOperator.h"

using namespace clang::ast_matchers;

void DummyOperator::run(const MatchFinder::MatchResult &Result)
{
    const clang::ForStmt *FS = Result.Nodes.getNodeAs<clang::ForStmt>(this->oprtName_);
    if (FS && this->isRelevant(FS, Result.SourceManager)) {
        this->addCandidate(
                std::make_unique<Operator::MutationOpTy>(
                    std::async(std::launch::async,
                        [&oprtName = this->oprtName_] (const MatchFinder::MatchResult &Result) ->
                        std::shared_ptr<Mutant> {
                            const clang::ForStmt *FS = Result.Nodes.getNodeAs<clang::ForStmt>(oprtName);
                            // Sanity check
                            assert(FS);
                            const clang::CompoundStmt *Body = llvm::dyn_cast<clang::CompoundStmt>(FS->getBody());
                            std::unique_ptr<clang::Rewriter> RewriterP =
                                std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                        Result.Context->getLangOpts());
                            if (Body) {
                                RewriterP->InsertTextAfterToken(Body->getEndLoc(), " // A loop");
                            } else {
                                clang::Token Tok;
                                clang::Lexer::getRawToken(FS->getEndLoc(), Tok,
                                        Result.Context->getSourceManager(),
                                        Result.Context->getLangOpts(), true);
                                // Make a copy
                                const clang::SourceLocation EndLoc = Tok.getEndLoc();
                                RewriterP->InsertTextAfterToken(EndLoc, " // A loop");
                                clang::Lexer::getRawToken(EndLoc, Tok,
                                        Result.Context->getSourceManager(),
                                        Result.Context->getLangOpts(), true);
                            }

                            return std::make_shared<Mutant>(std::move(RewriterP),
                                    Result.SourceManager->getFilename(FS->getBeginLoc()).str(),
                                    oprtName, rand());
                        }, Result)));
    }
}
