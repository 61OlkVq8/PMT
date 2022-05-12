#ifndef REDUN_OP_LOOP_OPERATOR_H
#define REDUN_OP_LOOP_OPERATOR_H
#include "MatcherOperator.h"
#include "RedunOperation.h"

class RedunOpLoopOperator : public MatcherOperator {
    public:
        RedunOpLoopOperator(const pt::ptree &config) : MatcherOperator(config), loopName_("loop"),
        funcName_("func"), preprocessor_(config.get_optional<std::string>("preprocessor"))
        {
            parseOpConfig(config, codeStr_, lg_);
            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        forStmt(hasBody(stmt()),
                            hasAncestor(functionDecl().bind(this->funcName_))).bind(this->loopName_)));
            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        whileStmt(hasBody(stmt()),
                            hasAncestor(functionDecl().bind(this->funcName_))).bind(this->loopName_)));
            this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                        doStmt(hasBody(stmt()),
                            hasAncestor(functionDecl().bind(this->funcName_))).bind(this->loopName_)));
        }
        virtual void run(const MatchFinder::MatchResult& Result) override;

        template <typename StmtTy>
            void handleLoopStmt(const MatchFinder::MatchResult& Result);
        void handleFuncBody(const MatchFinder::MatchResult& Result);

    private:
        std::string loopName_;
        std::string funcName_;
        std::stringstream codeStr_;
        boost::optional<std::string> preprocessor_;
};

#endif
