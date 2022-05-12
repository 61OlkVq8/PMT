#ifndef LOCAL_VAR_OPERATOR_H
#define LOCAL_VAR_OPERATOR_H
#include "MatcherOperator.h"
class LocalVarOperator : public MatcherOperator {
    public:
        using varMutantMapTy = std::unordered_map<std::string, std::shared_ptr<Mutant>>;
        LocalVarOperator(const pt::ptree &config) : MatcherOperator(config), varName_("var"),
        declName_("decl"),
        var_(config.get_optional<std::string>("var-name")),
        val_(config.get_optional<std::string>("value")),
        caller_(config.get_optional<std::string>("caller")) {
            if (var_) {
                if (caller_) {
                    this->declMatchers.push_back(std::make_unique<const DeclarationMatcher>(
                                functionDecl(hasName(*caller_),
                                    hasBody(forEachDescendant(declRefExpr(to(namedDecl(
                                                        hasName(*var_)).bind(
                                                    declName_))).bind(varName_))))
                                ));
                } else {
                    BOOST_LOG_SEV(lg_, warning) << "It is strongly recommended to set a function " <<
                        "context for variable mutation";
                    this->declMatchers.push_back(std::make_unique<const DeclarationMatcher>(
                                functionDecl(hasBody(forEachDescendant(declRefExpr(to(namedDecl(
                                                        hasName(*var_)).bind(
                                                        declName_))).bind(varName_))))
                                ));
                }
            } else {
                if (!var_)
                    BOOST_LOG_SEV(lg_, error) <<
                        "No variable name to be mutated is found in configuration";
            }
        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
        virtual std::unique_ptr<MutantPoolTy> mutate() override;
    private:
        const std::string varName_;
        const std::string declName_;
        boost::optional<std::string> var_;
        boost::optional<std::string> func_;
        boost::optional<std::string> caller_;
        boost::optional<std::string> val_;
        varMutantMapTy varMutant_;
};
#endif
