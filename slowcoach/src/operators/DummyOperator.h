#ifndef DUMMY_OPERATOR_H
#define DUMMY_OPERATOR_H
#include "MatcherOperator.h"

class DummyOperator : public MatcherOperator {
public:
    DummyOperator(const pt::ptree &config) : MatcherOperator(config) {
        std::unique_ptr<const StatementMatcher> matcher =
            std::make_unique<const StatementMatcher>(clang::ast_matchers::forStmt().bind(this->oprtName_));
        this->stmtMatchers.push_back(std::move(matcher));
    }
    virtual void run(const MatchFinder::MatchResult &Result) override;
};

#endif
