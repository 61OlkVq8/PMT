import os
import subprocess
import name
import timeutils
import json
import proc
import gc
import logging
import math
from functools import partial
import signal

from multiprocessing.dummy import Pool
import random
from findtools.find_files import (find_files, Match)
from shutil import copy, copyfile

from mutate import Mutate


def passOrNot(testResultTuple):
    with open(testResultTuple[0] + testResultTuple[1]) as f:
        for line in f:
            x = line.split()
            # TODO Hardcode test result.
            # Could use re.split() for good if other metrics are to be matched
            if x[0] == ':test-result:':
                if x[1] == 'PASS':
                    return True
                else:
                    return False
    # FIXME Add logging about erroneous file input here
    return False


# FIXME This function actually does three things:
# 1. It checks if the coverage file exists and creates one if not
# 2. Have a dry run on selftests to get which tests are available
# 3. Run tests without coverage instrumentation to get the performance baseline
# All these three steps should be splitted into three functions and they are gnu related.
# So they should also be put into gnu_compilation.py
def grepCov(build, rep):
    ret = None
    # Step 1: Check coverage file
    covFile = os.path.join(build.pwd, 'coverage.json')
    if not os.path.exists(covFile):
        build.conf('CFLAGS=-fprofile-instr-generate -fcoverage-mapping', True)
        assert(os.path.exists(os.path.join(build.pwd, 'default.profraw')))
        build.build()

        testCmd = ['make', '-e', 'check-expensive']
        covEnv = os.environ.copy()
        covEnv['LLVM_PROFILE_FILE'] = 'default.profraw'
        testProc = subprocess.Popen(testCmd, env=covEnv, cwd=build.pwd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        testProc.communicate()
        assert(testProc.returncode == 0)

        covCmd = ['llvm-profdata', 'merge', '--output=default.profdata', '-sparse',
                'default.profraw']
        genCov = subprocess.Popen(covCmd, cwd=build.pwd)
        genCov.communicate()
        assert(genCov.returncode == 0)

        assert(os.path.exists(os.path.join(build.pwd, 'default.profdata')))
        covCmd = ['llvm-cov', 'export', '--instr-profile=default.profdata',
                os.path.join(build.pwd, 'src', 'grep')]
        genCov = subprocess.Popen(covCmd, cwd=build.pwd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = genCov.communicate()
        with open(covFile, 'w') as f:
            json.dump(json.loads(out.decode()), f)
        ret = json.loads(out.decode())
    else:
        with open(covFile) as f:
            ret = json.load(f)

    # Step 2: Get passed tests
    # Clean the test results first
    clean = ['make', 'clean']
    cleanProc = subprocess.Popen(clean, cwd=build.pwd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    cleanProc.communicate()

    check = ['make', 'check-expensive']
    testProc = subprocess.Popen(check, cwd=build.pwd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    testProc.communicate()

    prefix, _, testFiles = next(os.walk(os.path.join(build.pwd, 'tests')))

    # If not evaluated here test results would no longer be availabe in step 3
    build.passedTests = list(map(lambda x: os.path.basename(x[0]), filter(passOrNot,
            filter(lambda x: x[1] == '.trs', map(os.path.splitext,
        map(partial(os.path.join, prefix), testFiles))))))

    # Step 3: Dry run workloads for performance baseline and coverage to filter mutants
    testDir = os.path.join(build.pwd, 'tests')

    timeResultDir = os.path.join(build.pwd, 'performance_results')
    if not os.path.exists(timeResultDir):
        os.mkdir(timeResultDir)
    if not os.path.isdir(timeResultDir):
        raise NotADirectoryError

    baselineFile = os.path.join(timeResultDir, 'time_baseline.csv')
    # Clean to avoid cannot create log/trs errors
    cleanProc = subprocess.Popen(clean, cwd=build.pwd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    cleanProc.communicate()
    bigtxt = os.path.join(build.pwd, 'big.txt')
    if not os.path.exists(bigtxt):
        bigtxtDl = subprocess.Popen(['wget', 'https://norvig.com/big.txt'], cwd=build.pwd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        bigtxtDl.communicate()
        assert(bigtxtDl.returncode == 0)

    for test in build.passedTests:
        testEnv = os.environ.copy()
        testEnv['RUN_EXPENSIVE_TESTS'] = 'yes'
        testEnv['TESTS'] = test
        testCmd = ['time', '-q', '-a', '-f', timeutils.TimeFmt(test), '-o', baselineFile, 'make',
                '-e', 'check']
        for i in range(rep):
            testProc = subprocess.Popen(testCmd, env=testEnv, cwd=build.pwd,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, err = testProc.communicate()
            if len(err) > 0:
                print(err.decode('utf-8', 'replace'))

    bigtxtTestProc = subprocess.Popen(['parallel', '-N0', '/usr/bin/time', '-a', '-f', timeutils.TimeFmt('bigtxt'),
        '-o', baselineFile, 'src/grep', "^The", bigtxt, ':::', 'seq', '1', '50'], env=testEnv, cwd=build.pwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bigtxtTestProc.communicate()
    return ret


def grepRunTests(mutant, timeResultFile, rep, baseline):
    assert(not os.path.exists(timeResultFile))
    with open(timeResultFile, 'w+') as f:
        f.write('{0}\n'.format(','.join(timeutils.TimeColName)))

    tmout = 60 * 5
    cleanCmd = ['make', 'clean']
    for test in mutant.mutationCompilation.passedTests:
        testEnv = os.environ.copy()
        testEnv['RUN_EXPENSIVE_TESTS'] = 'yes'
        testEnv['TESTS'] = test
        testCmd = ['time', '-q', '-a', '-f', timeutils.TimeFmt(test), '-o', timeResultFile,
                'make', '-e', 'check']

        for i in range(0, rep):
            cleanProc = subprocess.Popen(cleanCmd, cwd=mutant.mutationCompilation.pwd, env=testEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cleanProc.communicate()

            testProc = subprocess.Popen(testCmd, cwd=mutant.mutationCompilation.pwd, env=testEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # timeout is ALWAYS needed for mutants default to 60 seconds
            # sometimes tests on original grep finish too fast with 0 second while mutants run into inifinite loop

            err = None
            try:
                _, err = testProc.communicate(timeout=tmout)
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                # FIXME Don't know if back slash is necessary here
                logging.warning('Timeout while running {0} with mutant '\
                        '{1} of mutation {2}'.format(test, mutant.id, mutant.mutation))
                # Reap by
                proc.cleanExpieredProcess(testProc.pid, signal.SIGKILL)
                break

    bigtxt = os.path.join(mutant.mutationCompilation.pwd, 'big.txt')
    if not os.path.exists(bigtxt):
        bigtxtDl = subprocess.Popen(['wget', 'https://norvig.com/big.txt'],
                cwd=mutant.mutationCompilation.pwd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        bigtxtDl.communicate()
        assert(bigtxtDl.returncode == 0)

    tmout = tmout * 10
    bigtxtTestProc = subprocess.Popen(['parallel', '-N0', '/usr/bin/time', '-a', '-f',
        timeutils.TimeFmt('bigtxt'), '-o', timeResultFile, 'src/grep', "^The", bigtxt, ':::',
        'seq', '1', '10'], env=testEnv, cwd=mutant.mutationCompilation.pwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _, err = bigtxtTestProc.communicate(timeout=tmout)
        if err is not None and len(err) > 0:
            print(err.decode('utf-8', 'replace'))
    except subprocess.TimeoutExpired as tmOutErr:
        # FIXME Don't know if back slash is necessary here
        logging.warning('Timeout while running {0} with mutant '\
                '{1} of mutation {2}'.format(test, mutant.id, mutant.mutation))
        # Reap by
        proc.cleanExpieredProcess(bigtxtTestProc.pid, signal.SIGKILL)

prefix = f'{os.getenv("HOME")}/slowcoach'
projectRoot = f'{prefix}/mutation-targets/grep'
grepConf = f'{prefix}/config/grep_config.xml'
workTrees = f'{projectRoot}/worktrees'
mutantsPath = os.path.join(projectRoot, 'mutants')
gnulibSrc = f'{prefix}/lib/gnulib'


def confGrep(build, confArgs, gnulibLoc=gnulibSrc):
    confEnv = os.environ.copy()
    confEnv['CC'] = 'clang'
    confEnv['CXX'] = 'clang++'
    confEnv['GNULIB_SRCDIR'] = gnulibLoc
    if not os.path.exists(os.path.join(build, 'configure')):
        bootCmd = [f'{build}/bootstrap', '--copy']
        pBoot = subprocess.Popen(bootCmd, env=confEnv, cwd=build, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        pBoot.communicate()
        assert(pBoot.returncode == 0)
    # running conf is mandatory for compilation arguments
    confCmd = [f'{build}/configure', confArgs]
    pConf = subprocess.Popen(confCmd, env=confEnv, cwd=build, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    pConf.communicate()


def buildGrep(build, buildArgs):
    assert(os.path.exists(os.path.join(build, 'configure')))
    compCmd = ['make']
    compCmd.append(buildArgs)
    pComp = subprocess.Popen(compCmd, cwd=build,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    pComp.communicate()

def cleanGrep(build):
    compCmd = ['make', 'clean']
    pComp = subprocess.Popen(compCmd, cwd=build,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    pComp.communicate()

def genWorktree(mut):
    src = mut[0]
    oprt = mut[1]
    ident = mut[2]
    wt = os.path.join(workTrees, '_'.join(mut[0:3]))
    injectSpot = os.path.join(wt, mut[3])
    worktreeExec = ['git', 'worktree', 'add']
    workTr = subprocess.Popen(worktreeExec + [wt], cwd=workTrees,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    workTr.communicate()

    gnulibLoc = os.path.join(wt, 'gnulib')
    if not os.path.exists(gnulibLoc):
        os.mkdir(gnulibLoc)
    gnulibWorktreeGen = subprocess.Popen(worktreeExec + [f'-b{os.path.basename(wt)}', gnulibLoc],
            cwd=gnulibSrc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gnulibWorktreeGen.communicate()
    wtInit = subprocess.Popen(['git', 'submodule', 'update'], cwd=wt,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wtInit.communicate()

    confGrep(wt, '', gnulibLoc)
    copy(mut[-1], injectSpot, follow_symlinks=False)
    return wt

def getInjectSpot(compDB, mut):
    n = os.path.basename(mut).split('_')
    ident, ext = os.path.splitext(n[-1])
    oprt = n[-2]
    src = '_'.join(n[0: -2])

    m = os.path.dirname(os.path.relpath(mut, mutantsPath)).split('_')
    mutRelPath = '.'.join(['_'.join(m[:-1]), m[-1]])

    for srcEntry in compDB:
        if srcEntry['file'] == mutRelPath:
            return (src, oprt, ident,
                    os.path.relpath(os.path.join(srcEntry['directory'],
                        mutRelPath), projectRoot),
                    mut)
    # Should never execute here
    assert(False)

def getPassedTests(project):
    tst = next(os.walk(os.path.join(project, 'tests')))
    assert(os.path.exists(os.path.join(project, 'src', 'grep')))
    if not os.path.exists(os.path.join(tst[0], 'test-suite.log')):
        goldrunProc = subprocess.Popen(['make', 'check-expensive'], cwd=project,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        goldrunProc.communicate()
        tst = next(os.walk(os.path.join(project, 'tests')))
    res = filter(lambda x: x.endswith('.trs'),
        map(lambda y: os.path.join(tst[0], y), tst[2]))
    for r in res:
        with open(r) as f:
            if f.readline().split(':')[-1].strip() == 'PASS':
                yield os.path.basename(r).split('.')[0]

def runTests(project, output, testList, rep):
    assert(len(testList) > 0)
    testPath = os.path.join(project, 'tests')
    if os.path.exists(output):
        return output

    tmout = 60 * 5
    with open(output, 'w+') as f:
        f.write('{0}\n'.format(','.join(timeutils.TimeColName)))
    for t in testList:
        testEnv = os.environ.copy()
        testEnv['RUN_EXPENSIVE_TESTS'] = 'yes'
        testEnv['TESTS'] = t
        testCmd = ['time', '-q', '-a', '-f', timeutils.TimeFmt(t), '-o', output,
                'make', '-e', 'check-recursive']

        for i in range(0, rep):
            tstRes = os.path.join(project, 'tests', t + '.trs')
            tstLog = os.path.join(project, 'tests', t + '.log')
            suiteLog = os.path.join(project, 'tests', 'test-suite.log')
            if os.path.exists(tstRes):
                os.remove(tstRes)
            if os.path.exists(tstLog):
                os.remove(tstLog)
            if os.path.exists(suiteLog):
                os.remove(suiteLog)
            testProc = subprocess.Popen(testCmd, cwd=project, env=testEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # timeout is ALWAYS needed for mutants default to 60 seconds
            # sometimes tests on original grep finish too fast with 0 second while mutants run into inifinite loop

            err = None
            try:
                _, err = testProc.communicate(timeout=tmout)
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                # FIXME Don't know if back slash is necessary here
                logging.warning(f'Timeout while running {t} at {project}')
                # Reap by
                proc.cleanExpieredProcess(testProc.pid, signal.SIGKILL)
                break
    return output

def getMutAttr(wt):
    for w in wt:
        t = os.path.basename(w).split('_')
        yield ('_'.join(t[0:-2]), t[-2], t[-1])

def main():
    slowcoachInst = f'{os.getenv("HOME")}/slowcoach/build/slowcoach'
    configs = os.path.join(projectRoot, 'config')
    logging.basicConfig(filename='experiment.log',
                        format='[%(asctime)s]-%(levelname)s %(message)s', level=logging.INFO)
    with open(os.path.join(projectRoot, 'compile_commands.json')) as f:
        compDB = json.load(f)
    assert(compDB is not None)
    if not os.path.exists(mutantsPath):
        with Mutate(os.path.join(projectRoot, 'compile_commands.json'),
                '10.0.1', mutantsPath, [], grepConf, slowcoachInst) as m:
            m.mutate()
    if not os.path.exists(workTrees):
        os.mkdir(workTrees)

        p = subprocess.Popen(['find', mutantsPath, '-type', 'f'],
                cwd=workTrees, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rawMutants = filter(lambda x: not x.endswith('.log') and len(x) > 0,
                p.communicate()[0].decode().split(os.linesep))
        mutants = map(partial(getInjectSpot, compDB), random.sample(list(rawMutants), k=120))
        with Pool(32) as p:
            wt = p.map(genWorktree, mutants)
    else:
        _, projs, _ = next(os.walk(workTrees))
        wt = map(lambda x: os.path.join(workTrees, x), projs)
    mut = list(getMutAttr(wt))
    # start build and experiments:
    O0_confArgs = 'CC=clang CXX=clang++ CFLAGS=-O0'
    O3_confArgs = 'CC=clang CXX=clang++ CFLAGS=-O3'
    # build baseline O0
    confGrep(projectRoot, O0_confArgs)
    buildGrep(projectRoot, '-j46')
    resPath = os.path.join(projectRoot, 'grep_performance_results')
    if not os.path.exists(resPath):
        os.mkdir(resPath)
    tst = list(getPassedTests(projectRoot))
    r = runTests(projectRoot, os.path.join(resPath, 'time_baseline_O0.csv'), tst, 10)
    # build mutants
    with Pool(46) as p:
        p.map(lambda x: confGrep(x, O0_confArgs, os.path.join(x, 'gnulib')), wt)
    with Pool(6) as p:
        p.map(lambda x: buildGrep(x, '-j8'), wt)
    with Pool(32) as p:
        p.map(lambda x: runTests(x[0], timeutils.formResultFileName(resPath, 'time',
            x[1][0], x[1][1], x[1][2], 'O0'), tst, 10), zip(wt, mut))

    # build baseline O3
    confGrep(projectRoot, O3_confArgs)
    buildGrep(projectRoot, '-j46')
    r = runTests(projectRoot, os.path.join(resPath, 'time_baseline_O3.csv'), tst, 10)
    # build mutants
    with Pool(46) as p:
      p.map(lambda x: confGrep(x, O3_confArgs, os.path.join(x, 'gnulib')), wt)
    with Pool(6) as p:
        p.map(lambda x: buildGrep(x, '-j8'), wt)
    with Pool(32) as p:
        p.map(lambda x: runTests(x[0], timeutils.formResultFileName(resPath, 'time',
            x[1][0], x[1][1], x[1][2], 'O3'), tst, 10), zip(wt, mut))

if __name__ == '__main__':
    main()
