#ifndef CONFIG_H
#define CONFIG_H
#include "boost/property_tree/ptree.hpp"
#include "boost/property_tree/xml_parser.hpp"
#include "boost/filesystem.hpp"
#include "boost/log/trivial.hpp"
#include "boost/core/noncopyable.hpp"

namespace pt = boost::property_tree;
namespace fs = boost::filesystem;

const static fs::path SrcPath(fs::path(CMAKE_SOURCE_DIR));
const static fs::path ProjectRoot(SrcPath.parent_path());
const static fs::path ConfigPath(ProjectRoot / "config") ;

using namespace boost::log::trivial;

extern boost::log::sources::severity_logger<severity_level> MgmtLogger;

struct OperatorConfiguration: public boost::noncopyable {
    static void confInit(std::string &fileName) {
        fs::path p(fs::canonical(fs::path(fileName)));
        if (fs::exists(p)) {
            OperatorConfiguration::ConfFile = p;
            pt::read_xml(p.string(), OperatorConfiguration::Tree);
        } else {
            BOOST_LOG_SEV(MgmtLogger, warning) << "Cannot find " << fileName
                << ". Nothing to do.";
        }
    }
    static fs::path ConfFile;
    static pt::ptree Tree;

    // For line number operators
    static std::vector<std::string> SrcFileNames;
    static std::vector<size_t> LineNum;
};

#endif
