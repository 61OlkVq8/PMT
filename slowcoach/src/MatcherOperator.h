#ifndef MATCHER_OPERATOR_H
#define MATCHER_OPERATOR_H
#include "clang/ASTMatchers/ASTMatchers.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Lex/Lexer.h"
#include "clang/Basic/TokenKinds.h"

#include "Operator.h"

class MatcherOperator : public Operator, public MatchFinder::MatchCallback {
    public:
        MatcherOperator(const pt::ptree &config) : Operator(config) {
            stmtMatchers.reserve(1024);
            declMatchers.reserve(1024);
        }
        virtual ~MatcherOperator() = default;

        virtual void run(const MatchFinder::MatchResult &Result) = 0;

        inline bool isRelevant(const clang::Stmt *stmt, const clang::SourceManager *srcMgr) const {
            return (stmt && stmt->getBeginLoc().isValid()
                    && srcMgr->getSpellingLoc(stmt->getBeginLoc()) ==
                    srcMgr->getExpansionLoc(stmt->getBeginLoc())
                    && srcMgr->isWrittenInMainFile(stmt->getBeginLoc())
                    && !srcMgr->isInSystemHeader(stmt->getBeginLoc()));
        }

        using StmtMatcherPoolTy = std::vector<std::unique_ptr<const StatementMatcher>>;
        using DeclarationMatcherPoolTy = std::vector<std::unique_ptr<const DeclarationMatcher>>;

        using StmtMatcherConstIterTy = StmtMatcherPoolTy::const_iterator;
        using DeclarationMatcherConstIterTy = DeclarationMatcherPoolTy::const_iterator;

        StmtMatcherConstIterTy getStmtMatcherConstBegin() const { return stmtMatchers.cbegin(); }
        StmtMatcherConstIterTy getStmtMatcherConstEnd() const { return stmtMatchers.cend(); }
        DeclarationMatcherConstIterTy getDeclMatcherConstBegin() const { return declMatchers.cbegin(); }
        DeclarationMatcherConstIterTy getDeclMatcherConstEnd() const { return declMatchers.cend(); }
    protected:
        StmtMatcherPoolTy stmtMatchers;
        DeclarationMatcherPoolTy declMatchers;
};

#endif
