#include "RedunOperation.h"

static inline void buildBody(std::stringstream &codeStr_, const boost::optional<std::string> &body)
{
    if (body) {
        codeStr_ << '{' << *body << '}';
    } else {
        codeStr_ << "{}";
    }
    codeStr_ << '\n';
}

// FIXME Hackish implementation here
// It does not check validity of attributes, e.g. init statement makes no effect when
// specified with while op
// Also comparing strings is VERY INEFFICIENT
void parseOpConfig(const pt::ptree &config, std::stringstream &codeStr_,
        boost::log::sources::severity_logger<boost::log::trivial::severity_level> &lg) {
    boost::optional<std::string> op = config.get_optional<std::string>("op");
    boost::optional<std::string> cond = config.get_optional<std::string>("cond");
    boost::optional<std::string> var = config.get_optional<std::string>("var");
    boost::optional<std::string> body = config.get_optional<std::string>("body");
    codeStr_ << '\n';
    if (!op || *op == "for") {
        if (!op)
            BOOST_LOG_SEV(lg, warning) << "No operation specified. Applying default for loop";
        if (var)
            codeStr_ << *var << '\n';
        codeStr_ << "for (";
        boost::optional<std::string> init = config.get_optional<std::string>("init");
        if (init)
            codeStr_ << *init << ';';
        else
            codeStr_ << "int itera = 0;";

        boost::optional<std::string> cond = config.get_optional<std::string>("cond");
        // Default with 1000 loops
        if (cond)
            codeStr_ << *cond << ';';
        else
            codeStr_ << "itera  < 1000;";
        boost::optional<std::string> inc = config.get_optional<std::string>("inc");
        if (inc)
            codeStr_ << *inc << ")";
        else
            codeStr_ << "itera++)";
        buildBody(codeStr_, body);
    } else if (*op == "while") {
        if (var)
            codeStr_ << *var << '\n';
        else
            codeStr_ << "int itera = 0;\n";
        codeStr_ << "while (";
        if (cond)
            codeStr_ << *cond << ')';
        else
            codeStr_ << "itera++ < 1000)";
        buildBody(codeStr_, body);
    } else if (*op == "do") {
        if (var)
            codeStr_ << *var << '\n';
        else
            codeStr_ << "int itera = 0;\n";
        codeStr_ << "do";
        buildBody(codeStr_, body);
        codeStr_ << "while (";
        if (cond)
            codeStr_ << *cond << ')';
        else
            codeStr_ << "itera++ < 1000);";
    } else {
        // Just dump the content of op
        codeStr_ << *op << '\n';
    }
}
