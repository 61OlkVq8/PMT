#ifndef DECL_LOOP_OPERATOR_H
#define DECL_LOOP_OPERATOR_H
#include "MatcherOperator.h"
#include "RedunOperation.h"

class RedunOpDeclOperator : public MatcherOperator {
    public:
        RedunOpDeclOperator(const pt::ptree &config) : MatcherOperator(config),
        funcName_("func"), funcBodyName_("func-body"),
        preprocessor_(config.get_optional<std::string>("preprocessor"))
        {
            parseOpConfig(config, codeStr_, lg_);
            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        compoundStmt(hasParent(
                                functionDecl().bind(this->funcName_))).bind(this->funcBodyName_)));
        }
        virtual void run(const MatchFinder::MatchResult& Result) override;

    private:
        std::string funcName_;
        std::string funcBodyName_;
        std::stringstream codeStr_;
        boost::optional<std::string> preprocessor_;
};

#endif
