#ifndef FASTPATH_OPERATOR_H
#define FASTPATH_OPERATOR_H
#include "MatcherOperator.h"

class FastpathOperator : public MatcherOperator {
    public:
        FastpathOperator(const pt::ptree &config) : MatcherOperator(config),
        memberVar_(config.get_optional<std::string>("member-var")),
        call_(config.get_optional<std::string>("func-name")),
        allowedCaller_(config.get_optional<std::string>("caller")),
        fpCondName1_("fastpath-cond1"), fpCondName2_("fastpath-cond2"), callerName_("caller") {
            if (memberVar_) {
                this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                            ifStmt(hasCondition(expr(hasDescendant(memberExpr(
                                                hasDeclaration(namedDecl(hasName(*memberVar_))),
                                                hasAncestor(ifStmt().bind(fpCondName2_)))))),
                                hasAncestor(functionDecl().bind(callerName_)),
                                unless(hasElse(expr()))).bind(fpCondName1_)
                            ));
            } else if (call_) {
                this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                            ifStmt(hasThen(stmt(hasDescendant(callExpr(callee(
                                                functionDecl(hasName(*call_))),
                                                hasAncestor(ifStmt().bind(fpCondName2_)))))),
                                hasAncestor(functionDecl().bind(callerName_)),
                                unless(hasElse(expr()))).bind(fpCondName1_)
                            ));
            } else {
                BOOST_LOG_SEV(lg_, error) << "The name of variable is not provided";
            }
        }
        virtual void run(const MatchFinder::MatchResult& Result) override;
    private:
        boost::optional<std::string> memberVar_;
        boost::optional<std::string> call_;
        boost::optional<std::string> allowedCaller_;
        const std::string fpCondName1_;
        const std::string fpCondName2_;
        const std::string callerName_;
};

#endif
