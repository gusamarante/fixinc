from statsmodels.tsa.vector_ar.var_model import VAR
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np

# TODO Reconstructed curve


class CurvePCA:
    # TODO documentation with standartization

    def __init__(self, yields, n_components=3):
        self.yields = yields
        self.n_components = n_components
        self.means = yields.mean()

        col_labels = [f"PC {i+1}" for i in range(n_components)]

        x = yields - self.means
        pca = PCA(n_components=n_components)
        pca.fit_transform(x)

        loadings, factors = self._standardize(pca.components_.T, pca.transform(x))

        self.exp_var_ration = pd.Series(
            data=pca.explained_variance_ratio_,
            index=col_labels,
        )

        self.loadings = pd.DataFrame(
            data=loadings,
            index=yields.columns,
            columns=col_labels,
        )

        self.factors = pd.DataFrame(
            data=factors,
            index=yields.index,
            columns=col_labels,
        )

        self.res_var = VAR(endog=self.factors).fit(1)

    def simulate_pcs(self, n_steps):
        """
        Estimates a VAR(1) for the factors to capture factor persistence
        and simulate it forward

        Parameters
        ----------
        n_steps: int
            number of steps ahead to simulate
        """
        sim = self.res_var.simulate_var(steps=n_steps + 1, initial_values=self.factors.values[-1:, :])
        sim = pd.DataFrame(
            data=sim,
            columns=self.factors.columns
        )
        return sim

    def simulate_curve(self, n_steps):
        """
        Estimates a VAR(1) for the factors to capture factor persistence
        and simulate them forward, and them reconstructs the curve based
        on the factor loadings

        Parameters
        ----------
        n_steps: int
            number of steps ahead to simulate
        """
        sim = self.simulate_pcs(n_steps)
        return self.reconstruct(sim)


    def reconstruct(self, factors):
        """
        Reconstruct the original data from the factors.

        Parameters
        ----------
        factors : array-like, shape (n_samples, n_components)
            The factor scores to use for reconstruction
        """
        return pd.DataFrame(
            data=np.dot(factors, self.loadings.T) + self.means.values,
            columns=self.loadings.index,
        )

    @staticmethod
    def _standardize(loadings, factors):
        """
        Since the direction of the components is arbitrary, we standardize
        the sign of the last row of the loadings to be positive.
        """
        signal = np.sign(loadings[-1, :])
        loadings = loadings * signal
        factors = factors * signal
        return loadings, factors
