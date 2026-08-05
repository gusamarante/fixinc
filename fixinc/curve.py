import warnings

import numpy as np
import pandas as pd
from scipy.interpolate import make_interp_spline, CubicSpline, interp1d

from fixinc.compounder import RateCompounder
from fixinc.daycount import DayCount


class ZeroCurve:

    def __init__(self, yields, yc='compound'):
        # TODO yields ref_date X years to mat
        # TODO assert date types
        self.yields = yields
        self.comp = RateCompounder(yc=yc)

    def interpolate(self, ref_date, mat, method="linear"):
        # TODO Documentation
        curve = self.yields.loc[ref_date].dropna()

        if method == "linear":
            fun = make_interp_spline(curve.index, curve.values, k=1)
            y_interp = fun(mat)

        elif method == "flat forward":
            logfactor = np.log(self.comp.yield_to_factor_yf(curve.values, curve.index))
            factor_interp = np.exp(make_interp_spline(curve.index, logfactor, k=1)(mat))
            y_interp = self.comp.factor_to_yield_yf(factor_interp, mat)

        elif method == "cubic spline":
            fun = CubicSpline(curve.index, curve.values)
            y_interp = fun(mat)

        else:
            raise NotImplementedError(f"Interpolation method {method} not inplemented")

        return y_interp

    def forward(self, t1, t2):
        # TODO Documentation

        # Linear Interpolation
        def get_fra(yc):
            yc = yc.dropna()
            fun = interp1d(yc.index, yc.values, kind="linear", fill_value="extrapolate")
            y1, y2 = fun(t1), fun(t2)
            fra = (((1 + y2) ** t2) / ((1 + y1) ** t1)) ** (1 / (t2 - t1)) - 1  # TODO use the compouder
            return fra

        fras = self.yields.apply(get_fra, axis=1)
        return fras


class Bootstrap:
    # TODO add a method to read the output as a zero curve, passing a convention

    weighting_methods = ["none", "duration", "inverse duration"]

    def __init__(self, cashflows, prices, durations=None, weighting="none"):
        """
        Non-parametric bootstrap of a discount curve. Finds the discount
        factor of every cashflow date that best prices a cross-section of
        bonds, in the weighted least squares sense.

        The model price of a bond is the sum of its cashflows multiplied by
        the discount factor of their respective dates

            price_i = sum_j cashflow_ji * discount_j

        which is linear on the discount factors, so the objective

            sum_i weight_i * (model price_i - observed price_i) ** 2

        is minimized exactly, with no initial guess required. Weights add up
        to 1, so the objective is a weighted mean squared pricing error, and
        is therefore comparable across dates with different numbers of bonds.

        Not every cashflow date carries a free discount factor. Only the
        maturity dates of the bonds do, and they are called the knots of the
        curve. A date that is not a maturity, a coupon date sitting between
        two maturities, has its discount factor restricted to the linear
        interpolation of the two neighboring knots.

        The output of the class is a discount factor curve which are free of
        market convetions (yield compounding, day-counting, etc) convention
        free.

        Parameters
        ----------
        cashflows: pandas.DataFrame
            Cashflow matrix, with payment dates as index and bond identifiers
            as columns. Dates where a given bond pays nothing must be zero,
            not NaN.

        prices: pandas.Series
            Observed market prices, indexed by bond identifier.

        durations: pandas.Series, optional
            Duration of each bond, indexed by bond identifier. Only used to
            build the weights of the objective function, so it can be left
            as None when `weighting` is 'none'.

        weighting: str
            How to weight the pricing error of each bond in the objective
            function. Supported values:
            - 'none': every bond has the same weight (default)
            - 'duration': weight proportional to duration, favoring the fit
                          of the long end
            - 'inverse duration': weight proportional to 1 / duration, which
                                  approximates weighting the errors in yield
                                  terms instead of price terms
            Weights are normalized to add up to 1, so the objective is a mean
            squared error under every choice. Normalization does not change
            the fitted discount factors, only the scale of `mse`.

        Examples
        --------
        The three panels below only differ on how many bonds there are and on
        which dates they pay, and together they cover every way the problem
        can turn out. Each table holds the cashflow matrix, with the dates `t`
        down the side and the bonds across the top, and the observed price of
        each bond on the last row.

        1) Exactly identified. Three bonds and three dates, and every date is
        the maturity of one of the bonds.

            t      |    A      B      C
            -------+-------------------
            0      |  100      4      4
            1      |    0    100      5
            2      |    0      0    102
            -------+-------------------
            price  |   95     90     80

        Each bond matures one date after the previous one, so the cashflow
        matrix is triangular and there are three knots for three prices. One
        curve prices all three bonds exactly, [0.950000, 0.862000, 0.704804],
        and it is found by working down from the shortest bond, which is what
        the bootstrap is named after. There is no pricing error to trade off,
        so `weighting` makes no difference here.

        2) Overidentified. Bond D is added, maturing on the same date as
        bond C.

            t      |    A      B      C      D
            -------+--------------------------
            0      |  100      4      4      5
            1      |    0    100      5      5
            2      |    0      0    102    105
            -------+--------------------------
            price  |   95     90     80     82

        The dates, and therefore the knots, are still three, but there are now
        four prices to match. Bonds A, B and C already pin the curve down, and
        that curve values bond D at 83.06 rather than the 82 it trades at, so
        no set of discount factors prices all four. The fit becomes a
        compromise, here erring by -0.53 on bond C and +0.52 on bond D, and
        `weighting` is what decides which bonds are matched more closely.

        3) Underidentified without the knot restriction. Bond C now pays a
        coupon on date 2 and matures on date 3.

            t      |    A       B        C
            -------+----------------------
            0      |  100       4        5
            1      |    0     104        5
            2      |    0       0        5
            3      |    0       0      105
            -------+----------------------
            price  |   95    97.4   98.575

        No bond matures on date 2, it only carries a coupon of bond C. A free
        discount factor per date would mean four unknowns for three prices,
        and the fourth one is not something the bonds have any information
        about: the minimum norm solution that comes out of it prices the three
        bonds perfectly while putting a discount factor of 0.04 on date 2,
        well below both of the surrounding dates.

        Restricting date 2 to the interpolation of dates 1 and 3 leaves three
        knots for three prices. The 5 that bond C pays on date 2 is split
        evenly between the knots on each side, and the curve comes out as
        [0.950000, 0.900000, 0.855000, 0.810000], smooth and pricing every
        bond exactly.
        """
        assert weighting in self.weighting_methods, \
            f"weighting method '{weighting}' not implemented"

        assert durations is not None or weighting == "none", \
            f"'{weighting}' weighting requires 'durations'"

        self._assert_matching_bonds(cashflows, prices, durations)

        self.cashflows = cashflows
        self.bonds = cashflows.columns
        self.dates = cashflows.index

        # Reindex so that bonds are in the same order everywhere
        self.prices = prices.reindex(self.bonds)
        self.durations = None if durations is None else durations.reindex(self.bonds)

        self.weighting = weighting
        self.weights = self._get_weights()

        self.knots = self._get_knots()
        self.interp_matrix = self._get_interp_matrix()

        self.knot_discount, self.rank = self._solve()
        self.discount = self.interpolate(self.knot_discount)
        self.fitted_prices = self.get_prices(self.discount)
        self.pricing_errors = self.fitted_prices - self.prices
        self.mse = self.objective(self.discount)

    def interpolate(self, knot_discount):
        """
        Builds the discount factor of every cashflow date from the discount
        factors of the knots. Knots are returned untouched, and any other
        date is the linear interpolation of its two neighbouring knots

        Parameters
        ----------
        knot_discount: pandas.Series
            Discount factor of each knot, indexed by knot

        Returns
        -------
        pandas.Series
        """
        knot_discount = knot_discount.reindex(self.knots)
        assert not knot_discount.isna().any(), \
            "'knot_discount' must cover every knot"
        return pd.Series(
            data=self.interp_matrix @ knot_discount.values,
            index=self.dates,
            name="discount factor",
        )

    def get_prices(self, discount):
        """
        Prices every bond by discounting its cashflows with a given set of
        discount factors

        Parameters
        ----------
        discount: pandas.Series
            Discount factor of each cashflow date, indexed by date

        Returns
        -------
        pandas.Series
        """
        discount = discount.reindex(self.dates)
        assert not discount.isna().any(), \
            "'discount' must cover every date of the cashflow matrix"
        return self.cashflows.mul(discount, axis=0).sum(axis=0)

    def objective(self, discount):
        """
        Weighted mean squared pricing error of a given set of discount
        factors. This is the quantity minimized by the bootstrap.

        Parameters
        ----------
        discount: pandas.Series
            Discount factor of each cashflow date, indexed by date

        Returns
        -------
        float
        """
        pricing_errors = self.get_prices(discount) - self.prices
        return (self.weights * (pricing_errors ** 2)).sum()

    def _get_weights(self):
        if self.weighting == "none":
            weights = pd.Series(index=self.bonds, data=1.0)

        elif self.weighting == "duration":
            assert (self.durations > 0).all(), \
                "'duration' weighting requires strictly positive durations"
            weights = self.durations.astype(float)

        elif self.weighting == "inverse duration":
            assert (self.durations > 0).all(), \
                "'inverse duration' weighting requires strictly positive durations"
            weights = 1 / self.durations.astype(float)

        else:
            raise NotImplementedError(
                f"weighting method '{self.weighting}' not implemented")

        return weights / weights.sum()

    def _get_knots(self):
        # The maturity of a bond is the last date it pays a cashflow. These
        # are the only dates that carry a free discount factor.
        paying = self.cashflows != 0
        assert paying.any().all(), \
            f"bonds with no cashflow at all: {sorted(self.bonds[~paying.any()])}"

        maturities = self.cashflows.apply(lambda cf: cf[cf != 0].index.max())
        return pd.Index(maturities.values).unique().sort_values()

    def _get_interp_matrix(self):
        # Row i holds the weight of each knot in the discount factor of
        # cashflow date i. A date that is itself a knot gets a weight of 1 on
        # it, and any other date splits its weight between the knot before
        # and the knot after, proportionally to the distance to each
        x_dates = self._positions(self.dates)
        x_knots = self._positions(self.knots)

        n_dates, n_knots = len(x_dates), len(x_knots)
        matrix = np.zeros((n_dates, n_knots))

        if n_knots == 1:
            # Degenerate case, a single discount factor for every date
            matrix[:, 0] = 1.0
            return matrix

        right = np.clip(np.searchsorted(x_knots, x_dates, side="left"), 1, n_knots - 1)
        left = right - 1

        span = x_knots[right] - x_knots[left]
        # The last cashflow date is always the maturity of the longest bond,
        # so there is nothing to extrapolate above the last knot. Below the
        # first knot, which needs a coupon paid before the shortest bond
        # matures, clipping holds the discount factor flat
        weight_right = np.clip((x_dates - x_knots[left]) / span, 0.0, 1.0)

        rows = np.arange(n_dates)
        matrix[rows, left] = 1 - weight_right
        matrix[rows, right] = weight_right
        return matrix

    def _positions(self, index):
        # Interpolation runs on calendar days when the cashflows are indexed
        # by date, and on the index itself when they are not
        origin = self.dates[0]
        if isinstance(self.dates, pd.DatetimeIndex):
            return (pd.DatetimeIndex(index) - origin).days.values.astype(float)
        return np.asarray(index, dtype=float) - float(origin)

    def _solve(self):
        # A cashflow paid between two knots is split between them by the
        # interpolation weights, so the bonds can be priced off the knots
        # alone
        knot_cashflows = self.interp_matrix.T @ self.cashflows.values

        # The pricing equation is linear on the knot discount factors, so the
        # weighted least squares problem
        #     min || sqrt(W) (C' d - p) || ** 2
        # is solved directly, without an iterative optimizer
        sqrt_weights = np.sqrt(self.weights.values)
        weighted_cashflows = knot_cashflows.T * sqrt_weights[:, None]
        weighted_prices = self.prices.values * sqrt_weights

        discount_factors, _, rank, _ = np.linalg.lstsq(
            weighted_cashflows, weighted_prices, rcond=None)

        if rank < len(self.knots):
            warnings.warn(
                f"The bootstrap is underdetermined: {len(self.bonds)} bonds "
                f"price {len(self.knots)} knots and the system has rank "
                f"{rank}. The discount factors of the {len(self.knots) - rank} "
                f"unidentified directions are the minimum norm solution, "
                f"which has no economic meaning."
            )

        discount = pd.Series(
            data=discount_factors, index=self.knots, name="discount factor")
        return discount, rank

    @staticmethod
    def _assert_matching_bonds(cashflows, prices, durations):
        cf_bonds = set(cashflows.columns)

        missing = cf_bonds - set(prices.index)
        extra = set(prices.index) - cf_bonds
        assert not missing and not extra, (
            f"'prices' does not match the columns of 'cashflows'. "
            f"Missing from 'prices': {sorted(missing)}. "
            f"Not in 'cashflows': {sorted(extra)}."
        )

        assert cashflows.columns.is_unique, "'cashflows' has duplicate columns"
        assert prices.index.is_unique, "'prices' has duplicate bonds"

        if durations is None:
            return

        missing = cf_bonds - set(durations.index)
        extra = set(durations.index) - cf_bonds
        assert not missing and not extra, (
            f"'durations' does not match the columns of 'cashflows'. "
            f"Missing from 'durations': {sorted(missing)}. "
            f"Not in 'cashflows': {sorted(extra)}."
        )

        assert durations.index.is_unique, "'durations' has duplicate bonds"
