#include "RedunOpOperator.h"

void RedunOpOperator::genCandidates(const clang::SourceLocation loc,
        clang::SourceManager &srcMgr, const clang::ASTContext &ctx)
{
    this->addCandidate(std::make_unique<Operator::MutationOpTy>(std::async(std::launch::deferred,
                    [&srcMgr, &ctx, loc, &oprtName = this->oprtName_, &codeStr = this->codeStr_,
                    &lg_ = this->lg_] () -> std::shared_ptr<Mutant> {
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(std::make_unique<clang::Rewriter>(srcMgr, ctx.getLangOpts()),
                                    srcMgr.getFilename(loc).str(), oprtName, rand());
                        ret->InsertText(loc, codeStr.str());
                        return ret;
                    }))
            );
}
