#ifndef LINENUM_OPERATOR_H
#define LINENUM_OPERATOR_H
#include "Operator.h"
#include <vector>

class LineNumOperator : public Operator {
    public:
        LineNumOperator(const pt::ptree &config) : Operator(config) { }
        virtual ~LineNumOperator() = default;
        virtual void genCandidates(const clang::SourceLocation loc,
                clang::SourceManager &srcMgr, const clang::ASTContext &ctx) = 0;
};
#endif
