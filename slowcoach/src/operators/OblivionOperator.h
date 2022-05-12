#ifndef OBLIVION_OPERATOR_H
#define OBLIVION_OPERATOR_H

#include "MatcherOperator.h"
#include <map>
#include <vector>

#include "boost/foreach.hpp"

class OblivionOperator : public MatcherOperator {
    public:
        using varMutantMapTy = std::unordered_map<std::string, std::shared_ptr<Mutant>>;

        OblivionOperator(const pt::ptree &config) : MatcherOperator(config),
        declRefName_("declRef"), assignOpName_("assignOp"), initName_("redundancy"),
        refPrntName_("refPrnt") {
            // TODO Add cases where the local declaration has no initializer
            this->buildReplaceString = [] (llvm::raw_string_ostream &rso,
                    const clang::DeclRefExpr *ref, const clang::Expr *initExpr,
                    const clang::VarDecl *decl, const clang::ASTContext *ctx) ->
                llvm::raw_string_ostream & {
                // Theoretically we can apply Expr->getSourceRange() to Lexer
                // But Lexer::getSourceText seems to produce the text [begin, end)
                // So build the ugly string here
                clang::PrintingPolicy pp(ctx->getLangOpts());

                rso << "((";

                bool needCast = false;
                const clang::CXXRecordDecl *cxxRecord = decl->getType()->getAsCXXRecordDecl();
                // FIXME if it is a cxxRecord, we should test if equality oprt is implemented
                if (!decl->getType()->isStructureOrClassType()) {
                    // In simple C we test equality of types
                    // In C++ redundant cast won't bite either
                    if (const clang::CallExpr *call =
                            llvm::dyn_cast_or_null<clang::CallExpr>(initExpr))
                        needCast = (call->getCallReturnType(*ctx) == ref->getType());
                    else
                        needCast = (ref->getType() != initExpr->getType());

                    rso << '(';
                    ref->printPretty(rso, nullptr, pp);
                    rso << ')';

                    rso << " == ";

                    rso << '(';
                    if (needCast)
                        rso << '(' << ref->getType().getAsString(pp) << ')';
                    initExpr->printPretty(rso, nullptr, pp);
                    rso << ')';
                } else {
                    rso << "memcmp(";
                    // If localvariables are not pointers get their addresses
                    if (!ref->getType()->isPointerType())
                        rso << '&';
                    ref->printPretty(rso, nullptr, pp);
                    rso << ", ";
                    if (!initExpr->getType()->isPointerType())
                        rso << '&';
                    initExpr->printPretty(rso, nullptr, pp);
                    rso << ", sizeof(" << decl->getType().getAsString(pp) << "))";
                }

                rso << ")? (";
                if (needCast)
                    rso << '(' << ref->getType().getAsString(pp) << ')';
                ref->printPretty(rso, nullptr, pp);
                rso << "): (" ;
                initExpr->printPretty(rso, nullptr, pp);
                rso << "))";

                return rso;
            };

            // Initialize the blacklist: a set of function names where no mutation should
            // take place
            // FIXME Empty blacklist handling
            if (!config.empty()) {
                BOOST_FOREACH(const pt::ptree::value_type &funcNames,
                        this->config_.get_child("func-blacklist")) {
                    this->blacklistedFuncNames_.push_back(funcNames.second.data());
                }
            }

            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        declRefExpr(to(varDecl(hasLocalStorage(),
                                    hasInitializer(expr().bind(initName_)),
                                    hasParent(declStmt()))),
                            hasAncestor(binaryOperator(isAssignmentOperator()).bind(assignOpName_)),
                            hasParent(stmt().bind(refPrntName_))
                            ).bind(declRefName_)
                        ));
            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        declRefExpr(to(varDecl(hasLocalStorage(),
                                    hasInitializer(expr().bind(initName_)),
                                    hasParent(declStmt()))),
                            unless(hasAncestor(binaryOperator(isAssignmentOperator()))),
                            hasParent(stmt().bind(refPrntName_))
                            ).bind(declRefName_)
                        ));

        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
        virtual std::unique_ptr<MutantPoolTy> mutate() override;

        std::function<llvm::raw_string_ostream &(
                llvm::raw_string_ostream &, const clang::DeclRefExpr *, const clang::Expr *,
                const clang::VarDecl *, const clang::ASTContext *)> buildReplaceString;

        inline bool replacable(const clang::Stmt *parent);
    private:
        const std::string declRefName_;
        const std::string assignOpName_;
        const std::string initName_;
        const std::string refPrntName_;
        // TODO guard this member by locks for parallelization
        varMutantMapTy varMutant_;
        std::vector<std::string> blacklistedFuncNames_;
};

#endif
