#ifndef REDUN_OPERATION_H
#define REDUN_OPERATION_H
#include "config.h"
// This function generates useless operation strings
void parseOpConfig(const pt::ptree &config, std::stringstream &codeStr_,
        boost::log::sources::severity_logger<boost::log::trivial::severity_level> &lg);
#endif
