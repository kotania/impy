import sys
import os
from impy.constants import GeV
from impy.kinematics import EventKinematics
from impy import impy_config
from impy.models import DpmjetIII191
from collections import Counter

# This class will go through the event and decay all particles that should be
# unstable but did not decay in some other generator


# FIXME this should not be defined in a test
# if it works, it should be part of the library and tested here
class Pythia8DecayAfterburner(object):
    def __init__(self, stable_list):
        self.stable_list = stable_list
        self._init_pythia()

    def _init_pythia(self):
        # FIXME Anatoly test cannot contain special paths
        pythia_dir = os.path.join(
            os.path.expanduser("~"), "devel", "apps", "pythia8240"
        )
        sys.path.append(os.path.join(pythia_dir, "lib"))
        import pythia8

        self.pythia = pythia8.Pythia()
        self.pythia.readString("ProcessLevel:all = off")
        self.pythia.readString("ParticleDecays:tau0Max = 1e100")
        # Set muons unstable
        self.pythia.particleData.mayDecay(13, True)
        self.pythia.init()

    def __call__(self, event):
        nappend = 0
        p_ids, status, px, py, pz, en, m = [], [], [], [], [], [], []

        for ip in range(event.npart):
            if event.status[ip] != 1 or abs(event.p_ids[ip]) in self.stable_list:
                continue

            # Set particle to not final and simulate decay
            event.status[ip] = 2
            self.pythia.event.reset()
            # put decaying particle
            self.pythia.event.append(
                int(event.p_ids[ip]),
                91,
                0,
                0,
                event.px[ip],
                event.py[ip],
                event.pz[ip],
                event.en[ip],
                event.m[ip],
            )
            self.pythia.particleData.mayDecay(int(event.p_ids[ip]), True)
            # Decay it
            self.pythia.forceHadronLevel()
            for p in self.pythia.event:
                if not p.isFinal():
                    continue
                p_ids.append(p.id())
                status.append(1)
                px.append(p.px())
                py.append(p.py())
                pz.append(p.pz())
                en.append(p.e())
                m.append(p.m())
                nappend += 1

        append = slice(event.npart, event.npart + nappend)

        event.en[append] = en
        event.p_ids[append] = p_ids
        event.status[append] = status
        event.px[append] = px
        event.py[append] = py
        event.pz[append] = pz
        event.m[append] = m

        event.npart = nappend
        event.selection = slice(None, event.npart)
        event._apply_slicing()


def test_decay_afterburner():
    event_kinematics = EventKinematics(
        ecm=200 * GeV,
        p1pdg=2212,
        p2pdg=2212
        # nuc2_prop=(14,7)
    )

    # Watch out this setting!
    impy_config["pre_slice"] = False

    # The rest is pretty standard
    generator = DpmjetIII191(event_kinematics)

    # Here provide the list of particles which you want to retain as stable
    pythia_afterburner = Pythia8DecayAfterburner(
        stable_list=[2212, 11, 12, 14, 15, 16, 22]
    )

    before = Counter()
    after = Counter()
    for event in generator(200):
        before.update(event.p_ids)
        # This has to be the first call after an event is generated. The event object
        # will be modified and finalized by this call
        pythia_afterburner(event)
        # Here filter only the particles that are remaining as stable
        event.filter_final_state()
        # Enjoy the result
        after.update(event.p_ids)
    assert len(after) < len(before)
    # TODO check list of specific particles that are expected to
    # be decayed by Pythia but not Dpmjet
