import subprocess
import os
import signal
import proc

class FuncRun:
    def __init__(self, mut, dump):
        self.mut = mut
        if dump is not None:
            self.out = dump[0]
            self.err = dump[1]
        else:
            self.out = None
            self.err = None

def runBench(cmdname, wd, exe, arg):
    cmd = [exe]
    ret = None
    if type(arg) is list:
        for a in arg:
            cmd.append(a)
    else:
        cmd.append(arg)

    try:
        exprProc = subprocess.Popen(cmd, cwd=wd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = exprProc.communicate(timeout=60*30)
    except subprocess.TimeoutExpired as tmOutErr:
        proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
        print(tmOutErr)
        ret = None
    return ret

def astarBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test-lake', os.path.join(projRoot, 'data', 'test', 'input'), exe, 'lake.cfg'))
    yield FuncRun(mut, runBench('ref-biglake', os.path.join(projRoot, 'data', 'ref', 'input'), exe,
        'BigLakes2048.cfg'))
    yield FuncRun(mut, runBench('ref-rivers', os.path.join(projRoot, 'data', 'ref', 'input'), exe,
        'rivers.cfg'))
    yield FuncRun(mut, runBench('train-biglake', os.path.join(projRoot, 'data', 'train', 'input'), exe,
        'BigLakes1024.cfg'))
    yield FuncRun(mut, runBench('train-rivers', os.path.join(projRoot, 'data', 'train', 'input'), exe,
        'rivers1.cfg'))


def bzip2Bench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe, 'control'))
    yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'control'))
    yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe, 'control'))


def gobmkBench(projRoot, exe, mut):
    dataDir = os.path.join(projRoot, 'data')
    testWl = os.path.join(projRoot, 'data', 'test', 'input')
    refWl = os.path.join(projRoot, 'data', 'ref', 'input')
    trainWl = os.path.join(projRoot, 'data', 'train', 'input')
    testinputs = map(lambda x: os.path.join(testWl, x),
            ['capture.tst', 'connect.tst', 'connect_rot.tst', 'connection.tst', 'connection_rot.tst',
            'cutstone.tst', 'dniwog.tst'])
    refinputs = map(lambda x: os.path.join(refWl, x),
            ['13x13.tst', 'nngs.tst', 'score2.tst', 'trevorc.tst', 'trevord.tst'])
    traininputs = map(lambda x: os.path.join(trainWl, x),
            ['arb.tst', 'arend.tst', 'arion.tst', 'atari_atari.tst', 'blunder.tst', 'buzco.tst', 'nicklas2.tst',
                'nicklas4.tst'])
    cmd = [exe, '--mode', 'gtp']
    for inp in testinputs:
        ret = FuncRun(mut, None)
        try:
            with open(inp) as inf:
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                ret = FuncRun(mut, exprProc.communicate(timeout=60*30))
        except subprocess.TimeoutExpired as tmOutErr:
            proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
            print(tmOutErr)
            ret = FuncRun(mut, None)
        yield ret
    for inp in refinputs:
        ret = FuncRun(mut, None)
        try:
            with open(inp) as inf:
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                ret = FuncRun(mut, exprProc.communicate(timeout=60*30))
        except subprocess.TimeoutExpired as tmOutErr:
            proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
            print(tmOutErr)
            ret = FuncRun(mut, None)
        yield ret
    for inp in traininputs:
        ret = FuncRun(mut, None)
        try:
            with open(inp) as inf:
                exprProc = subprocess.Popen(cmd, cwd=os.path.join(dataDir, 'all', 'input'),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inf)
                yield FuncRun(mut, exprProc.communicate(timeout=60*30))
        except subprocess.TimeoutExpired as tmOutErr:
            proc.cleanExpieredProcess(exprProc.pid, signal.SIGKILL)
            print(tmOutErr)
            ret = FuncRun(mut, None)
        yield ret

def h264refBench(projRoot, exe, mut):
    dataDir = os.path.join(projRoot, 'data')
    testWl = os.path.join(projRoot, 'data', 'test', 'input')
    refWl = os.path.join(projRoot, 'data', 'ref', 'input')
    trainWl = os.path.join(projRoot, 'data', 'train', 'input')
    yield FuncRun(mut, runBench('test-foreman-test-encoder-baseline', os.path.join(dataDir, 'all', 'input'), exe,
            ['-d', os.path.join(testWl, 'foreman_test_encoder_baseline.cfg')]))
    refinputs = ['foreman_ref_encoder_baseline.cfg', 'foreman_ref_encoder_main.cfg', 'sss_encoder_main.cfg']
    yield FuncRun(mut, runBench('ref-foreman_ref_encoder_baseline',
            os.path.join(dataDir, 'all', 'input'), exe,
            ['-d', os.path.join(refWl, 'foreman_ref_encoder_baseline.cfg')]))
    yield FuncRun(mut, runBench('ref-foreman_ref_encoder_main',
             os.path.join(dataDir, 'all', 'input'), exe,
            ['-d', os.path.join(refWl, 'foreman_ref_encoder_main.cfg')]))
    yield FuncRun(mut, runBench('ref-sss_encoder_main', os.path.join(dataDir, 'all', 'input'), exe,
            ['-d', os.path.join(refWl, 'sss_encoder_main.cfg')]))
    yield FuncRun(mut, runBench('train-foreman-train-encoder-baseline',
            os.path.join(dataDir, 'all', 'input'), exe,
            ['-d', os.path.join(trainWl, 'foreman_train_encoder_baseline.cfg')]))

def hmmerBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test-bombesin', os.path.join(projRoot, 'data', 'test', 'input'), exe,
        'bombesin.hmm'))
    yield FuncRun(mut, runBench('ref-nph3', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'nph3.hmm'))
    yield FuncRun(mut, runBench('ref-retro', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'retro.hmm'))
    yield FuncRun(mut, runBench('train-leng100', os.path.join(projRoot, 'data', 'train', 'input'), exe,
        'leng100.hmm'))

def libquantumBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe, '33 5'))
    yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe, '1397 8'))
    yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe, '143 25'))

def mcfBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe, 'inp.in'))
    yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'inp.in'))
    yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe, 'inp.in'))

def omnetppBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe, 'omnetpp.ini'))
    yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'omnetpp.ini'))
    yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe, 'omnetpp.ini'))

def sjengBench(projRoot, exe, mut):
   yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe, 'test.txt'))
   yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe, 'ref.txt'))
   yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe, 'train.txt'))

def xalancbmkBench(projRoot, exe, mut):
    yield FuncRun(mut, runBench('test', os.path.join(projRoot, 'data', 'test', 'input'), exe,
        ['test.xml', 'xalanc.xsl']))
    yield FuncRun(mut, runBench('ref', os.path.join(projRoot, 'data', 'ref', 'input'), exe,
        ['t5.xml', 'xalanc.xsl']))
    yield FuncRun(mut, runBench('train', os.path.join(projRoot, 'data', 'train', 'input'), exe,
        ['allbooks.xml', 'xalanc.xsl']))
