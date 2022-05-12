import os
import pandas as pd
import re

TimeFmt = lambda x: '{0},%D,%E,%F,%I,%K,%M,%O,%P,%R,%S,%U,%W,%X,%Z,%c,%e,%k,%p,%r,%s,%t,%w,%x'.format(x)
TimeColName = ['cmd', 'unshared_data_size', 'wall_clk', 'major_pg_faults', 'file_input_num',
               'avg_mem_use', 'max_proc_size', 'file_output_num', 'cpu_pct', 'minor_pg_faults',
               'kernel_cpu_time', 'user_cpu_time', 'swp_num', 'avg_shared_text_size', 'pg_size',
               'cxt_switch_num', 'wall_clk_sec', 'signal_num', 'avg_unshared_stack_size',
               'socket_rcv_msg_num', 'socket_send_msg_num', 'avg_proc_size', 'cxt_yield_num', 'exit']
TimeFileMatcher = re.compile(r'^(?P<profiler>.+)\_(?P<src>.+)\_(?P<mut>\w+)\_(?P<id>\d+).csv')

def loadTimeResult(timeResult):
    assert(os.path.exists(timeResult))
    return pd.read_csv(timeResult, names=TimeColName)

def formResultFileName(prefix, profileName, source, mutator, ident, opt):
    return os.path.join(prefix, '{0}_{1}_{2}_{3}_{4}.csv'.format(profileName, source, mutator, ident, opt))
