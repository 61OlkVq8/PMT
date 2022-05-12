import os
import logging
import name
import subprocess


class Compilation:

    def __init__(self, projectName, workdir, prefix=None):
        self.pwd = os.path.abspath(workdir)
        self.compDB = os.path.join(self.pwd, 'compile_commands.json')
        self.compErrors = os.path.join(self.pwd, 'mutants_compile_errors')
        self.name = os.path.basename(self.pwd)
        if not os.path.exists(self.compErrors):
            os.mkdir(self.compErrors)
        elif os.path.exists(self.compErrors) and not os.path.isdir(self.compErrors):
            logging.info('{0} is not a directory'.format(self.compErrors))
        self.parser = name.MutantMatcher
        if prefix is not None:
            self.prefix = os.path.abspath(prefix)
        self.projectName = projectName
        self.passedTests = None
        self.isMutant = False

    def conf(self, confParam=None):
        pass

    def build(self):
        pass

    def install(self, mutantAbsPath=None):
        installCmd = ['make', 'install']
        pInstall = subprocess.Popen(installCmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        _, _ = pInstall.communicate()
        # FIXME Add error handling

    def parseMutantName(self, mutantName):
        m = self.parser.match(mutantName)
        return m.groupdict()
