#ifndef DECL_OPERATOR_H
#define DECL_OPERATOR_H
#include "MatcherOperator.h"

class DeclOperator : public MatcherOperator {
    public:
        DeclOperator(const pt::ptree &config) : MatcherOperator(config), varName_("var"),
        var_(config.get_optional<std::string>("var-name")), initName_("initializer"),
        initializer_(config.get_optional<std::string>("initializer")) {
            if (var_ && initializer_) {
                std::unique_ptr<const DeclarationMatcher> matcher =
                    std::make_unique<const DeclarationMatcher>(
                            namedDecl(hasName(*var_), has(expr().bind(this->initName_))).bind(
                                this->varName_));
                this->declMatchers.push_back(std::move(matcher));
            } else {
                BOOST_LOG_SEV(this->lg_, error) << "Missing func-name or value";
            }
        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
    private:
        boost::optional<std::string> var_;
        boost::optional<std::string> initializer_;
        const std::string varName_;
        const std::string initName_;
};
#endif
