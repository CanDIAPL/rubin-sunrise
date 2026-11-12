"""New Full-sky Collector subsystem entry point.

Runs the data collection pipeline indefinitely, populating healpix FITS
files with observation data from the LSST simulator or RSV.

Entry point: `python -m rubin_sunrise.collector.new_collector_main`

**Author:** Anna Ordog
"""

from rubin_sunrise.collector.daily_sky import loop_sky


if __name__ == "__main__":
    loop_sky()