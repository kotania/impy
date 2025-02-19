'''
Created on 17.03.2014

@author: afedynitch
'''

import numpy as np
from impy.common import standard_particles


class SophiaCascadeRun():
    def __init__(self,
                 lib_str,
                 label,
                 decay_mode,
                 n_events,
                 fill_subset=False,
                 p_debug=False,
                 nucleon_Ekin=None):
        from ParticleDataTool import SibyllParticleTable
        exec("import " + lib_str + " as siblib")
        self.lib = siblib  # @UndefinedVariable
        self.label = label
        self.nEvents = n_events
        self.fill_subset = fill_subset
        self.spectrum_hists = []
        self.dbg = p_debug
        self.nucleon_Ekin = nucleon_Ekin
        set_stable(self.lib, decay_mode, self.dbg)
        self.ptab = SibyllParticleTable()
        self.init_generator()

    def init_generator(self):
        from random import randint
        seed = randint(1000000, 10000000)
        print(self.__class__.__name__ + '::init_generator(): seed=', seed)
        self.lib.init_rmmard(seed)

    def get_hadron_air_cs(self, E_lab, projectile_sibid):
        raise Exception('Not implemented, yet')

    def start(self, evkin):

        swap = False
        nucleon_id = None
        nucleon_mass = None
        if evkin.p1pdg == 22 and evkin.p2pdg in [2212, 2112]:
            swap = True
            nucleon_id = self.ptab.pdg2modid[evkin.p2pdg]
            nucleon_mass = evkin.pmass2
        elif evkin.p2pdg == 22 and evkin.p1pdg in [2212, 2112]:
            swap = False
            nucleon_id = self.ptab.pdg2modid[evkin.p1pdg]
            nucleon_mass = evkin.pmass1

        swap = False
        nucleon_e = nucleon_mass + self.nucleon_Ekin

        hist_d = {}
        for hist in self.spectrum_hists:
            hist_d[hist.particle_id] = hist
        ngenerated = self.nEvents

        for i in range(self.nEvents):
            self.lib.eventgen(nucleon_id, nucleon_e, evkin.elab, 180., 0)
            if not (i % 10000) and i and self.dbg:
                print(i, "events generated.")

            event = SophiaCascadeEvent(self.lib, swap)

            unique_pids = np.unique(event.p_ids)
            if 0 in unique_pids:
                self.lib.sib_list(6)
                ngenerated = ngenerated - 1
                continue
            if not self.fill_subset:
                [hist_d[pid].fill_event(event) for pid in unique_pids]
            else:
                for pid in unique_pids:
                    if pid in list(hist_d.keys()):
                        hist_d[pid].fill_event(event)
        # Correct for selective filling of histograms
        for hist in self.spectrum_hists:
            hist.n_events_filled = ngenerated


class SophiaCascadeEvent():
    def __init__(self, lib, swap=False):
        npart = lib.s_plist.np
        stable = np.nonzero(np.abs(lib.s_plist.llist[:npart]) < 10000)[0]

        self.p_ids = lib.s_plist.llist[:npart][stable]
        self.E = lib.s_plist.p[:npart, 3][stable]
        if swap:
            self.pz = -lib.s_plist.p[:npart, 2][stable]
        else:
            self.pz = lib.s_plist.p[:npart, 2][stable]


#=========================================================================
# set_stable
#=========================================================================
def set_stable(lib, decay_mode, dbg=True):
    idb = lib.s_csydec.idb

    if dbg:
        print("SophiaCascadeRun::set_stable(): Setting standard" +
              " particles stable.")

    #fast-mode particles
    if decay_mode == 0:
        stab = SibyllParticleTable()
        for pdg_id in standard_particles:
            print('stable,', pdg_id)
            idb[i - 1] = -np.abs(idb[i - 1])
        return

    # keep muons pions, kaons
    for i in range(4, 5 + 1):
        idb[i - 1] = -np.abs(idb[i - 1])
    for i in range(7, 18 + 1):
        idb[i - 1] = -np.abs(idb[i - 1])
    # K0 and K0-bar have to remain unstable to form K0S/L

    if decay_mode <= 1:
        return

    # Decay mode 2 for generation of decay spectra (all conventional with
    # lifetime >= K0S
    if dbg:
        print("SophiaCascadeRun::set_stable(): Setting conventional " +
              "Sigma-, Xi0, Xi- and Lambda0 stable (decay mode).")
    for i in range(36, 39 + 1):
        idb[i - 1] = -np.abs(idb[i - 1])

    if decay_mode <= 2:
        return

    # Conventional mesons and baryons
    # keep eta, eta', rho's, omega, phi, K*
    if dbg:
        print("SophiaCascadeRun::set_stable(): Setting all " +
              "conventional stable.")
    # pi0
    idb[6 - 1] = -np.abs(idb[6 - 1])
    for i in range(23, 33 + 1):
        idb[i - 1] = -np.abs(idb[i - 1])

    # keep SIGMA, XI, LAMBDA
    for i in range(34, 49 + 1):
        idb[i - 1] = -np.abs(idb[i - 1])

    if decay_mode <= 3:
        return

    # Charmed particles (only for version >= 2.2)
    # keep all charmed
    if dbg:
        print("SophiaCascadeRun::set_stable(): Setting all " +
              "conventional and charmed stable.")
    for i in list(range(59, 61)) + list(range(71, 99 + 1)):
        idb[i - 1] = -np.abs(idb[i - 1])
