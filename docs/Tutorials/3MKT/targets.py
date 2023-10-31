import verification_tools as vt

from passengersim import Config


def load(experiment_n: int, config: Config):
    files = {
        1: "./pods-outputs/ZF2-1/01_3mktnoAPutil.SOT",
        2: "./pods-outputs/ZF2-1/02_3mktutilnoAP.SOT",
        3: "./pods-outputs/ZF2-1/03_3mktAPutil.SOT",
        4: "./pods-outputs/ZF2-1/04_EMSRlowNT.SOT",
        5: "./pods-outputs/ZF2-1/05_EMSRNT.SOT",
        6: "./pods-outputs/ZF2-1/06_EMSRhiNT.SOT",
        7: "./pods-outputs/ZF2-1/07_EMSRlow.SOT",
        8: "./pods-outputs/ZF2-1/08_EMSR.SOT",
        9: "./pods-outputs/ZF2-1/09_EMSRhi.SOT",
        10: "./pods-outputs/ZF2-1/08_ProBPnoreoptnok",
    }
    target = vt.pods(files[experiment_n], config)
    return target
