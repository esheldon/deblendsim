import os
import numpy as np
import ngmix

class CosmosSampler(object):
    def __init__(self,
                 r50_range=[0.05, 2.0],
                 flux_range=[0.5, 100.0],
                 kde_factor=0.01,
                 flux_mult=None,
                 rng=None):
        # Make sure required dependencies are checked right away, so the user gets timely
        # feedback of what this code requires.
        import scipy
        import fitsio
        import galsim

        if rng is None:
            rng=np.random.RandomState()

        self.rng=rng
        self.r50_range = r50_range
        self.flux_range = flux_range
        self.flux_mult=flux_mult

        self.r50_sanity_range=0.05,2.0
        self.flux_sanity_range=0.5,100.0
        self.kde_factor=kde_factor

        self._load_data()
        self._make_kde()

    def sample(self, size=None):
        """
        parameters
        ----------
        size: int, optional
            Number of samples to get. If not sent an array
            of size (2,) is returned with [r50,flux].
            If a number is sent, then an array of
            [size, 2] is returned, each row holding
            [r50,flux]
        """
        if size is None:
            size=1
            is_scalar=True
        else:
            is_scalar=False

        r50min,r50max=self.r50_range
        fmin,fmax=self.flux_range

        data=np.zeros( (size,2) )

        ngood=0
        nleft=data.shape[0]
        while nleft > 0:
            r = self._resample(nleft).T

            w,=np.where( (r[:,0] > r50min) &
                            (r[:,0] < r50max) &
                            (r[:,1] > fmin) &
                            (r[:,1] < fmax)
            )

            if w.size > 0:
                data[ngood:ngood+w.size,:] = r[w,:]
                ngood += w.size
                nleft -= w.size

        if self.flux_mult is not None:
            data[:,1] *= self.flux_mult
            
        if is_scalar:
            data=data[0,:]

        return data

    def _resample(self, size):
        # Equivalent to this line:
        #    return self.kde.resample(size=size)
        # except we do this using a numpy RandomState, rather than using the global
        # np.random state.
        # The following is basically copied from the scipy code, but patching in the use
        # of the RandomState where appropriate.

        svals = np.zeros( (self.kde.d,) )
        norm = self.rng.multivariate_normal(
            svals,
            self.kde.covariance,
            size=size,
        )

        norm = np.transpose(norm)

        indices = self.rng.randint(0, self.kde.n, size=size)
        means = self.kde.dataset[:, indices]
        return means + norm


    def _load_data(self):
        import fitsio
        import galsim
        fname='real_galaxy_catalog_25.2_fits.fits'
        fname=os.path.join(
            galsim.meta_data.share_dir,
            'COSMOS_25.2_training_sample',
            fname,
        )

        r50min,r50max=self.r50_sanity_range
        fmin,fmax=self.flux_sanity_range

        alldata=fitsio.read(fname, lower=True)
        w,=np.where(
            (alldata['viable_sersic']==1) &
            (alldata['hlr'][:,0] > r50min) &
            (alldata['hlr'][:,0] < r50max) &
            (alldata['flux'][:,0] > fmin) &
            (alldata['flux'][:,0] < fmax)
        )

        self.alldata=alldata[w]

    def _make_kde(self):
        import scipy.stats

        data=np.zeros( (self.alldata.size, 2) )
        data[:,0] = self.alldata['hlr'][:,0]
        data[:,1] = self.alldata['flux'][:,0]

        self.kde=scipy.stats.gaussian_kde(
            data.transpose(),
            bw_method=self.kde_factor,
        )

class Flat2D(object):
    def __init__(self, xrng, yrng, rng):

        self.rng=rng

        assert len(xrng)==2
        assert len(yrng)==2

        self.xrng=xrng
        self.yrng=yrng

    def sample(self, size=None):
        if size is None:
            size=1
            scalar=True
        else:
            scalar=False

        output=np.zeros( (size, 2) )
        output[:,0] = self.rng.uniform(
            low  = self.yrng[0],
            high = self.yrng[1],
            size=size,
        )
        output[:,1] = self.rng.uniform(
            low  = self.xrng[0],
            high = self.xrng[1],
            size=size,
        )

        if scalar:
            output=output[0]

        return output

class Constant(object):
    def __init__(self, value):
        self.value=value

    def sample(self):
        return self.value
