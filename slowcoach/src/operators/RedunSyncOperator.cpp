#include "RedunSyncOperator.h"

#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/AST/Expr.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "llvm/ADT/StringRef.h"

static const std::string HeaderDecl("#include <pthread.h>\n");
static const std::string MutexDecl("pthread_mutex_t oprt_mutex = PTHREAD_MUTEX_INITIALIZER;\n");
static const std::string MutexLock("\npthread_mutex_lock(&oprt_mutex);");
static const std::string MutexUnlock("pthread_mutex_unlock(&oprt_mutex);\n");

static bool hasRecursiveCall(const clang::Stmt *stmt, const clang::FunctionDecl *functionDecl)
{
    clang::Stmt::const_child_iterator iterator;

    if (stmt == nullptr) {
        return false;
    } else {
        for (iterator = stmt->child_begin();
                iterator != stmt->child_end();
                ++iterator) {
            if (const clang::CallExpr *CALLEXPR = clang::dyn_cast_or_null<clang::CallExpr>(*iterator)) {
                if (CALLEXPR->getDirectCallee() == functionDecl)
                    return true;
                else if (CALLEXPR->getDirectCallee())
                    return hasRecursiveCall(CALLEXPR->getDirectCallee()->getBody(), functionDecl);
            }
        }
        return false;
    }
}

static void getReturnStmtsInStmt(const clang::Stmt *stmt,
        std::vector<const clang::ReturnStmt*> &returnVector)
{
    clang::Stmt::const_child_iterator iterator;
    if (!stmt) return;
    for (iterator = stmt->child_begin();
            iterator != stmt->child_end(); ++iterator) {
        if (const clang::ReturnStmt *RETURNSTMT =
                clang::dyn_cast_or_null<clang::ReturnStmt>(*iterator))
            returnVector.push_back(RETURNSTMT);
        else
            getReturnStmtsInStmt(*iterator, returnVector);
    }
}

static std::string modifyReturnString(const MatchFinder::MatchResult &Result,
        const clang::ReturnStmt *returnStmt)
{
    std::string str("{\n");
    llvm::raw_string_ostream rso(str);
    rso << MutexUnlock;
    returnStmt->printPretty(rso, nullptr,
            clang::PrintingPolicy(Result.Context->getLangOpts()));
    rso << " }\n";

    return rso.str();
}

void RedunSyncOperator::run(const MatchFinder::MatchResult &Result)
{
    const clang::FunctionDecl *FUNCTIONDECL =
        Result.Nodes.getNodeAs<clang::FunctionDecl>(this->oprtName_);
    if (!FUNCTIONDECL || !Result.SourceManager->isInMainFile(FUNCTIONDECL->getBeginLoc()))
        return;

    if (!FUNCTIONDECL->hasBody()) return;

    const clang::CompoundStmt *BODY =
        llvm::dyn_cast_or_null<clang::CompoundStmt>(FUNCTIONDECL->getBody());
    assert(BODY);
    if(hasRecursiveCall(BODY, FUNCTIONDECL)) return;

    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(
                std::async(std::launch::deferred,
                    [&oprtName = this->oprtName_, BODY, FUNCTIONDECL]
                    (const MatchFinder::MatchResult &Result) -> std::shared_ptr<Mutant> {
                        const clang::FunctionDecl *FUNCTIONDECL =
                            Result.Nodes.getNodeAs<clang::FunctionDecl>(oprtName);
                        clang::SourceManager *sm = Result.SourceManager;
                        assert(FUNCTIONDECL);
                        std::shared_ptr<Mutant> ret =
                            std::make_shared<Mutant>(std::make_unique<clang::Rewriter>(*sm,
                                        Result.Context->getLangOpts()),
                                    Result.SourceManager->getFilename(FUNCTIONDECL->getBody()->getBeginLoc()).str(),
                                    oprtName, rand());

                        std::vector<const clang::ReturnStmt*> returnVector;
                        getReturnStmtsInStmt(BODY,returnVector);

                        ret->InsertTextBefore(sm->getExpansionLoc(FUNCTIONDECL->getBeginLoc()),
                                llvm::StringRef(MutexDecl));
                        ret->InsertTextBefore(sm->getExpansionLoc(FUNCTIONDECL->getBeginLoc()),
                                llvm::StringRef(HeaderDecl));
                        ret->InsertTextAfterToken(BODY->getLBracLoc(), llvm::StringRef(MutexLock));
                        // If the function is of void type just prepend the unlock statement before right brace
                        if (returnVector.empty())
                            ret->InsertTextBefore(BODY->getRBracLoc(), llvm::StringRef(MutexUnlock));
                        else {
                            for (auto iterator = returnVector.cbegin();
                                    iterator != returnVector.cend();
                                    ++iterator) {
                                std::string modifiedString(modifyReturnString(Result, *iterator));

                                clang::Token Tok;
                                // Consume ;
                                clang::Lexer::getRawToken((*iterator)->getEndLoc(), Tok,
                                        Result.Context->getSourceManager(),
                                        Result.Context->getLangOpts(), true);
                                ret->ReplaceText(clang::SourceRange((*iterator)->getBeginLoc(),
                                            Tok.getEndLoc()), modifiedString);
                            }
                            if (FUNCTIONDECL->getReturnType().getTypePtr()->isVoidType()) {
                                ret->InsertTextBefore(BODY->getRBracLoc(), llvm::StringRef(MutexUnlock));
                            }
                        }
                        // Assume we have declaration like this:
                        // bool func()
                        // The speelling begin location of the function declaration is pointed to
                        // the declaration of bool, which is stdbool.h
                        return ret;
                    }, Result)));
}
