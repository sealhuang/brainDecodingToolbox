# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import statsmodels.api as sm
from sklearn import linear_model
from scipy import stats


def ols_fit(y, x):
    """Return the R-squared value of the OLS fitted model."""
    x = sm.add_constant(x)
    res = sm.OLS(y, x).fit()
    return res.rsquared

class LinearRegression(linear_model.LinearRegression):
    """
    LinearRegression class after sklearn's, but calculate t-statistics
    and p-value for model coefficients (betas).
    Additional attributes available after .fit() are `t` and `p` which
    are of the shape (y.shape[1], X.shape[1]) which is (n_targets, n_coefs).
    This class sets the intercept to 0 by default, since usually we include
    it in X.
    """
    
    def __init__(self, *args, **kwargs):
        if not "fit_intercept" in kwargs:
            kwargs['fit_intercept'] = False
        super(LinearRegression, self).__init__(*args, **kwargs)

    def fit(self, X, y, n_jobs=1):
        self = super(LinearRegression, self).fit(X, y, n_jobs)
        
        sse = np.sum((self.predict(X)-y)**2,axis=0)/float(X.shape[0]-X.shape[1])
        if not sse.shape:
            sse = np.array([sse])
        se = np.array([
            np.sqrt(np.diagonal(sse[i]*np.linalg.inv(np.dot(X.T, X))))
                                    for i in range(sse.shape[0])
                    ])
        self.t = self.coef_ / se
        self.p = 2 * (1-stats.t.cdf(np.abs(self.t), y.shape[0]-X.shape[1]))
        return self


