import compilation
import os
import subprocess
import multiprocessing
import logging


class CmakeCompilation(compilation.Compilation):

    def build(self, mutantAbsPath=None):
        buildDir = os.path.join(self.pwd, '_build')
        if os.path.exists(buildDir) and not os.path.isdir(buildDir):
            raise NotADirectoryError
        else:
            os.makedirs(buildDir)

        os.chdir(buildDir)
        if not os.path.exists(os.path.join(buildDir, 'Makefile')):
            cmakeOpts = ['cmake', '-DCMAKE_EXPORT_COMPILE_COMMANDS=True',
                         '-DCMAKE_C_COMPILER=clang', '-DCMAKE_CXX_COMPILER=clang++', self.pwd]
            pCmake = subprocess.Popen(cmakeOpts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pCmake.communicate()

        compOpts = ['make', '-j{0}'.format(multiprocessing.cpu_count())]
        pComp = subprocess.Popen(compOpts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = pComp.communicate()

        # Logging failed compilation but do not raise the exception
        if not pComp.returncode == 0:
            if mutantAbsPath is None:
                logging.error('{0} does not compile'.format(self.name))
                with open(os.path.join(self.compErrors,
                          'origin_errors'), 'w') as f:
                    f.write(err.decode('utf-8'))
                raise subprocess.CalledProcessError(pComp.returncode, pComp)
            r = self.parseMutantName(os.path.basename(mutantAbsPath))
            assert(r is not None)
            with open(os.path.join(self.compErrors,
                      '{0}_{1}_{2}_errors'.format(r['source'], r['mutation'], r['id'])), 'w') as f:
                f.write(err.decode('utf-8'))
            logging.info('{0} mutant at {1} failed to compile'.format(self.projectName, mutantAbsPath))

        os.chdir(self.pwd)
