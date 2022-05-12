import pandas as pd
import timeutils as tmu
import os


def fetchTimeResults(resDir):
    assert(os.path.exists(resDir) and os.path.isdir(resDir))
    prefix, _, res = next(os.walk(resDir))
    baselineFile = 'time_baseline.csv'
    assert(baselineFile in res)
    res.remove(baselineFile)
    return os.path.join(prefix, baselineFile), list(map(lambda x: os.path.join(prefix, x), res))


def timeAnalyze(baseFile, resFiles):
    baseline = pd.read_csv(baseFile, names=tmu.TimeColName)
    execTimeBase = baseline.groupby(['cmd'])['wall_clk_sec'].median()
    assert(baseFile not in resFiles)
    for r in resFiles:
        mutRes = pd.read_csv(r, names=tmu.TimeColName)
        mutTime = baseline.groupby(['cmd'])['wall_clk_sec'].median()
        for cmd, wallTime in mutTime.items():
            if execTimeBase[execTimeBase.index==cmd].values[0] < wallTime:
                print('{1} is slower than baseline while running {0}'.format(cmd, os.path.basename(r).split('_')[2]))

def main():
    baseline, res = fetchTimeResults('/home/chen/slowcoach/mutation-targets/grep/time_results')
    timeAnalyze(baseline, res)


if __name__ == '__main__':
    main()
