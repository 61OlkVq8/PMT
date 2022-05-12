#ifndef OPERATOR_MANAGER_H
#define OPERATOR_MANAGER_H

#include <vector>
#include <memory>
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/Tooling.h"

#include "MatcherOperator.h"
#include "LineNumOperator.h"
#include "operators/DummyOperator.h"
#include "operators/RedunSyncOperator.h"
#include "operators/RedunOpOperator.h"
#include "operators/RedunOpLoopOperator.h"
#include "operators/OblivionOperator.h"
#include "operators/SlowpathOperator.h"
#include "operators/FastpathCondOperator.h"
#include "operators/FastpathOperator.h"
#include "operators/FuncOperator.h"
#include "operators/LazyUpdateOperator.h"
#include "operators/LocalVarOperator.h"
#include "operators/DeclOperator.h"
#include "operators/RedunOpDeclOperator.h"
#include "operators/LoopUnbreakOperator.h"

#include "MutantManager.h"
#include "InjectSpot.h"

#include "boost/core/noncopyable.hpp"

extern boost::log::sources::severity_logger<boost::log::trivial::severity_level> MgmtLogger;

class OperatorManager : private boost::noncopyable {
    public:
        using MatcherOpeartorTy = std::unique_ptr<MatcherOperator>;
        using MatcherOperatorPoolTy = std::vector<MatcherOpeartorTy>;
        using LineNumOperatorTy = std::unique_ptr<LineNumOperator>;
        using LineNumOperatorPoolTy = std::vector<LineNumOperatorTy>;
        using OperatorPoolTy = std::vector<std::unique_ptr<Operator>>;

        OperatorManager() = delete;

        using ASTPoolTy = std::vector<std::unique_ptr<clang::ASTUnit>>;

        static void registerMatcherOperator(std::unique_ptr<MatcherOperator> MatcherOperatorP);
        static void registerLineNumOperator(std::unique_ptr<LineNumOperator> LineNumOperatorP) {
            LineNumOperators.push_back(std::move(LineNumOperatorP));
        }
        static void mutateAll();
        static void initialize();

        static void activateMutation(const ASTPoolTy &asts);

        static clang::ast_matchers::MatchFinder Finder;

    private:
        static void registerOperators();

        static MatcherOperatorPoolTy MatcherOperators;

        static std::vector<InjectSpot> InjectSpots;
        static LineNumOperatorPoolTy LineNumOperators;
};
#endif
