import subprocess
import os
import subprocess
import proc
import timeutils
import name
import signal
from functools import reduce



class SpecCov:
    def __init__(self, exe, worktree, resultDir, dataDir, opt, isOrig=False):
        self.worktree = worktree
        self.exe = exe
        self.resultDir = resultDir
        self.dataDir = dataDir
        self.testWl = os.path.join(dataDir, 'test', 'input')
        self.refWl = os.path.join(dataDir, 'ref', 'input')
        self.trainWl = os.path.join(dataDir, 'train', 'input')
        self.isOrig = isOrig
        self.opt = opt
        if not os.path.exists(os.path.join(worktree, exe)):
            buildMut = subprocess.Popen(['make', '-j', '4'], cwd=worktree,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = buildMut.communicate()
            # if buildMut.returncode != 0:
            #     print(worktree)
            #     print(err.decode())

    # FIXME argument of opt is useless
    def formProfName(self, prefix, opt, wl):
        return os.path.expanduser(os.path.join(self.resultDir, f'{wl}_{self.opt}.profraw'))

    def covRun(self, cmdName, wd, arg, profName):
        profFileName = self.formProfName(self.resultDir, 'O0', profName)
        if os.path.exists(profFileName):
            return profFileName

        cmd = [os.path.join(self.worktree, self.exe)]
        if type(arg) is list:
            for a in arg:
                cmd.append(a)
        else:
            cmd.append(arg)
        covEnv = os.environ.copy()
        covEnv['LLVM_PROFILE_FILE'] = profFileName
        exprProc = subprocess.Popen(cmd, cwd=wd, env=covEnv,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        _, err = exprProc .communicate()
        if err is not None and len(err) > 0:
            print(err.decode('utf-8', 'replace'))
        return profFileName 


def astarCov(experiment):
    return [experiment.covRun('test-lake', experiment.testWl, 'lake.cfg', 'test_lake'),
            experiment.covRun('ref-biglake', experiment.refWl, 'BigLakes2048.cfg', 'ref_BigLakes2048'),
            experiment.covRun('ref-rivers', experiment.refWl, 'rivers.cfg', 'ref_rivers'),
            experiment.covRun('train-biglake', experiment.trainWl, 'BigLakes1024.cfg', 'train_BigLakes1024'),
            experiment.covRun('train-rivers', experiment.trainWl, 'rivers1.cfg', 'train_rivers1')
            ]


def bzip2Cov(experiment):
    return [experiment.covRun('test', experiment.testWl, 'control', 'test'),
            experiment.covRun('ref', experiment.refWl, 'control', 'ref'),
            experiment.covRun('train', experiment.trainWl, 'control', 'train')
            ]


def gobmkCov(experiment):
    testinputs = map(lambda x: os.path.join(experiment.testWl, x),
            ['capture.tst', 'connect.tst', 'connect_rot.tst', 'connection.tst', 'connection_rot.tst',
            'cutstone.tst', 'dniwog.tst'])
    refinputs = map(lambda x: os.path.join(experiment.refWl, x),
            ['13x13.tst', 'nngs.tst', 'score2.tst', 'trevorc.tst', 'trevord.tst'])
    traininputs = map(lambda x: os.path.join(experiment.trainWl, x),
            ['arb.tst', 'arend.tst', 'arion.tst', 'atari_atari.tst', 'blunder.tst', 'buzco.tst', 'nicklas2.tst',
                'nicklas4.tst'])
    ret = list()
    for inp in testinputs:
        profFileName = experiment.formProfName(experiment.resultDir, 'O0',
                f'test_{os.path.basename(inp).split(".")[0]}')
        # Stop if raw prof file exists
        if os.path.exists(profFileName):
            ret.append(profFileName)
            continue
        covEnv = os.environ.copy()
        covEnv['LLVM_PROFILE_FILE'] = profFileName
        cmd = [os.path.join(experiment.worktree, experiment.exe)]
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'), env=covEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
            try:
                _, err = exprProc.communicate()
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                print(experiment.worktree)
                print(tmOutErr)
                break
        ret.append(profFileName)

    for inp in refinputs:
        profFileName = experiment.formProfName(experiment.resultDir, 'O0',
                f'ref_{os.path.basename(inp).split(".")[0]}')
        if os.path.exists(profFileName):
            ret.append(profFileName)
            continue

        covEnv = os.environ.copy()
        covEnv['LLVM_PROFILE_FILE'] = profFileName
        cmd = [os.path.join(experiment.worktree, experiment.exe)]
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'), env=covEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
            try:
                _, err = exprProc.communicate()
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                print(experiment.worktree)
                print(tmOutErr)
                break
        ret.append(profFileName)

    for inp in traininputs:
        profFileName = experiment.formProfName(experiment.resultDir, 'O0',
                f'ref_{os.path.basename(inp).split(".")[0]}')
        if os.path.exists(profFileName):
            ret.append(profFileName)
            continue

        covEnv = os.environ.copy()
        covEnv['LLVM_PROFILE_FILE'] = profFileName
        cmd = [os.path.join(experiment.worktree, experiment.exe)]
        cmd += ['--mode', 'gtp']
        with open(inp) as inf:
            exprProc = subprocess.Popen(cmd, cwd=os.path.join(experiment.dataDir, 'all', 'input'), env=covEnv,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
            try:
                _, err = exprProc .communicate()
                if err is not None and len(err) > 0:
                    print(err.decode('utf-8', 'replace'))
            except subprocess.TimeoutExpired as tmOutErr:
                proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
                print(experiment.worktree)
                print(tmOutErr)
                break
        ret.append(profFileName)

    return ret

def h264refCov(experiment):
    # refinputs = ['foreman_ref_encoder_baseline.cfg', 'foreman_ref_encoder_main.cfg', 'sss_encoder_main.cfg']
    return [experiment.covRun('test-foreman-test-encoder-baseline', os.path.join(experiment.dataDir, 'all', 'input'),
        ['-d', os.path.join(experiment.testWl, 'foreman_test_encoder_baseline.cfg')], 'test_foreman'),
        experiment.covRun('ref-foreman_ref_encoder_baseline',
            os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.refWl, 'foreman_ref_encoder_baseline.cfg')], 'ref_foreman_baseline'),
        experiment.covRun('ref-foreman_ref_encoder_main',
            os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.refWl, 'foreman_ref_encoder_main.cfg')], 'ref_foreman_main'),
        experiment.covRun('ref-sss_encoder_main', experiment.refWl,
            ['-d', os.path.join(experiment.refWl, 'sss_encoder_main.cfg')], 'ref_sss'),
        experiment.covRun('train-foreman-train-encoder-baseline',
            os.path.join(experiment.dataDir, 'all', 'input'),
            ['-d', os.path.join(experiment.trainWl, 'foreman_train_encoder_baseline.cfg')], 'train_foreman')
        ]

def hmmerCov(experiment):
    return [experiment.covRun('test-bombesin', experiment.testWl, 'bombesin.hmm', 'test_bombesin'),
            experiment.covRun('ref-nph3', experiment.refWl, 'nph3.hmm', 'ref_nph3'),
            experiment.covRun('ref-retro', experiment.refWl, 'retro.hmm', 'ref_retro'),
            experiment.covRun('train-leng100', experiment.trainWl, 'leng100.hmm', 'train_leng100')
            ]

def libquantumCov(experiment):
    return [experiment.covRun('test', experiment.testWl, '33 5', 'test'),
            experiment.covRun('ref', experiment.refWl, '1397 8', 'ref'),
            experiment.covRun('train', experiment.refWl, '143 25', 'train')
            ]

def mcfCov(experiment):
    return [experiment.covRun('test', experiment.testWl, 'inp.in', 'test'),
            experiment.covRun('ref', experiment.refWl, 'inp.in', 'ref'),
            experiment.covRun('train', experiment.trainWl, 'inp.in', 'train')
            ]

def omnetppCov(experiment):
    return [experiment.covRun('test', experiment.testWl, 'omnetpp.ini', 'test'),
            experiment.covRun('ref', experiment.refWl, 'omnetpp.ini', 'ref'),
            experiment.covRun('train', experiment.trainWl, 'omnetpp.ini', 'train')
            ]

def sjengCov(experiment):
    return [experiment.covRun('test', experiment.testWl, 'test.txt', 'test'),
            experiment.covRun('ref', experiment.refWl, 'ref.txt', 'ref'),
            experiment.covRun('train', experiment.trainWl, 'train.txt', 'train')
            ]

def xalancbmkCov(experiment):
    return [experiment.covRun('test', experiment.testWl, ['test.xml', 'xalanc.xsl'], 'test'),
            experiment.covRun('ref', experiment.refWl, ['t5.xml', 'xalanc.xsl'], 'ref'),
            experiment.covRun('train', experiment.trainWl, ['allbooks.xml', 'xalanc.xsl'], 'train')
            ]
