#ifndef MUTANT_H
#define MUTANT_H
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "llvm/Support/FileSystem.h"
#include "clang/Basic/SourceManager.h"
#include "llvm/Support/raw_ostream.h"

#include <string>
#include <memory>
#include <sstream>

#include "boost/log/sources/severity_logger.hpp"
#include "boost/log/trivial.hpp"

using namespace boost::log::trivial;

class Mutant {
    public:
        explicit Mutant(std::unique_ptr<clang::Rewriter> rewriter, const std::string src,
                std::string MutName, uint16_t mutId) :
            // FIXME Do not copy the rewriter buffer and source code paths
            rewriter_(std::move(rewriter)), srcPath_(src), mutationName_(MutName), mutId_(mutId) { }
        Mutant(const Mutant &mut) = delete;
        Mutant(Mutant &&mut) = delete;
        Mutant &operator =(const Mutant &mut) = delete;
        Mutant &operator =(Mutant &&mut) = delete;
        virtual ~Mutant() = default;

        std::error_code WriteOutput();

        // std::unique_ptr<clang::Rewriter> getRewriter() { return this->rewriter_; }

        bool InsertText(clang::SourceLocation Loc, llvm::StringRef Str,
                bool InsertAfter = true, bool indentNewLines = false) {
            if (!Loc.isValid()) return false;
            if (InsertAfter)
                BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                    "] Inserting after " << Loc.printToString(this->rewriter_->getSourceMgr());
            else
                BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                    "] Inserting before " << Loc.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->InsertText(Loc, Str, InsertAfter, indentNewLines);
        }

        bool InsertTextAfter(clang::SourceLocation Loc, llvm::StringRef Str) {
            if (!Loc.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Inserting after " << Loc.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->InsertText(Loc, Str);
        }

        bool InsertTextAfterToken(clang::SourceLocation Loc, llvm::StringRef Str) {
            if (!Loc.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Inserting after token at " << Loc.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->InsertTextAfterToken(Loc, Str);
        }

        bool InsertTextBefore(clang::SourceLocation Loc, llvm::StringRef Str) {
            if (!Loc.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Inserting before " << Loc.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->InsertText(Loc, Str, false);
        }

        bool RemoveText(clang::SourceLocation Start, unsigned Length,
                clang::Rewriter::RewriteOptions opts = clang::Rewriter::RewriteOptions()) {
            if (!Start.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Removing from " << Start.printToString(this->rewriter_->getSourceMgr()) <<
                " with length " << Length;
            return this->rewriter_->RemoveText(Start, Length, opts);
        }

        bool RemoveText(clang::CharSourceRange range,
                clang::Rewriter::RewriteOptions opts = clang::Rewriter::RewriteOptions()) {
            if (!range.isValid()) return false;
            return this->rewriter_->RemoveText(range.getBegin(), this->rewriter_->getRangeSize(range, opts), opts);
        }

        bool RemoveText(clang::SourceRange range,
                clang::Rewriter::RewriteOptions opts = clang::Rewriter::RewriteOptions()) {
            if (!range.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Removing " << range.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->RemoveText(range.getBegin(),
                    this->rewriter_->getRangeSize(range, opts), opts);
        }

        bool ReplaceText(clang::SourceLocation Start, unsigned OrigLength,
                llvm::StringRef NewStr) {
            if (!Start.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Replacing from " << Start.printToString(this->rewriter_->getSourceMgr()) <<
                " with length " << OrigLength;
            return this->rewriter_->ReplaceText(Start, OrigLength, NewStr);
        }

        bool ReplaceText(clang::CharSourceRange range, llvm::StringRef NewStr) {
            if (!range.isValid()) return false;
            return this->rewriter_->ReplaceText(range.getBegin(),
                    this->rewriter_->getRangeSize(range), NewStr);
        }

        bool ReplaceText(clang::SourceRange range, llvm::StringRef NewStr) {
            if (!range.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Replacing " << range.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->ReplaceText(range.getBegin(), this->rewriter_->getRangeSize(range), NewStr);
        }

        bool ReplaceText(clang::SourceRange range, clang::SourceRange replacementRange) {
            if (!range.isValid()) return false;
            BOOST_LOG_SEV(lg_, info) << '[' << this->mutationName_ << "] [" << this->mutId_ <<
                "] Replacing " << range.printToString(this->rewriter_->getSourceMgr());
            return this->rewriter_->ReplaceText(range, replacementRange);
        }

    private:
        std::unique_ptr<clang::Rewriter> rewriter_;
        clang::FileID editBufFileID_;
        std::string srcPath_;
        std::string mutationName_;
        uint64_t mutId_;
        boost::log::sources::severity_logger<boost::log::trivial::severity_level> lg_;
};

#endif
