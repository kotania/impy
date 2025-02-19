from __future__ import print_function

import sys
import os
import numpy as np
from multiprocessing import Pool, freeze_support
import tempfile
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.append(os.path.join(root_dir, '../../apps/pythia8240/lib'))

from impy.definitions import *
from impy.constants import *
from impy.kinematics import EventKinematics
from impy import impy_config, pdata
from impy.util import info

gen_list = [
    'SIBYLL23D',
    'SIBYLL23C',
    'SIBYLL23C01',
    'SIBYLL23C00', 
    'SIBYLL23', 
    'SIBYLL21', 
    'DPMJETIII306', 
    'DPMJETIII191', 
    'EPOSLHC',
    'PHOJET112',
    'PHOJET191',
    'URQMD34',
    # 'PYTHIA8',
    'QGSJET01C',
    'QGSJETII03',
    'QGSJETII04'
]


def run_generator(gen,*args):
    event_kinematics = EventKinematics(ecm=7000 * GeV,
                                    p1pdg=2212,
                                    p2pdg=2212
                                    # nuc2_prop=(14,7)
                                    )

    impy_config["user_frame"] = 'center-of-mass'


    eta_bins = np.linspace(-5,5,21)
    eta_widths = eta_bins[1:] - eta_bins[:-1]
    eta_centers = 0.5*(eta_bins[1:] + eta_bins[:-1])
    nevents = 5000
    norm = 1./float(nevents)/eta_widths
    print('Testing',gen)
    hist = np.zeros(len(eta_centers)) 
    try:
        log = tempfile.mkstemp()[1]
        generator = make_generator_instance(interaction_model_by_tag[gen])
        generator.init_generator(event_kinematics,logfname=log)
        for event in generator.event_generator(event_kinematics, nevents):
            event.filter_final_state_charged()
            hist += norm*np.histogram(event.eta,bins=eta_bins)[0]
        return True, gen, log, eta_bins, hist
    except:
        return False, gen, log, eta_bins, hist

# import IPython
# IPython.embed()
if __name__ in ['__main__', '__test__']:
    freeze_support()
    pool = Pool(processes=32)
    result = [pool.apply_async(run_generator, (gen,)) for gen in gen_list]
    result = [res.get(timeout=1000) for res in result]

    failed = []
    passed = []
    psrap = {}
    logs = {}

    eta_bins = result[0][3]

    for r, gen, log, _, hist in result:
        if r:
            passed.append(gen)
            psrap[gen] = hist
        else:
            failed.append(gen)
            
        with open(log) as f:
                logs[gen] = f.read()
            
    info(0, 'Test results for 7 TeV pp collisions in cms frame:\n')
    info(0, 'Passed:', '\n', '\n '.join(passed))
    info(0, '\nFailed:', '\n', '\n '.join(failed))

    import pickle
    pickle.dump((eta_bins, psrap, logs),
                open(os.path.splitext(__file__)[0] + '.pkl','wb'), protocol=-1)