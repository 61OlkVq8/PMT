#ifndef REDUN_SYNC_OPERATOR_H
#define REDUN_SYNC_OPERATOR_H

#include "MatcherOperator.h"

class RedunSyncOperator : public MatcherOperator {
    public:
        RedunSyncOperator (const pt::ptree &config) : MatcherOperator(config) {
            std::unique_ptr<const DeclarationMatcher> matcherP =
                std::make_unique<const DeclarationMatcher>(functionDecl().bind(this->oprtName_));
            this->declMatchers.push_back(std::move(matcherP));
        }
        virtual void run(const MatchFinder::MatchResult &Result) override;
};
#endif
