#ifndef INJECT_SPOT_H
#define INJECT_SPOT_H
#include <string>
#include <vector>
#include "boost/property_tree/ptree.hpp"

namespace pt = boost::property_tree;

extern boost::log::sources::severity_logger<boost::log::trivial::severity_level> MgmtLogger;

struct InjectSpot {
    InjectSpot(const pt::ptree &config) : sourceFile_(config.get_optional<std::string>("<xmlattr>.name")) {
        assert(sourceFile_);
        lineNums_.reserve(1024UL);
        BOOST_FOREACH(const pt::ptree::value_type &ln, config.get_child("lines")) {
            auto &l = ln.second.data();
            lineNums_.push_back(size_t(atol(l.c_str())));
        }
    }
    boost::optional<std::string> sourceFile_;
    std::vector<size_t> lineNums_;
};

#endif
