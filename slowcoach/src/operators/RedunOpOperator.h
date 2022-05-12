#ifndef REDUN_OP_OPERATOR_H
#define REDUN_OP_OPERATOR_H
#include "LineNumOperator.h"
#include "RedunOperation.h"

class RedunOpOperator : public LineNumOperator {
    public:
        RedunOpOperator (const pt::ptree &config) : LineNumOperator(config),
        preprosessor_(config.get_optional<std::string>("preprosessor")) {
            parseOpConfig(config, codeStr_, lg_);
        }
        virtual void genCandidates(const clang::SourceLocation loc,
                clang::SourceManager &srcMgr, const clang::ASTContext &ctx);
    private:
        std::stringstream codeStr_;
        boost::optional<std::string> preprosessor_;
};

#endif
