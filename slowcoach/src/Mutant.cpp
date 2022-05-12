#include "Mutant.h"

#include "boost/filesystem.hpp"

std::error_code Mutant::WriteOutput()
{
    const clang::SourceManager &srcMgr = this->rewriter_->getSourceMgr();
    std::error_code EC;
    const std::string &AbsPath = this->srcPath_;
    assert(!AbsPath.empty());

    // Iterator type on primitive types, just a raw pointer
    // And we randomly access the string by manipulating integers
    auto LastDot = AbsPath.rfind('.');
    auto LastSlash = AbsPath.rfind('/');
    // Some version of clang may only return the file name instead of the absolute path.
    // Double check the validity of the LastSlash for safety
    assert(LastDot != std::string::npos || (LastSlash == std::string::npos && LastDot > LastSlash));

    // FIXME Implement this path more efficiently
    // Skip the dot itself
    const std::string FileExtension(AbsPath.begin() + LastDot + 1, AbsPath.end());
    // Skip the last slash
    const std::string FileName(AbsPath.begin() + (LastSlash != std::string::npos ? LastSlash + 1 : 0),
            AbsPath.begin() + LastDot);

    // NOTE simply using the source file name as the prefix
    // Take the last slash in
    std::string PrefixName(AbsPath.begin(), AbsPath.begin() + LastSlash + 1);
    PrefixName.append(FileName).append("_").append(FileExtension);

    if (!boost::filesystem::exists(PrefixName))
        boost::filesystem::create_directories(PrefixName.c_str());

    std::ostringstream os;
    os << PrefixName << '/' << FileName << '_' << this->mutationName_ << '_' << this->mutId_ << '.' << FileExtension;

    llvm::raw_fd_ostream OutFile(os.str(), EC, llvm::sys::fs::F_None);

    this->rewriter_->getEditBuffer(srcMgr.getMainFileID()).write(OutFile);
    OutFile.close();
    return EC;
}
