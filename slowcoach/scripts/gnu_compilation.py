import compilation
import os
import logging

import subprocess
import multiprocessing
from threading import Semaphore


GNUTestStates = set(['PASS', 'SKIP', 'FAIL', 'XFAIL', 'XPASS', 'ERROR'])


class GNUCompilation(compilation.Compilation):

    def __init__(self, projectName, workdir, gnulibSrc, prefix=None):
        super(GNUCompilation, self).__init__(projectName, workdir, prefix)
        self.gnulibSrc = gnulibSrc

    def conf(self, confParam=None, mustrun=False):
        if os.path.exists(os.path.join(self.pwd, 'Makefile')) and mustrun == False:
            return
        confEnv = os.environ.copy()
        confEnv['CC'] = 'clang'
        confEnv['CXX'] = 'clang++'
        assert(self.gnulibSrc is not None and os.path.exists(self.gnulibSrc))
        confEnv['GNULIB_SRCDIR'] = self.gnulibSrc
        if os.path.exists('{0}/bootstrap'.format(self.pwd)):
            bootCmd = ['{0}/bootstrap'.format(self.pwd), '--copy']
        elif os.path.exists('{0}/autogen.sh'.format(self.pwd)) and self.prefix is not None:
            bootCmd = ['{0}/autogen.sh'.format(self.pwd), '--prefix={0}'.format(self.prefix)]
        pBoot = subprocess.Popen(bootCmd, env=confEnv, cwd=self.pwd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = pBoot.communicate()
        if not pBoot.returncode == 0:
            print(out.decode())
            print(err.decode())
            raise subprocess.CalledProcessError(pBoot.returncode, bootCmd)

        confCmd = ['{0}/configure'.format(self.pwd)]
        if self.prefix is not None:
            confCmd.append('--prefix={0}'.format(self.prefix))
        if confParam is not None:
            confCmd.append(confParam)
        pConf = subprocess.Popen(confCmd, env=confEnv, cwd=self.pwd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        _, err = pConf.communicate()
        if not pConf.returncode == 0:
            print(err.decode())
            raise subprocess.CalledProcessError(pConf.returncode, confCmd)

    def build(self):
        if not os.path.exists(self.compDB):
            compCmd = ['bear', 'make', '-j{0}'.format(multiprocessing.cpu_count())]
        else:
            compCmd = ['make', '-j{0}'.format(multiprocessing.cpu_count())]

        pComp = subprocess.Popen(compCmd, cwd=self.pwd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        out, err = pComp.communicate()

        # Logging failed compilation but do not raise the exception
        if not pComp.returncode == 0:
            if not self.isMutant:
                logging.error('{0} does not compile'.format(self.name))
                with open(os.path.join(self.compErrors,
                          'origin_errors'), 'w') as f:
                    f.write(err.decode())
                raise subprocess.CalledProcessError(pComp.returncode, pComp)
            with open(os.path.join(self.compErrors,
                      '{0}_{1}_{2}_errors'.format(self.source, self.mutation, self.id)), 'w') as f:
                f.write(err.decode('utf-8'))
            logging.info('{0} mutant at {1} failed to compile'.format(self.projectName,
                mutantAbsPath))
        return pComp.returncode
