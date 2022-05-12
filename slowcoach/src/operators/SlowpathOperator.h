#ifndef SLOWPATH_OPERATOR_H
#define SLOWPATH_OPERATOR_H
#include <MatcherOperator.h>

class SlowpathOperator : public MatcherOperator {
    public:
        SlowpathOperator(const pt::ptree &config) : MatcherOperator(config),
        slowPath_(config.get_optional<std::string>("func-name")),
        slowPathFuncName_("slowpath"), ifName1_("ifcond1"), ifName2_("ifcond2"),
        callName_("call"), callerName_("caller"), elseName_("else"), thenName_("then"),
        allowedCaller_(config.get_optional<std::string>("caller")) {
            if (this->slowPath_) {
                this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                            ifStmt(hasAncestor(functionDecl().bind(this->callerName_)),
                                hasThen(stmt(hasDescendant(callExpr(callee(functionDecl(
                                                        hasName(*(this->slowPath_))).bind(
                                                        this->slowPathFuncName_)),
                                                hasAncestor(ifStmt().bind(ifName2_))).bind(
                                                    callName_))).bind(thenName_)),
                                unless(hasElse(stmt()))).bind(ifName1_)
                            ));
                this->stmtMatchers.push_back(std::make_unique<const StatementMatcher>(
                            ifStmt(hasAncestor(functionDecl().bind(this->callerName_)),
                                hasElse(stmt(hasDescendant(callExpr(callee(functionDecl(
                                                        hasName(*(this->slowPath_))).bind(
                                                        this->slowPathFuncName_)),
                                                hasAncestor(ifStmt().bind(ifName2_))).bind(
                                                    callName_))).bind(elseName_))
                                ).bind(ifName1_)
                            ));
            } else {
                BOOST_LOG_SEV(lg_, error) << "Cannot find the slowpath name";
            }
        }
        virtual void run(const MatchFinder::MatchResult& Result) override;
    private:
        boost::optional<std::string> slowPath_;
        const std::string slowPathFuncName_;
        // ifName1_ should capture the same if statement of ifName2_
        const std::string ifName1_;
        const std::string ifName2_;
        const std::string callName_;
        const std::string callerName_;
        const std::string thenName_;
        const std::string elseName_;
        boost::optional<std::string> allowedCaller_;
};

#endif
