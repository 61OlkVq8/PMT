#ifndef LOOP_UNBREAK_OPERATOR
#define LOOP_UNBREAK_OPERATOR
#include "MatcherOperator.h"

class LoopUnbreakOperator : public MatcherOperator {
    public:
        LoopUnbreakOperator (const pt::ptree &config) : MatcherOperator(config), exitCondition_("exit-cond")
    {
        this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                    ifStmt(anyOf(hasAncestor(forStmt().bind(this->oprtName_)),
                                hasAncestor(whileStmt().bind(this->oprtName_)),
                                hasAncestor(doStmt().bind(this->oprtName_))
                                ),
                            anyOf(has(breakStmt()), has(returnStmt()), has(gotoStmt()),
                                has(compoundStmt(has(breakStmt()))),
                                has(compoundStmt(has(returnStmt()))),
                                has(compoundStmt(has(gotoStmt())))),
                            unless(hasElse(stmt()))).bind(this->exitCondition_)
                    ));
    }
    virtual void run(const MatchFinder::MatchResult& Result) override;

    template <typename StmtTy>
    void handleStmt(const MatchFinder::MatchResult& Result);

private:
    bool inline isInfinite(const clang::ForStmt *forStmt, const MatchFinder::MatchResult& result) {
        auto *cond = forStmt->getCond();
        bool ret = false;
        if (!cond) return true;
        if (cond->isEvaluatable(*result.Context)) { cond->EvaluateAsBooleanCondition(ret, *result.Context); }
        return ret;
    }

    bool inline isInfinite(const clang::WhileStmt *whileStmt, const MatchFinder::MatchResult& result) {
        auto *cond = whileStmt->getCond();
        bool ret = false;
        assert(cond);
        if (cond->isEvaluatable(*result.Context)) { cond->EvaluateAsBooleanCondition(ret, *result.Context); }
        return ret;
    }
    bool inline isInfinite(const clang::DoStmt *doStmt, const MatchFinder::MatchResult& result) {
        auto *cond = doStmt->getCond();
        bool ret = false;
        assert(cond);
        if (cond->isEvaluatable(*result.Context)) { cond->EvaluateAsBooleanCondition(ret, *result.Context); }
        return ret;
    }
    std::string exitCondition_;
};
#endif
