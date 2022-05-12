#include "LocalVarOperator.h"

void LocalVarOperator::run(const MatchFinder::MatchResult &Result) {
    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(
                std::async(std::launch::deferred,
                    [&oprtName = this->oprtName_,
                    val = this->val_, var = Result.Nodes.getNodeAs<clang::DeclRefExpr>(varName_),
                    decl = Result.Nodes.getNodeAs<clang::NamedDecl>(declName_),
                    &varMutant = this->varMutant_,
                    &lg = this->lg_] (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        assert(var && decl);
                        std::string varName(decl->getNameAsString());
                        varMutantMapTy::iterator i = varMutant.find(varName);
                        if (i == varMutant.end()) {
                            varMutant.insert({varName, std::make_shared<Mutant>(
                                            std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                                Result.Context->getLangOpts()),
                                            Result.SourceManager->getFilename(
                                                var->getBeginLoc()).str(),
                                            oprtName, rand())});
                        }
                        // FIXME if insert failed dereferencing i is a security bug
                        i = varMutant.find(varName);
                        assert(i != varMutant.end());
                        if (val)
                            i->second->ReplaceText(var->getSourceRange(), *val);
                        else
                            i->second->RemoveText(var->getSourceRange());

                        return nullptr;
                    }, Result)));

}

std::unique_ptr<Operator::MutantPoolTy> LocalVarOperator::mutate()
{
    std::unique_ptr<MutantPoolTy> ret = std::make_unique<Operator::MutantPoolTy>();
    for (auto i = this->candidates_.begin();
            i != this->candidates_.end(); i++) {
        // Ignore the returned mutant, as we will push mutants in the mapping to return
        (*i)->get();
    }
    for (auto i = this->varMutant_.cbegin(); i != this->varMutant_.cend(); i++) {
        ret->push_back(i->second);
    }
    return ret;
}
