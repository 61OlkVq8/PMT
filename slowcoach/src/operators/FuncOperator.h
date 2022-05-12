#ifndef FUNC_OPERATOR_H
#define FUNC_OPERATOR_H
#include "MatcherOperator.h"
class FuncOperator : public MatcherOperator {
    public:
        FuncOperator(const pt::ptree &config) : MatcherOperator(config), callName_("call"),
        callee_(config.get_optional<std::string>("func-name")),
        val_(config.get_optional<std::string>("value")) {
            if (callee_) {
                std::unique_ptr<const StatementMatcher> matcher =
                    std::make_unique<const StatementMatcher>(
                            callExpr(callee(functionDecl(
                                        hasName(*callee_)))).bind(
                                this->callName_));
                this->stmtMatchers.push_back(std::move(matcher));
            } else {
                BOOST_LOG_SEV(this->lg_, error) << "Missing func-name or value";
            }
        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
    private:
        boost::optional<std::string> callee_;
        boost::optional<std::string> val_;
        const std::string callName_;
};
#endif
