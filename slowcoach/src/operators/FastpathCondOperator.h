#ifndef FASTPATH_COND_OPERATOR_H
#define FASTPATH_COND_OPERATOR_H
#include <MatcherOperator.h>

class FastpathCondOperator : public MatcherOperator {
    public:
        FastpathCondOperator(const pt::ptree &config) : MatcherOperator(config),
        var_(config.get_optional<std::string>("var-name")), varName_("var"),
        callerName_("caller"), value_(config.get_optional<std::string>("value")),
        fpCondName_("fastpath-cond"), allowedCaller_(config.get_optional<std::string>("caller")) {
            if (var_) {
                this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                            ifStmt(hasCondition(expr(hasDescendant(declRefExpr(to(
                                                    varDecl(hasName(*var_))),
                                                hasAncestor(
                                                    functionDecl().bind(
                                                        callerName_))).bind(
                                                    varName_))))).bind(fpCondName_)
                            ));
            }
            else
                BOOST_LOG_SEV(lg_, error) << "The name of variable is not provided";
        }
        virtual void run(const MatchFinder::MatchResult& Result) override;
    private:
        boost::optional<std::string> var_;
        boost::optional<std::string> allowedCaller_;
        // Values to substitute
        boost::optional<std::string> value_;
        const std::string callerName_;
        const std::string varName_;
        const std::string fpCondName_;
};

#endif
