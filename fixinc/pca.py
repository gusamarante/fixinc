from sklearn.decomposition import PCA
import pandas as pd
import numpy as np

# TODO Reconstructed curve


class CurvePCA:
    # TODO documentation with standartization

    def __init__(self, yields, n_components=3):
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


