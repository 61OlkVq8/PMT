#ifndef LAZY_UPDATE_OPERATOR_H
#define LAZY_UPDATE_OPERATOR_H
#include "MatcherOperator.h"

class LazyUpdateOperator : public MatcherOperator {
    public:
        LazyUpdateOperator (const pt::ptree &config) : MatcherOperator(config),
        assignmentName_("update"),
        updatee_(config.get_optional<std::string>("updated-var")) {
            if (updatee_) {
                std::unique_ptr<const StatementMatcher> matcher =
                    std::make_unique<const StatementMatcher>(
                            binaryOperator(isAssignmentOperator(), hasLHS(declRefExpr(to(namedDecl(
                                                hasName(*updatee_)))))).bind(
                                this->assignmentName_));
                this->stmtMatchers.push_back(std::move(matcher));
            } else
                BOOST_LOG_SEV(lg_, error) << "The name of variable to be updated is not provided";
        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
    private:
        boost::optional<std::string> updatee_;
        const std::string assignmentName_;
};

#endif
