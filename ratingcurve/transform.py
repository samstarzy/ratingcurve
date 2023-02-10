"""Data transformations to improve optimization"""
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from patsy import dmatrix, build_design_matrices

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


class Transform:
    """Transformation class

    All children of Transform must have transfom and untransform methods
    """
    def __init__(self, x):
        """Create empty Transform object
        """
        self.mean_ = None
        self.std_ = None

    def transform(self, x: ArrayLike) -> ArrayLike:
        """Transform data

        Parameters
        ----------
        x : array_like
            Data to be transformed.

        Returns
        -------
        ArrayLike
            Transformed data.
        """
        return x

    def untransform(self, x: ArrayLike) -> ArrayLike:
        return x

    def mean(self):
        raise NotImplementedError

    def sigma(self):
        raise NotImplementedError

    def median(self):
        raise NotImplementedError


class ZTransform(Transform):
    """Z-transforms data to have zero mean and unit variance
    """

    def __init__(self, x: ArrayLike):
        """Create a ZTransform object

        Parameters
        ----------
        x : array_like
          Data that defines the transform.
        """
        self.mean_ = np.nanmean(x, axis=0)
        self.std_ = np.nanstd(x, axis=0)

    def transform(self, x: ArrayLike) -> ArrayLike:
        """Transform to z score (standardize x)

        Parameters
        ----------
        x : array_like
          Data to be transformed.

        Returns
        -------
        ArrayLike
            original data standardized to zero mean and unit variance (z-score)
        """
        return (x - self.mean_) / self.std_

    def untransform(self, z: ArrayLike) -> ArrayLike:
        """Transform from z score back to original units.

        Parameters
        ----------
        z : array_like
          Transformed data

        Returns
        -------
        ArrayLike
            z-scores transformed back to original units.
        """
        return z * self.std_ + self.mean_


class LogZTransform(ZTransform):
    """Log transform then takes z-score.
    """

    def __init__(self, x: ArrayLike):
        """Create a LogZTransform for x.

        Parameters
        ----------
        x : array_like
          Data that defines the transform.
        """
        log_x = np.log(x)
        super().__init__(log_x)

    def transform(self, x: ArrayLike) -> ArrayLike:
        """Transform to log z-score

        Logs the data then standardizes to zero mean and unit variance.

        Parameters
        ----------
        x : array_like
          Data to be transformed.

        Returns
        -------
        ArrayLike
            log transform data standardized to zero mean and unit variance (log z-score)
        """
        log_x = np.log(x)
        return super().transform(log_x)

    def untransform(self, z: ArrayLike) -> ArrayLike:
        """Reverse log z-score transformation.

        Parameters
        ----------
        z : array_like
          Transformed data.

        Returns
        -------
        ArrayLike
            log z-scores transformed back to original units.
        """
        log_x = super().untransform(z)
        return np.exp(log_x)

    def mean(self, z: ArrayLike, axis: int = 1) -> ArrayLike:
        """Compute mean.

        Parameters
        ----------
        z : array_like
          Transformed data.

        Returns
        -------
        ArrayLike
            Arithmetic mean.
        """
        x = self.untransform(z)
        return x.mean(axis=axis)

    def sigma(self, z: ArrayLike, axis: int = 1) -> ArrayLike:
        """Compute standard deviation.

        Parameters
        ----------
        z : array_like
          Transformed data.

        Returns
        -------
        ArrayLike
            Multiplicative standard deviation.
        """
        sigma = z.std(axis=axis)
        return np.exp(sigma)
    
    def median(self, z: ArrayLike, axis: int = 1) -> ArrayLike:
        """Compute median.

        Parameters
        ----------
        z : array_like
          Transformed data.

        Returns
        -------
        ArrayLike
            Median or geometric mean.
        """
        x = self.untransform(z)
        return x.median(axis=axis)


class UnitTransform(Transform):
    """Transforms data to the unit (0 to 1) interval.
    """
    def __init__(self, x: ArrayLike):
        """Create UnitTransform of array

        Parameters
        ----------
        x : array_like
            Data that defines the transform.
        """
        self.max_ = np.nanmax(x, axis=0)

    def transform(self, x: ArrayLike) -> ArrayLike:
        """Transform to unit interval

        Parameters
        ----------
        x : array_like
            Data to be transformed.
        
        Returns
        -------
        ArrayLike
            Original data transformed to unit interval
        """
        return x/self.max_

    def untransform(self, x: ArrayLike) -> ArrayLike:
        """Transform from unit interval back to original units

        Parameters
        ----------
        x : array_like
          Transformed data.

        Returns
        -------
        ArrayLike
            Unit interval transformed back to original units.
        """
        return x*self.max_


class Dmatrix():
    """Transform for spline design matrix
    """
    def __init__(self, stage: ArrayLike, df: int, form: str = 'cr'):
        """Create a Dmatrix object
        
        Parameters
        ----------
        stage : array_like
          Stage data
        df : int
          Degrees of freedom
        form : str
          Spline form
        """
        temp = dmatrix(f"{form}(stage, df={df}) - 1", {"stage": stage})
        self.design_info = temp.design_info

    def transform(self, stage: ArrayLike) -> ArrayLike:
        """Transform stage using spline design matrix
 
        Parameters
        ----------
        stage : array-like
          Stage data

        Returns
        -------
        ArrayLike
            Transformed data
        """
        return np.asarray(build_design_matrices([self.design_info], {"stage": stage})).squeeze()