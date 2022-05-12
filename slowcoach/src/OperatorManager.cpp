#include "OperatorManager.h"
#include "config.h"
#include "boost/optional.hpp"

#define REGISTER_OPERATOR(OPERATOR_NAME, CLASS_NAME, OP_TY) \
    else if (oprtName == OPERATOR_NAME) { \
            OperatorManager::register##OP_TY##Operator( \
                    std::make_unique<CLASS_NAME>(oprt.second)); \
    } \

#define REGISTER_MATCH_OPERATOR(OPERATOR_NAME, CLASS_NAME) \
    REGISTER_OPERATOR(OPERATOR_NAME, CLASS_NAME, Matcher) \

#define REGISTER_LINENUM_OPERATOR(OPERATOR_NAME, CLASS_NAME) \
    REGISTER_OPERATOR(OPERATOR_NAME, CLASS_NAME, LineNum) \

namespace pt = boost::property_tree;

clang::ast_matchers::MatchFinder OperatorManager::Finder;
OperatorManager::MatcherOperatorPoolTy OperatorManager::MatcherOperators;
OperatorManager::LineNumOperatorPoolTy OperatorManager::LineNumOperators;
std::vector<InjectSpot> OperatorManager::InjectSpots;

void OperatorManager::initialize()
{
    MatcherOperators.reserve(1024UL);
    LineNumOperators.reserve(1024UL);

    InjectSpots.reserve(1024UL);
    registerOperators();
    BOOST_FOREACH(pt::ptree::value_type &injtPt,
            OperatorConfiguration::Tree.get_child("config.inject-spots")) {
        assert(injtPt.first == "src");
        InjectSpots.push_back(InjectSpot(injtPt.second));
    }
}

void OperatorManager::registerMatcherOperator(std::unique_ptr<MatcherOperator> MatcherOperatorP)
{
    for (auto i = MatcherOperatorP->getStmtMatcherConstBegin();
            i != MatcherOperatorP->getStmtMatcherConstEnd(); i++) {
        Finder.addMatcher(**i, MatcherOperatorP.get());
    }
    for (auto i = MatcherOperatorP->getDeclMatcherConstBegin();
            i != MatcherOperatorP->getDeclMatcherConstEnd(); i++) {
        Finder.addMatcher(**i, MatcherOperatorP.get());
    }
    MatcherOperators.push_back(std::move(MatcherOperatorP));
}

static inline std::error_code mutate_(Operator &op)
{
    std::unique_ptr<MutantManager::MutantPoolTy> mutantsP;
    mutantsP = op.mutate();
    return MutantManager::writeMutants(std::move(mutantsP));
}

void OperatorManager::mutateAll()
{
    for (auto i = MatcherOperators.cbegin(); i != MatcherOperators.cend(); i++) {
        // FIXME Handle error code
        mutate_(**i);
    }
    for (auto i = LineNumOperators.cbegin(); i != LineNumOperators.cend(); i++) {
        // FIXME Handle error code
        mutate_(**i);
    }
}

void OperatorManager::activateMutation(const ASTPoolTy &ast)
{
    for (auto i = ast.cbegin(); i < ast.cend(); i++) {
        Finder.matchAST((*i)->getASTContext());
    }
    for (auto i = InjectSpots.cbegin(); i < InjectSpots.cend(); i++) {
        for (auto j = ast.cbegin(); j < ast.cend(); j++) {
            auto srcName = (*j)->getOriginalSourceFileName();
            auto srcEntry = (*j)->getFileManager().getFile(srcName);
            if (srcName.str() != *(i->sourceFile_)) continue;
            for (auto k = LineNumOperators.cbegin(); k < LineNumOperators.cend(); k++) {
                for (auto l = i->lineNums_.cbegin(); l < i->lineNums_.cend(); l++) {
                    (*k)->genCandidates((*j)->getLocation(*srcEntry, unsigned(*l), 0UL),
                            (*j)->getSourceManager(), (*j)->getASTContext());
                }
            }
        }
    }
}

// FIXME Remove this when introducing options enable/disable features
void OperatorManager::registerOperators()
{
    // Ugly enough decision list
    BOOST_FOREACH(pt::ptree::value_type &oprt,
            OperatorConfiguration::Tree.get_child("config.operators")) {
        const std::string &oprtName = oprt.first;
        if (oprtName == "dummy") {
            OperatorManager::registerMatcherOperator(
                    std::make_unique<DummyOperator>(oprt.second));
        }
        REGISTER_MATCH_OPERATOR("redun-op-loop", RedunOpLoopOperator)
        REGISTER_LINENUM_OPERATOR("redun-op", RedunOpOperator)
        REGISTER_MATCH_OPERATOR("redun-sync", RedunSyncOperator)
        REGISTER_MATCH_OPERATOR("oblivion", OblivionOperator)
        REGISTER_MATCH_OPERATOR("slowpath", SlowpathOperator)
        REGISTER_MATCH_OPERATOR("fastpath-cond", FastpathCondOperator)
        REGISTER_MATCH_OPERATOR("func", FuncOperator)
        REGISTER_MATCH_OPERATOR("fastpath", FastpathOperator)
        REGISTER_MATCH_OPERATOR("lazy-update", LazyUpdateOperator)
        REGISTER_MATCH_OPERATOR("local-var", LocalVarOperator)
        REGISTER_MATCH_OPERATOR("decl", DeclOperator)
        REGISTER_MATCH_OPERATOR("loop-unbreak", LoopUnbreakOperator)
        REGISTER_MATCH_OPERATOR("redun-op-decl", RedunOpDeclOperator)
        else
            BOOST_LOG_SEV(MgmtLogger, error) << "Cannot instantialize oprt " << oprtName;
    }
}
