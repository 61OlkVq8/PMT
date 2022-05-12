#include "OblivionOperator.h"

inline bool OblivionOperator::replacable(const clang::Stmt *parent)
{
    // The reference parent should no be an array subscription
    if (llvm::dyn_cast_or_null<clang::ArraySubscriptExpr>(parent)) {
        BOOST_LOG_SEV(this->lg_, debug) <<
            "The matched local variable reference is an array to be subscribed";
        return false;
    }

    if (llvm::dyn_cast_or_null<clang::MemberExpr>(parent)) {
        BOOST_LOG_SEV(this->lg_, debug) <<
            "The matched local variable reference is an object member referece: e.g. foo->bar;";
        return false ;
    }


    // Unary parents could also yield problems
    const clang::UnaryOperator *refPrnt = llvm::dyn_cast_or_null<clang::UnaryOperator>(parent);
    if (refPrnt &&
            // The parent of the declRef should not be increment or decrement
            (refPrnt->isIncrementDecrementOp() ||
             // Nor should it be address oprt
             clang::UnaryOperator::getOpcodeStr(refPrnt->getOpcode()).equals("&"))) {
        BOOST_LOG_SEV(this->lg_, debug) <<
            "The matched local variable reference is in an unary oprt";
        return false;
    }
    return true;
}

void OblivionOperator::run(const MatchFinder::MatchResult &Result)
{
    const clang::DeclRefExpr *ref = Result.Nodes.getNodeAs<clang::DeclRefExpr>(this->declRefName_);
    const clang::BinaryOperator *assign =
        Result.Nodes.getNodeAs<clang::BinaryOperator>(this->assignOpName_);
    const clang::Expr *initExpr = Result.Nodes.getNodeAs<clang::Expr>(this->initName_);

    if (!ref || !initExpr) {
        BOOST_LOG_SEV(this->lg_, error) << "libclang matchers bug fetching irrelevant AST nodes";
        return ;
    }
    if (!this->isRelevant(ref, Result.SourceManager))
        return ;

    if (assign && ref == assign->getLHS()) {
        BOOST_LOG_SEV(this->lg_, debug) << "The matched local variable reference is on the lhs";
        return ;
    }

    if (llvm::dyn_cast_or_null<clang::InitListExpr>(initExpr) ||
            llvm::dyn_cast_or_null<clang::CXXStdInitializerListExpr>(initExpr)) {
        BOOST_LOG_SEV(this->lg_, debug) <<
            "The matched initializer is list: e.g. foo = {1};";
        return ;
    }

    // Skip all blacklisted functions
    // FIXME Handle cpp Class::Methods notion
    const auto *call = llvm::dyn_cast_or_null<clang::CallExpr>(initExpr);
    if (call) {
        const auto *callee = call->getDirectCallee();
        if (callee && std::find(this->blacklistedFuncNames_.cbegin(),
                    this->blacklistedFuncNames_.cend(),
                    callee->getNameAsString()) != this->blacklistedFuncNames_.end()) {
            return ;
        }
    }

    const clang::ImplicitCastExpr *implicit =
        Result.Nodes.getNodeAs<clang::ImplicitCastExpr>(this->refPrntName_);
    if (!implicit) {
        if (!replacable(Result.Nodes.getNodeAs<clang::Stmt>(this->refPrntName_)))
            return ;
    } else {
        const clang::ASTContext::DynTypedNodeList &truePrnt = Result.Context->getParents(*implicit);
        // FIXME should check parents of implicit conversion node as replacable()
        for (auto i = truePrnt.begin(); i != truePrnt.end(); i++) {
            if (i->get<clang::MemberExpr>() ||
                    i->get<clang::ArraySubscriptExpr>())
                return ;
        }
    }

    const clang::VarDecl *decl = llvm::dyn_cast_or_null<clang::VarDecl>(ref->getDecl());
    assert(decl);

    this->addCandidate(
            std::make_unique<Operator::MutationOpTy>(
                std::async(std::launch::deferred,
                    [&oprtName = this->oprtName_,
                    initExpr, ref, decl,
                    &varMutant = this->varMutant_,
                    buildReplaceString = this->buildReplaceString,
                    &lg = this->lg_] (const MatchFinder::MatchResult &Result) ->
                    std::shared_ptr<Mutant> {
                        std::string varName(decl->getNameAsString());
                        varMutantMapTy::iterator i = varMutant.find(varName);
                        if (i == varMutant.end()) {
                            varMutant.insert({varName, std::make_shared<Mutant>(
                                            std::make_unique<clang::Rewriter>(*Result.SourceManager,
                                                Result.Context->getLangOpts()),
                                            Result.SourceManager->getFilename(
                                                ref->getBeginLoc()).str(),
                                            oprtName, rand())});
                        }
                        // FIXME if insert failed dereferencing i is a security bug
                        i = varMutant.find(varName);
                        assert(i != varMutant.end());
                        std::string substitute;
                        llvm::raw_string_ostream rso(substitute);
                        buildReplaceString(rso, ref, initExpr, decl, Result.Context);
                        BOOST_LOG_SEV(lg, debug) << rso.str();
                        i->second->ReplaceText(ref->getSourceRange(), rso.str());
                        return nullptr;
                    }, Result)));
}

std::unique_ptr<Operator::MutantPoolTy> OblivionOperator::mutate()
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
