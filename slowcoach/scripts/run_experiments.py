#!/usr/bin/python3

import os
import logging
import gnu_compilation
import cmake_compilation
import experiments
import meson_compilation

from grep_experiments import grepCov, grepExpr
from functools import partial
from random import sample


def main():
    projectRoot = '{0}/slowcoach/'.format(os.getenv('HOME'))
    configs = os.path.join(projectRoot, 'config')
    logging.basicConfig(filename='experiment.log',
                        format='[%(asctime)s]-%(levelname)s %(message)s', level=logging.INFO)

    ge = experiments.Experiment(gnu_compilation.GNUCompilation('grep',
                                os.path.join(projectRoot, 'mutation-targets', 'grep'),
                                os.path.join(projectRoot, 'lib', 'gnulib'),
                                os.path.join(projectRoot, 'mutation-targets', 'grep_install')),
                                os.path.join(projectRoot, 'build', 'slowcoach'),
                                os.path.join(configs, 'grep_config.xml'), 10)
    # ge.experiment(grepCov, grepExpr, experiments.mutantInCoverage, partial(sample, k=100))
    ge.experiment(grepCov, grepExpr, experiments.mutantInCoverage, partial(sample, k=100))

    # xe = experiments.Experiment(gnu_compilation.GNUCompilation('libxml2',
    #                             os.path.join(projectRoot, 'mutation-targets', 'libxml2'),
    #                             os.path.join(projectRoot, 'mutation-targets', 'libxml2_install')),
    #                             os.path.join(projectRoot, 'build', 'slowcoach'),
    #                             os.path.join(configs, 'grep_config.xml'))
    # xe.experiment()
    # xppe = experiments.Experiment(gnu_compilation.GNUCompilation('libxml++',
    #                               os.path.join(projectRoot, 'mutation-targets', 'libxmlplusplus'),
    #                               os.path.join(projectRoot, 'mutation-targets', 'libxmlplusplus_install')),
    #                               os.path.join(projectRoot, 'build', 'slowcoach'),
    #                               os.path.join(configs, 'grep_config.xml'))
    # xppe.experiment()
    # jsonc = experiments.Experiment(gnu_compilation.GNUCompilation('json-c',
    #                                os.path.join(projectRoot, 'mutation-targets', 'json-c'),
    #                                os.path.join(projectRoot, 'mutation-targets', 'json-c_install')),
    #                                os.path.join(projectRoot, 'build', 'slowcoach'),
    #                                os.path.join(configs, 'grep_config.xml'))
    # jsonc.experiment()

    # libyaml = experiments.Experiment(gnu_compilation.GNUCompilation('libyaml',
    #                                  os.path.join(projectRoot, 'mutation-targets', 'libyaml'),
    #                                  os.path.join(projectRoot, 'mutation-targets', 'libyaml_install')),
    #                                  os.path.join(projectRoot, 'build', 'slowcoach'),
    #                                  os.path.join(configs, 'grep_config.xml'))
    # libyaml.experiment()
    # yamlcpp = experiments.Experiment(cmake_compilation.CmakeCompilation('yaml-cpp',
    #                                  os.path.join(projectRoot, 'mutation-targets', 'yaml-cpp'),
    #                                  os.path.join(projectRoot, 'mutation-targets', 'yaml-cpp_install')),
    #                                  os.path.join(projectRoot, 'build', 'slowcoach'),
    #                                  os.path.join(configs, 'grep_config.xml'))
    # yamlcpp.experiment()

    # tomlplusplus = experiments.Experiment(meson_compilation.MesonCompilation('toml++',
    #                                       os.path.join(projectRoot, 'mutation-targets', 'tomlplusplus'),
    #                                       os.path.join(projectRoot, 'mutation-targets', 'tomlplusplus_install')),
    #                                       os.path.join(projectRoot, 'build', 'slowcoach'),
    #                                       os.path.join(configs, 'libxml2_config.xml'))
    # tomlplusplus.experiment()

    # libyaml = experiments.Experiment(gnu_compilation.GNUCompilation('libyaml',
    #                                  os.path.join(projectRoot, 'mutation-targets', 'libyaml'),
    #                                  os.path.join(projectRoot, 'mutation-targets', 'libyaml_install')),
    #                                  os.path.join(projectRoot, 'build', 'slowcoach'),
    #                                  os.path.join(configs, 'grep_config.xml'))
    # libyaml.experiment()


if __name__ == '__main__':
    main()
