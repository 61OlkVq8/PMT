#include "llvm/Support/CommandLine.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/ASTMatchers/ASTMatchers.h"

#include <memory>
#include <vector>
#include <iostream>

#include "config.h"

#include "OperatorManager.h"
#include "MutantManager.h"

#include "boost/log/utility/setup/file.hpp"
#include "boost/log/utility/setup/common_attributes.hpp"

using namespace clang::ast_matchers;
using namespace clang::tooling;

boost::log::sources::severity_logger<boost::log::trivial::severity_level> MgmtLogger;

static llvm::cl::OptionCategory CheckerCategory("slowcoach options");
static llvm::cl::extrahelp CommonHelp(clang::tooling::CommonOptionsParser::HelpMessage);

llvm::cl::opt<std::string> ConfFileName("c",
        llvm::cl::desc("The path to configuration file"),
        llvm::cl::value_desc("conf_file"));

llvm::cl::opt<std::string> LogFileName("l",
        llvm::cl::desc("The path to log file"),
        llvm::cl::value_desc("conf_file"),
        llvm::cl::init("slowcoach.log"));

int main(int argc, const char **argv)
{
    clang::tooling::CommonOptionsParser ArgParser(argc, argv, CheckerCategory);
    clang::tooling::ClangTool Tool(ArgParser.getCompilations(),
            ArgParser.getSourcePathList());

    int ret;
    OperatorManager::ASTPoolTy ast;

    ast.reserve(1024);
    ret = Tool.buildASTs(ast);

    if (!ConfFileName.empty())
        OperatorConfiguration::confInit(ConfFileName);

    boost::log::register_simple_formatter_factory<boost::log::trivial::severity_level,
        char>("Severity");
    boost::log::add_file_log(
            boost::log::keywords::file_name = LogFileName,
            boost::log::keywords::auto_flush = true,
            boost::log::keywords::open_mode = (std::ios::out | std::ios::app),
            boost::log::keywords::format = "[%TimeStamp%] (%LineID%) <%Severity%>: %Message%"
            );
    boost::log::add_common_attributes();

    OperatorManager::initialize();

    OperatorManager::activateMutation(ast);

    OperatorManager::mutateAll();
    return ret;
}
