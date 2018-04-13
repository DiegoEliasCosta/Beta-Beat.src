"""
Provides Class to get response matrices from Twiss parameters.

The calculation is based on formulas in [#FranchiAnalyticformulasrapid2017]_, [#TomasReviewlinearoptics2017]_.


Only works properly for on-orbit twiss files.

 * Beta Beating Response:  Eq. A35 inserted into Eq. B45 in [#FranchiAnalyticformulasrapid2017]_
 * Dispersion Response:    Eq. 25-27 in [#FranchiAnalyticformulasrapid2017]_
 * Phase Advance Response: Eq. 28 in [#FranchiAnalyticformulasrapid2017]_
 * Tune Response:          Eq. 7 in [#TomasReviewlinearoptics2017]_

For people reading the code, the response matrices are first calculated like:

::

    |  Elements of interest (j) --> ... |
    |Magnets (m)                        |
    |  |                                |
    |  v                                |
    |  .                                |
    |  .                                |
    |  .                                |
    |                                   |

As this was avoided transposing all vectors in the beginning.
At the end (of the calculation) the matrix is then transposed
to fit the :math:`M \cdot \delta K` orientation.

.. rubric:: References

..  [#FranchiAnalyticformulasrapid2017]
    A. Franchi et al.,
    Analytic formulas for the rapid evaluation of the orbit response matrix
    and chromatic functions from lattice parameters in circular accelerators
    https://arxiv.org/abs/1711.06589

.. [#TomasReviewlinearoptics2017]
    R. Tomas, et al.,
    'Review of linear optics measurement and correction for charged particle
    accelerators.'
    Physical Review Accelerators and Beams, 20(5), 54801. (2017)
    https://doi.org/10.1103/PhysRevAccelBeams.20.054801

"""
import cPickle as pickle

import numpy as np
import pandas as pd

from correction.fullresponse.sequence_evaluation import check_varmap_file
from twiss_optics.twiss_functions import get_phase_advances, tau, dphi
from twiss_optics.twiss_functions import regex_in, upper
from utils import logging_tools as logtool
from utils import tfs_pandas as tfs
from utils.contexts import timeit

LOG = logtool.get_logger(__name__)

DUMMY_ID = "DUMMY_PLACEHOLDER"


# Twiss Response Class ########################################################


class TwissResponse(object):
    """ Provides Response Matrices calculated from sequence, model and given variables.

    Args:
        varmap_or_seq_path: Path to sequence file. If there is a pre-parsed .varmap file in the same
            folder, it will use this one. (Hence, can also be the path to this file)
        model_or_path: Path to twiss-model file, or model
        variables: List of variable-names
        direction: Either +1 or -1, default +1.
        at_elements (str): Get response matrix for these elements. Can be:
            'bpms': All BPMS (Default)
            'bpms+': BPMS+ used magnets (== magnets defined by variables in varfile)
            'all': All BPMS and Magnets given in the model (Markers are removed)

    """

    ################################
    #            INIT
    ################################

    def __init__(self, varmap_or_path, model_or_path, variables, direction=1,
                 at_elements='bpms'):

        LOG.debug("Initializing TwissResponse.")
        with timeit(lambda t: LOG.debug("  Time initializing TwissResponse: {:f}s".format(t))):
            # Get input
            self._twiss = self._get_model_twiss(model_or_path)
            self._variables = variables
            self._var_to_el = self._get_variable_mapping(varmap_or_path)
            self._elements_in = self._get_input_elements()
            self._elements_out = self._get_output_elements(at_elements)
            self._direction = self._get_direction(direction)

            # calculate all phase advances
            self._phase_advances = get_phase_advances(self._twiss)

            # All responses are calcluated as needed, see getters below!
            # slots for response matrices
            self._beta = None
            self._dispersion = None
            self._phase = None
            self._phase_adv = None
            self._tune = None
            self._coupling = None
            self._beta_beat = None
            self._norm_dispersion = None

            # slots for mapped response matrices
            self._coupling_mapped = None
            self._beta_mapped = None
            self._dispersion_mapped = None
            self._phase_mapped = None
            self._phase_adv_mapped = None
            self._tune_mapped = None
            self._beta_beat_mapped = None
            self._norm_dispersion_mapped = None

    @staticmethod
    def _get_model_twiss(model_or_path):
        """ Load model, but keep only BPMs and Magnets """
        try:
            model = tfs.read_tfs(model_or_path, index="NAME")
        except TypeError:
            LOG.debug("Received model as DataFrame")
            model = model_or_path
        else:
            LOG.debug("Loaded Model from file '{:s}'".format(model_or_path))

        # Remove not needed entries
        LOG.debug("Removing non-necessary entries:")
        LOG.debug("  Entries total: {:d}".format(model.shape[0]))
        model = model.loc[regex_in(r"\A(M|BPM)", model.index), :]
        LOG.debug("  Entries left: {:d}".format(model.shape[0]))

        # make a copy to suppress "SettingWithCopyWarning"
        model = model.copy()

        # Add Dummy for Phase Calculations
        model.loc[DUMMY_ID, ["S", "MUX", "MUY"]] = 0.0
        return model

    def _get_variable_mapping(self, varmap_or_path):
        """ Get variable mapping as dictionary

        Define _variables first!
        """
        LOG.debug("Converting variables to magnet names.")
        variables = self._variables

        try:
            with open(varmap_or_path, "rb") as varmapfile:
                mapping = pickle.load(varmapfile)
        except TypeError:
            LOG.debug("Received varmap as dictionary.")
            mapping = varmap_or_path
        else:
            LOG.debug("Loaded varmap from file '{:s}'".format(varmap_or_path))

        for order in ("K0L", "K0SL", "K1L", "K1SL"):
            if order not in mapping:
                mapping[order] = {}

        # check if all variables can be found
        check_var = [var for var in variables
                     if all(var not in mapping[order] for order in mapping)]
        if len(check_var) > 0:
            raise ValueError("Variables '{:s}' cannot be found in sequence!".format(
                ", ".join(check_var)
            ))

        # drop mapping for unused variables
        [mapping[order].pop(var) for order in mapping for var in mapping[order].keys()
         if var not in variables]

        return mapping

    def _get_input_elements(self):
        """ Return variable names of input elements.

        Define _var_to_el and _twiss first!
        """
        v2e = self._var_to_el
        tw = self._twiss

        el_in = dict.fromkeys(v2e.keys())
        for order in el_in:
            el_order = []
            for var in v2e[order]:
                el_order += upper(v2e[order][var].index)
            el_in[order] = tw.loc[list(set(el_order)), "S"].sort_values().index.tolist()
        return el_in

    @staticmethod
    def _get_direction(direction):
        if direction not in [+1, -1]:
            raise AttributeError(
                "Direction can be either +1 or -1, instead it was {}".format(direction)
            )
        return direction

    def _get_output_elements(self, at_elements):
        """ Return name-array of elements to use for output.

        Define _elements_in first!
        """
        tw_idx = self._twiss.index

        if isinstance(at_elements, list):
            # elements specified
            if any(el not in tw_idx for el in at_elements):
                LOG.warning("One or more specified elements are not in the model.")
            return [idx for idx in tw_idx
                    if idx in at_elements]

        if at_elements == "bpms":
            # bpms only
            return [idx for idx in tw_idx
                    if idx.upper().startswith('B')]

        if at_elements == "bpms+":
            # bpms and the used magnets
            el_in = self._elements_in
            return [idx for idx in tw_idx
                    if (idx.upper().startswith('B')
                        or any(idx in el_in[order] for order in el_in))]

        if at_elements == "all":
            # all, obviously
            return [idx for idx in tw_idx if idx != DUMMY_ID]

    ################################
    #       Response Matrix
    ################################

    def _calc_coupling_response(self):
        """ Response Matrix for coupling.

        Eq. 10 in [#FranchiAnalyticformulasrapid2017]_
        """
        LOG.debug("Calculate Coupling Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}s".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            el_out = self._elements_out
            k1s_el = self._elements_in["K1SL"]
            dcoupl = dict.fromkeys(["1001", "1010"])

            i2pi = 2j * np.pi
            phx = dphi(adv['X'].loc[k1s_el, el_out], tw.Q1).values
            phy = dphi(adv['Y'].loc[k1s_el, el_out], tw.Q2).values
            bet_term = np.sqrt(tw.loc[k1s_el, "BETX"].values * tw.loc[k1s_el, "BETY"].values)

            for plane in ["1001", "1010"]:
                phs_sign = -1 if plane == "1001" else 1
                dcoupl[plane] = tfs.TfsDataFrame(
                    bet_term[:, None] * np.exp(i2pi * (phx + phs_sign * phy)) /
                    (4 * (1 - np.exp(i2pi * (tw.Q1 + phs_sign * tw.Q2)))),
                    index=k1s_el, columns=el_out).transpose()
        return dict_mul(self._direction, dcoupl)

    def _calc_beta_response(self):
        """ Response Matrix for delta beta.

        Eq. A35 -> Eq. B45 in [#FranchiAnalyticformulasrapid2017]_
        """
        LOG.debug("Calculate Beta Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}s".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            el_out = self._elements_out
            k1_el = self._elements_in["K1L"]
            dbeta = dict.fromkeys(["X", "Y"])

            for plane in ["X", "Y"]:
                col_beta = "BET" + plane
                q = tw.Q1 if plane == "X" else tw.Q2
                coeff_sign = -1 if plane == "X" else 1

                pi2tau = 2 * np.pi * tau(adv[plane].loc[k1_el, el_out], q)

                dbeta[plane] = tfs.TfsDataFrame(
                    tw.loc[el_out, col_beta].values[None, :] *
                    tw.loc[k1_el, col_beta].values[:, None] * np.cos(2 * pi2tau.values) *
                    (coeff_sign / (2 * np.sin(2 * np.pi * q))),
                    index=k1_el, columns=el_out).transpose()

        return dict_mul(self._direction, dbeta)

    def _calc_dispersion_response(self):
        """ Response Matrix for delta dispersion

            Eq. 25-27 in [#FranchiAnalyticformulasrapid2017]_
        """
        LOG.debug("Calculate Dispersion Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            el_out = self._elements_out
            els_in = self._elements_in

            disp_resp = dict.fromkeys(["X_K0L", "X_K1SL", "Y_K0SL", "Y_K1SL"])

            for plane in ["X", "Y"]:
                q = tw.Q1 if plane == "X" else tw.Q2
                type_plane = ("K0L" if plane == "X" else "K0SL", "K1SL")
                el_in_plane = (els_in[type_plane[0]], els_in[type_plane[1]])
                col_beta = "BET" + plane
                col_disp = "DY" if plane == "X" else "DX"

                if any((len(el_in_plane[0]), len(el_in_plane[1]))):
                    coeff = np.sqrt(tw.loc[el_out, col_beta].values) / (2 * np.sin(np.pi * q))

                for el_in, el_type in zip(el_in_plane, type_plane):
                    coeff_sign = -1 if el_type == "K0SL" else 1
                    out_str = "{p:s}_{t:s}".format(p=plane, t=el_type)

                    if len(el_in):
                        pi2tau = 2 * np.pi * tau(adv[plane].loc[el_in, el_out], q)
                        bet_term = np.sqrt(tw.loc[el_in, col_beta].values)
                        if el_type == "K1SL":
                            bet_term *= tw.loc[el_in, col_disp].values
                        disp_resp[out_str] = tfs.TfsDataFrame(
                            coeff_sign * coeff[None, :] * bet_term[:, None] * np.cos(pi2tau),
                            index=el_in, columns=el_out).transpose()
                    else:
                        LOG.debug(
                            "  No '{:s}' variables found. ".format(el_type) +
                            "Dispersion Response '{:s}' will be empty.".format(out_str))
                        disp_resp[out_str] = tfs.TfsDataFrame(None, index=el_out)
        return dict_mul(self._direction, disp_resp)

    def _calc_norm_dispersion_response(self):
        """ Response Matrix for delta normalized dispersion

            Eq. 25-27 in [#FranchiAnalyticformulasrapid2017]_
            But w/o the assumtion :math:`\delta K_1 = 0` from Appendix B.1
        """
        LOG.debug("Calculate Normalized Dispersion Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            el_out = self._elements_out
            els_in = self._elements_in

            col_disp_map = {
                "X": {"K1L": "DX", "K1SL": "DY", },
                "Y": {"K1L": "DY", "K1SL": "DX", },
            }

            sign_map = {
                "X": {"K0L": 1, "K1L": -1, "K1SL": 1, },
                "Y": {"K0SL": -1, "K1L": 1, "K1SL": 1, },
            }

            q_map = {"X": tw.Q1, "Y": tw.Q2}
            disp_resp = dict.fromkeys(["{p:s}_{t:s}".format(p=p, t=t)
                                       for p in sign_map for t in sign_map[p]])

            for plane in sign_map:
                q = q_map[plane]
                col_beta = "BET{}".format(plane)
                el_types = sign_map[plane]
                els_per_type = [els_in[el_type] for el_type in el_types]

                if any([len(el_in) for el_in in els_per_type]):
                    coeff = 1 / (2 * np.sin(np.pi * q))

                for el_in, el_type in zip(els_per_type, el_types):
                    coeff_sign = sign_map[plane][el_type]
                    out_str = "{p:s}_{t:s}".format(p=plane, t=el_type)

                    if len(el_in):
                        pi2tau = 2 * np.pi * tau(adv[plane].loc[el_in, el_out], q)
                        bet_term = np.sqrt(tw.loc[el_in, col_beta].values)

                        try:
                            col_disp = col_disp_map[plane][el_type]
                        except KeyError:
                            pass
                        else:
                            bet_term *= tw.loc[el_in, col_disp].values

                        disp_resp[out_str] = tfs.TfsDataFrame(
                            coeff_sign * coeff[None, :] * bet_term[:, None] * np.cos(pi2tau),
                            index=el_in, columns=el_out).transpose()
                    else:
                        LOG.debug(
                            "  No '{:s}' variables found. ".format(el_type) +
                            "Normalized Dispersion Response '{:s}' will be empty.".format(out_str))
                        disp_resp[out_str] = tfs.TfsDataFrame(None, index=el_out)
        return dict_mul(self._direction, disp_resp)

    def _calc_phase_advance_response(self):
        """ Response Matrix for delta DPhi.

        Eq. 28 in [#FranchiAnalyticformulasrapid2017]_
        Reduced to only phase advances between consecutive elements,
        as the 3D-Matrix of all elements exceeds memory space
        (~11000^3 = 1331 Giga Elements)
        --> w = j-1:  DPhi(z,j) = DPhi(x, (j-1)->j)
        """
        LOG.debug("Calculate Phase Advance Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}s".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            k1_el = self._elements_in["K1L"]

            el_out_all = [DUMMY_ID] + self._elements_out  # Add MU[XY] = 0.0 to the start
            el_out = el_out_all[1:]  # in these we are actually interested
            el_out_mm = el_out_all[0:-1]  # elements--

            if len(k1_el) > 0:
                dmu = dict.fromkeys(["X", "Y"])

                pi = tfs.TfsDataFrame(tw['S'][:, None] < tw['S'][None, :],  # pi(i,j) = s(i) < s(j)
                                      index=tw.index, columns=tw.index, dtype=int)

                pi_term = (pi.loc[k1_el, el_out].values -
                           pi.loc[k1_el, el_out_mm].values +
                           np.diag(pi.loc[el_out, el_out_mm].values)[None, :])

                for plane in ["X", "Y"]:
                    col_beta = "BET" + plane
                    q = tw.Q1 if plane == "X" else tw.Q2
                    coeff_sign = 1 if plane == "X" else -1

                    pi2tau = 2 * np.pi * tau(adv[plane].loc[k1_el, el_out_all], q)
                    brackets = (2 * pi_term +
                                ((np.sin(2 * pi2tau.loc[:, el_out].values) -
                                  np.sin(2 * pi2tau.loc[:, el_out_mm].values))
                                 / np.sin(2 * np.pi * q)
                                 ))
                    dmu[plane] = tfs.TfsDataFrame(
                        tw.loc[k1_el, col_beta].values[:, None] * brackets
                        * (coeff_sign / (8 * np.pi)),
                        index=k1_el, columns=el_out).transpose()
            else:
                LOG.debug("  No 'K1L' variables found. Phase Response will be empty.")
                dmu = {"X": tfs.TfsDataFrame(None, index=el_out),
                       "Y": tfs.TfsDataFrame(None, index=el_out)}

        return dict_mul(self._direction, dmu)

    def _calc_phase_response(self):
        """ Response Matrix for delta DPhi.

        Eq. 28 in [#FranchiAnalyticformulasrapid2017]_
        Reduced to only delta phase.
        --> w = 0:  DPhi(z,j) = DPhi(x, 0->j)

        This calculation could also be achieved by applying np.cumsum to the DataFrames of
        _calc_phase_adv_response() (tested!), but _calc_phase_response() is about 4x faster.
        """
        LOG.debug("Calculate Phase Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}s".format(t))):
            tw = self._twiss
            adv = self._phase_advances
            k1_el = self._elements_in["K1L"]
            el_out = self._elements_out

            if len(k1_el) > 0:
                dmu = dict.fromkeys(["X", "Y"])

                pi = tfs.TfsDataFrame(tw['S'][:, None] < tw['S'][None, :],  # pi(i,j) = s(i) < s(j)
                                      index=tw.index, columns=tw.index, dtype=int)

                pi_term = pi.loc[k1_el, el_out].values

                for plane in ["X", "Y"]:
                    col_beta = "BET" + plane
                    q = tw.Q1 if plane == "X" else tw.Q2
                    coeff_sign = 1 if plane == "X" else -1

                    pi2tau = 2 * np.pi * tau(adv[plane].loc[k1_el, [DUMMY_ID] + el_out], q)
                    brackets = (2 * pi_term +
                                ((np.sin(2 * pi2tau.loc[:, el_out].values) -
                                  np.sin(2 * pi2tau.loc[:, DUMMY_ID].values[:, None]))
                                 / np.sin(2 * np.pi * q)
                                 ))
                    dmu[plane] = tfs.TfsDataFrame(
                        tw.loc[k1_el, col_beta].values[:, None] * brackets
                        * (coeff_sign / (8 * np.pi)),
                        index=k1_el, columns=el_out).transpose()
            else:
                LOG.debug("  No 'K1L' variables found. Phase Response will be empty.")
                dmu = {"X": tfs.TfsDataFrame(None, index=el_out),
                       "Y": tfs.TfsDataFrame(None, index=el_out)}

        return dict_mul(self._direction, dmu)

    def _calc_tune_response(self):
        """ Response vectors for Tune.

        Eq. 7 in [#TomasReviewlinearoptics2017]_
        """
        LOG.debug("Calculate Tune Response Matrix")
        with timeit(lambda t: LOG.debug("  Time needed: {:f}s".format(t))):
            tw = self._twiss
            k1_el = self._elements_in["K1L"]

            if len(k1_el) > 0:
                dtune = dict.fromkeys(["X", "Y"])

                dtune["X"] = 1/(4 * np.pi) * tw.loc[k1_el, ["BETX"]].transpose()
                dtune["X"].index = ["DQX"]

                dtune["Y"] = -1 / (4 * np.pi) * tw.loc[k1_el, ["BETY"]].transpose()
                dtune["Y"].index = ["DQY"]
            else:
                LOG.debug("  No 'K1L' variables found. Tune Response will be empty.")
                dtune = {"X": tfs.TfsDataFrame(None, index=["DQX"]),
                         "Y": tfs.TfsDataFrame(None, index=["DQY"])}

        return dict_mul(self._direction, dtune)

    ################################
    #       Normalizing
    ################################

    def _normalize_beta_response(self, beta):
        """ Convert to Beta Beating """
        el_out = self._elements_out
        tw = self._twiss

        beta_norm = dict.fromkeys(beta.keys())
        for plane in beta:
            col = "BET" + plane
            beta_norm[plane] = beta[plane].div(
                tw.loc[el_out, col], axis='index')
        return beta_norm

    ################################
    #       Mapping
    ################################

    def _map_dispersion_response(self, disp):
        """ Maps all dispersion matrices """
        disp_mapped = dict.fromkeys(disp.keys())
        m2v = self._map_to_variables
        for plane in disp:
            mapping = self._var_to_el[plane.split("_")[1]]
            disp_mapped[plane] = m2v(disp[plane], mapping)
        return disp_mapped

    @staticmethod
    def _map_to_variables(df, mapping):
        """ Maps from magnets to variables using self._var_to_el.
            Could actually be done by matrix multiplication :math:'A \cdot var_to_el',
             yet, as var_to_el is very sparsely populated, looping is easier.

            Args:
                df: DataFrame or dictionary of DataFrames to map
                mapping: mapping to be applied (e.g. var_to_el[order])
            Returns:
                DataFrame or dictionary of mapped DataFrames
        """
        def map_fun(df, mapping):
            """ Actual mapping function """
            df_map = tfs.TfsDataFrame(index=df.index, columns=mapping.keys())
            for var, magnets in mapping.iteritems():
                df_map[var] = df.loc[:, upper(magnets.index)].mul(
                    magnets.values, axis="columns"
                ).sum(axis="columns")
            return df_map

        # convenience wrapper for dicts
        if isinstance(df, dict):
            mapped = dict.fromkeys(df.keys())
            for plane in mapped:
                mapped[plane] = map_fun(df[plane], mapping)
        else:
            mapped = map_fun(df, mapping)
        return mapped

    ################################
    #          Getters
    ################################

    def get_beta(self, mapped=True):
        """ Returns Response Matrix for Beta """
        if not self._beta:
            self._beta = self._calc_beta_response()

        if mapped and not self._beta_mapped:
            self._beta_mapped = self._map_to_variables(self._beta,
                                                       self._var_to_el["K1L"])

        if mapped:
            return self._beta_mapped
        else:
            return self._beta

    def get_beta_beat(self, mapped=True):
        """ Returns Response Matrix for Beta Beating """
        if not self._beta:
            self._beta = self._calc_beta_response()

        if not self._beta_beat:
            self._beta_beat = self._normalize_beta_response(self._beta)

        if mapped and not self._beta_beat_mapped:
            self._beta_beat_mapped = self._map_to_variables(self._beta_beat,
                                                            self._var_to_el["K1L"])

        if mapped:
            return self._beta_beat_mapped
        else:
            return self._beta_beat

    def get_dispersion(self, mapped=True):
        """ Returns Response Matrix for Dispersion """
        if not self._dispersion:
            self._dispersion = self._calc_dispersion_response()

        if mapped and not self._dispersion_mapped:
            self._dispersion_mapped = self._map_dispersion_response(self._dispersion)

        if mapped:
            return self._dispersion_mapped
        else:
            return self._dispersion

    def get_norm_dispersion(self, mapped=True):
        """ Returns Response Matrix for Normalized Dispersion """
        if not self._norm_dispersion:
            self._norm_dispersion = self._calc_norm_dispersion_response()

        if mapped and not self._norm_dispersion_mapped:
            self._norm_dispersion_mapped = self._map_dispersion_response(self._norm_dispersion)

        if mapped:
            return self._norm_dispersion_mapped
        else:
            return self._norm_dispersion

    def get_phase(self, mapped=True):
        """ Returns Response Matrix for Total Phase """
        if not self._phase:
            self._phase = self._calc_phase_response()

        if mapped and not self._phase_mapped:
            self._phase_mapped = self._map_to_variables(self._phase, self._var_to_el["K1L"])

        if mapped:
            return self._phase_mapped
        else:
            return self._phase

    def get_phase_adv(self, mapped=True):
        """ Returns Response Matrix for Phase Advance """
        if not self._phase_adv:
            self._phase_adv = self._calc_phase_advance_response()

        if mapped and not self._phase_adv_mapped:
            self._phase_adv_mapped = self._map_to_variables(self._phase_adv, self._var_to_el["K1L"])

        if mapped:
            return self._phase_adv_mapped
        else:
            return self._phase_adv

    def get_tune(self, mapped=True):
        """ Returns Response Matrix for the Tunes """
        if not self._tune:
            self._tune = self._calc_tune_response()

        if mapped and not self._tune_mapped:
            self._tune_mapped = self._map_to_variables(self._tune, self._var_to_el["K1L"])

        if mapped:
            return self._tune_mapped
        else:
            return self._tune

    def get_coupling(self, mapped=True):
        """ Returns Response Matrix for the coupling """
        if not self._coupling:
            self._coupling = self._calc_coupling_response()

        if mapped and not self._coupling_mapped:
            self._coupling_mapped = self._map_to_variables(self._coupling, self._var_to_el["K1SL"])

        if mapped:
            return self._coupling_mapped
        else:
            return self._coupling

    def get_variable_names(self):
        return self._variables

    def get_variable_mapping(self, order=None):
        if order is None:
            return self._var_to_el
        else:
            return self._var_to_el[order]

    def get_response_for(self, obs=None):
        """ Calculates and returns only desired response matrices """
        # calling functions for the getters to call functions only if needed
        def caller(func, plane):
            return func()[plane]

        def disp_caller(func, plane):
            disp = func()
            return response_add(*[disp[k] for k in disp.keys() if k.startswith(plane)])

        def tune_caller(func, _unused):
            tune = func()
            res = tune["X"].append(tune["Y"])
            res.index = ["Q1", "Q2"]
            return res

        def couple_caller(func, plane):
            # apply() converts empty DataFrames to Series! Cast them back.
            # Also: take care of minus-sign convention!
            sign = -1 if plane[-1] == "R" else 1
            part_func = np.real if plane[-1] == "R" else np.imag
            return sign * tfs.TfsDataFrame(func()[plane[:-1]].apply(part_func).astype(np.float64))

        # to avoid if-elif-elif-...
        obs_map = {
            'Q': (tune_caller, self.get_tune, None),
            'BETX': (caller, self.get_beta, "X"),
            'BETY': (caller, self.get_beta, "Y"),
            'BBX': (caller, self.get_beta_beat, "X"),
            'BBY': (caller, self.get_beta_beat, "Y"),
            'MUX': (caller, self.get_phase, "X"),
            'MUY': (caller, self.get_phase, "Y"),
            'DX': (disp_caller, self.get_dispersion, "X"),
            'DY': (disp_caller, self.get_dispersion, "Y"),
            'NDX': (disp_caller, self.get_norm_dispersion, "X"),
            'NDY': (disp_caller, self.get_norm_dispersion, "Y"),
            'F1001R': (couple_caller, self.get_coupling, "1001R"),
            'F1001I': (couple_caller, self.get_coupling, "1001I"),
            'F1010R': (couple_caller, self.get_coupling, "1010R"),
            'F1010I': (couple_caller, self.get_coupling, "1010I"),
        }

        if obs is None:
            obs = obs_map.keys()

        LOG.debug("Calculating responses for {:s}.".format(obs))
        with timeit(lambda t: LOG.debug("Total time getting responses: {:f}s".format(t))):
            response = dict.fromkeys(obs)
            for key in obs:
                response[key] = obs_map[key][0](*obs_map[key][1:3])
        return response


# Associated Functions #########################################################


def get_delta(response, delta_k):
    """ Returns the deltas of :math:`response_matrix \cdot delta_k`.

    Args:
        response: Response dictionary
        delta_k: Pandas Series of variables and their delta-value

    Returns:
        TFS_DataFrame with elements as indices and the calculated deltas in the columns
    """
    delta_df = tfs.TfsDataFrame(None, index=response.index)
    for col in response.keys():
        # equivalent to .dot() but more efficient as delta_k is "sparse"
        if col == "Q":
            try:
                delta_q = (response[col].loc[:, delta_k.index] * delta_k
                           ).dropna(axis="columns").sum(axis="columns")
            except KeyError:
                # none of the delta_k are in DataFrame
                delta_q = pd.Series([0., 0.], index=["Q1", "Q2"])
            delta_df.headers["QX"] = delta_q["Q1"]
            delta_df.headers["QY"] = delta_q["Q2"]
        else:
            try:
                delta_df.loc[:, col] = (response[col].loc[:, delta_k.index] * delta_k
                                        ).dropna(axis="columns").sum(axis="columns")
            except KeyError:
                # none of the delta_k are in DataFrame
                delta_df.loc[:, col] = 0.
    return delta_df


def response_add(*args):
    """ Merges two or more Response Matrix DataFrames """
    base_df = args[0]
    for df in args[1:]:
        base_df = base_df.add(df, fill_value=0.)
    return base_df


def dict_mul(number, dictionary):
    """ Multiply an int with a dict of dataframes (or anything multiplyable) """
    if number != 1:
        for key in dictionary:
            dictionary[key] = number * dictionary[key]
    return dictionary


# Wrapper ##################################################################


def create_response(accel_inst, vars_categories, optics_params):
    """ Wrapper to create response via TwissResponse """
    LOG.debug("Creating response via TwissResponse.")
    vars_list = accel_inst.get_variables(classes=vars_categories)
    if len(vars_list) == 0:
        raise ValueError("No variables found! Make sure your categories are valid!")

    varmap_path = check_varmap_file(accel_inst, vars_categories)

    with timeit(lambda t:
                LOG.debug("Total time getting TwissResponse: {:f}s".format(t))):
        sign = 1 if accel_inst.get_beam() == 1 else -1
        tr = TwissResponse(varmap_path, accel_inst.get_elements_tfs(), vars_list, sign)
        response = tr.get_response_for(optics_params)

    if not any([resp.size for resp in response.values()]):
        raise ValueError("Responses are all empty. " +
                         "Are variables {:s} ".format(vars_list) +
                         "correct for '{:s}'?".format(optics_params)
                         )
    return response


# Script Mode ##################################################################


if __name__ == '__main__':
    raise EnvironmentError("{:s} is not supposed to run as main.".format(__file__))
