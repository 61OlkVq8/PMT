import subprocess
import os
import subprocess
import proc
import timeutils
import name
import signal
from functools import reduce


rep = 30
# Maximal 10 mins of execution for each test
tmout = 60 * 30


class SpecExperiment:
    def __init__(self, exe, worktree, resultDir, dataDir, opt, isOrig=False):
        self.worktree = worktree
        self.exe = exe
        self.resultDir = resultDir
        self.dataDir = dataDir
        self.testWl = os.path.join(dataDir, 'test', 'input')
        self.refWl = os.path.join(dataDir, 'ref', 'input')
        self.trainWl = os.path.join(dataDir, 'train', 'input')
        self.isOrig = isOrig
        self.cmd = lambda cmdName, resFile: ['time', '-q', '-a', '-f', timeutils.TimeFmt(cmdName), '-o', resFile,
                os.path.join(self.worktree, self.exe)]
        self.opt = opt
        if not os.path.exists(os.path.join(worktree, exe)):
            buildMut = subprocess.Popen(['make', '-j', '4'], cwd=worktree,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = buildMut.communicate()
            # if buildMut.returncode != 0:
            #     print(worktree)
            #     print(err.decode())

    def isReady(self):
        return os.path.exists(os.path.join(self.worktree, self.exe))

    def timeResultFile(self, profile):
        if self.isOrig:
            ret = os.path.join(self.resultDir, 'time_baseline_{}.csv'.format(self.opt))
            if not os.path.exists(ret):
                with open(ret, 'w') as f:
                    f.write(','.join(timeutils.TimeColName))
                    f.write('\n')
            return ret
        wt = os.path.basename(self.worktree).split('_')
        assert(len(wt) >= 4)
        if len(wt) == 4:
            ret = timeutils.formResultFileName(self.resultDir, profile, wt[1], wt[2], wt[3], self.opt)
        else:
            ret = timeutils.formResultFileName(self.resultDir, profile, '_'.join(wt[1:-2]), wt[-2],
                    wt[-1], self.opt)
        if not os.path.exists(ret):
            with open(ret, 'w') as f:
                f.write(','.join(timeutils.TimeColName))
        return ret

    def runExperiment(self, cmdname, wd, arg):
        cmd = self.cmd(cmdname, self.timeResultFile('time')).copy()
        if type(arg) is list:
            for a in arg:
                cmd.append(a)
        else:
            cmd.append(arg)
        for i in range(0, rep):
            exprProc = subprocess.Popen(cmd, cwd=wd,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                _, err = exprProc.communicate(timeout=tmout)
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                print(self.worktree)
                print(tmOutErr)
                break


def astarExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test-lake', experiment.testWl, 'lake.cfg')
    experiment.runExperiment('ref-biglake', experiment.refWl, 'BigLakes2048.cfg')
    experiment.runExperiment('ref-rivers', experiment.refWl, 'rivers.cfg')
    experiment.runExperiment('train-biglake', experiment.trainWl, 'BigLakes1024.cfg')
    experiment.runExperiment('train-rivers', experiment.trainWl, 'rivers1.cfg')


def bzip2Experiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, 'control')
    experiment.runExperiment('ref', experiment.refWl, 'control')
    experiment.runExperiment('train', experiment.trainWl, 'control')


def gobmkExperiment(experiment):
    if not experiment.isReady():
        return
    testinputs = map(lambda x: os.path.join(experiment.testWl, x),
            ['capture.tst', 'connect.tst', 'connect_rot.tst', 'connection.tst', 'connection_rot.tst',
            'cutstone.tst', 'dniwog.tst'])
    refinputs = map(lambda x: os.path.join(experiment.refWl, x),
            ['13x13.tst', 'nngs.tst', 'score2.tst', 'trevorc.tst', 'trevord.tst'])
    traininputs = map(lambda x: os.path.join(experiment.trainWl, x),
            ['arb.tst', 'arend.tst', 'arion.tst', 'atari_atari.tst', 'blunder.tst', 'buzco.tst', 'nicklas2.tst',
                'nicklas4.tst'])
    # FIXME inp.split is buggy. It captures the first portion of the absolute path
    # Should be os.path.basename(inp).split()
    for inp in testinputs:
        cmd = experiment.cmd(f"test-{os.path.basename(inp).split('.')[0]}",
                experiment.timeResultFile('time')).copy()
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            for i in range(0, rep):
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                try:
                    _, err = exprProc.communicate(timeout=tmout)
                    if err is not None and len(err) > 0:
                        print(err.decode('utf-8', 'replace'))
                except subprocess.TimeoutExpired as tmOutErr:
                    proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                    print(experiment.worktree)
                    print(tmOutErr)
                    break
    for inp in refinputs:
        cmd = experiment.cmd(f"ref-{os.path.basename(inp).split('.')[0]}",
                experiment.timeResultFile('time')).copy()
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            for i in range(0, rep):
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                try:
                    _, err = exprProc.communicate(timeout=tmout)
                    if err is not None and len(err) > 0:
                        print(err.decode('utf-8', 'replace'))
                except subprocess.TimeoutExpired as tmOutErr:
                    proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                    print(experiment.worktree)
                    print(tmOutErr)
                    break
    for inp in traininputs:
        cmd = experiment.cmd(f"train-{os.path.basename(inp).split('.')[0]}",
                experiment.timeResultFile('time')).copy()
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            for i in range(0, rep):
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                try:
                    _, err = exprProc .communicate(timeout=tmout)
                    if err is not None and len(err) > 0:
                        print(err.decode('utf-8', 'replace'))
                except subprocess.TimeoutExpired as tmOutErr:
                    proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                    print(experiment.worktree)
                    print(tmOutErr)
                    break

def h264refExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test-foreman-test-encoder-baseline', os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.testWl, 'foreman_test_encoder_baseline.cfg')])
    refinputs = ['foreman_ref_encoder_baseline.cfg', 'foreman_ref_encoder_main.cfg', 'sss_encoder_main.cfg']
    experiment.runExperiment('ref-foreman_ref_encoder_baseline',
            os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.refWl, 'foreman_ref_encoder_baseline.cfg')])
    experiment.runExperiment('ref-foreman_ref_encoder_main',
             os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.refWl, 'foreman_ref_encoder_main.cfg')])
    experiment.runExperiment('ref-sss_encoder_main', experiment.refWl,
            ['-d', os.path.join(experiment.refWl, 'sss_encoder_main.cfg')])
    experiment.runExperiment('train-foreman-train-encoder-baseline',
            os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.trainWl, 'foreman_train_encoder_baseline.cfg')])

def hmmerExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test-bombesin', experiment.testWl, 'bombesin.hmm')
    experiment.runExperiment('ref-nph3', experiment.refWl, 'nph3.hmm')
    experiment.runExperiment('ref-retro', experiment.refWl, 'retro.hmm')
    experiment.runExperiment('train-leng100', experiment.trainWl, 'leng100.hmm')

def libquantumExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, '33 5')
    experiment.runExperiment('ref', experiment.refWl, '1397 8')
    experiment.runExperiment('train', experiment.refWl, '143 25')

def mcfExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, 'inp.in')
    experiment.runExperiment('ref', experiment.refWl, 'inp.in')
    experiment.runExperiment('train', experiment.trainWl, 'inp.in')

def omnetppExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, 'omnetpp.ini')
    experiment.runExperiment('ref', experiment.refWl, 'omnetpp.ini')
    experiment.runExperiment('train', experiment.trainWl, 'omnetpp.ini')

def sjengExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, 'test.txt')
    experiment.runExperiment('ref', experiment.refWl, 'ref.txt')
    experiment.runExperiment('train', experiment.trainWl, 'train.txt')

def xalancbmkExperiment(experiment):
    if not experiment.isReady():
        return
    experiment.runExperiment('test', experiment.testWl, ['test.xml', 'xalanc.xsl'])
    experiment.runExperiment('ref', experiment.refWl, ['t5.xml', 'xalanc.xsl'])
    experiment.runExperiment('train', experiment.trainWl, ['allbooks.xml', 'xalanc.xsl'])
