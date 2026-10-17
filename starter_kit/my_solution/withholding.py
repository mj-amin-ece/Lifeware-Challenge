"""t7: the taxes withheld from a payout (withdrawal, surrender, death benefit).

- Gain of a payout: the payout converted into the tax currency on the payout day, less the premiums paid, each one
  converted on the day it was received (and reduced by the shares already withdrawn), times the share now withdrawn.
- CH: withholding tax (VST) on the whole payout in CHF.
- IT: substitute tax (SOS) on the gain, each rate weighted by the days of the contract in its period: the law
  applied the rate changes of 2012 and 2014 pro rata temporis to the gain accrued before them.
- DE: capital gains tax (KST) on the gain, less the partial exemption (TFS) from 2018 and only half of it (HEV) after
  12 years and from the age of 60 (62 from 2012); solidarity surcharge (SOL) and church tax (KIS) on the KST. For a
  church member the KST is base / (4 + church rate) instead of 25 %: the tax is reduced by a quarter of the church tax
  on it (section 32d of the German income tax act).
"""
from payout_basis import HALF_INCOME, PayoutBasis
from decimal import Decimal

from rules import money

WITHHOLDING = {'CH': 'VST', 'IT': 'SOS', 'DE': 'KST'}


class Withholding(PayoutBasis):
    def italian_rate(self, policy, day, known):
        """
        Substitute tax rate of a payout: every rate known at `known`, weighted by the days of the contract in its
        validity period (pro rata temporis).

        Parameters:
        - policy (str): Policy number.
        - day (datetime.date): Day of the payout.
        - known (pd.Timestamp): Processing time of the payout.

        Returns:
        - Decimal: Weighted rate.
        """
        begin = self.policies[policy].PH_BEGDT.date()
        weighted = Decimal(0)
        for region, start, end, _, entered, rate, _ in self.rates.rows[('IT', 'SOS')]:
            days = (min(day, end) - max(begin, start)).days + 1
            if not region and entered <= known and days > 0:
                weighted += rate * days
        return weighted / ((day - begin).days + 1)

    def withholding(self, policy, payout, withdrawals, country, region):
        """
        Report the payout base independently of whether Neuron booked withholding.

        The absence of a withholding booking controls the tax amounts, rather than
        erasing the base; a loss is reported as a negative base (Italy, Germany).
        Countries without a supported withholding regime keep a zero base.

        Returns:
        - tuple: (base, withheld, surcharges, {tax type: amount})
        """
        event, day, known, amount, _ = payout
        booked, cobol = self.booked[(policy, event)], day < self.conversion
        tax = WITHHOLDING.get(country)
        if country == 'CH':
            base = self.convert(amount, policy, country, day)
        elif country in ('IT', 'DE'):
            base = self.gain(policy, payout, withdrawals, country)
            base = self.german_base(policy, day, base) if country == 'DE' else base
        else:
            base = Decimal('0.00')
        if tax not in booked:
            return base, Decimal('0.00'), Decimal('0.00'), {}
        rate, _ = self.rates.rate(country, tax, day, known)
        rate = self.italian_rate(policy, day, known) if country == 'IT' else rate
        church_rate, _ = self.rates.rate(country, 'KIS', day, known, region) if 'KIS' in booked else (None, None)
        withheld = money(base / (4 + church_rate) if church_rate is not None else base * rate, cobol)
        amounts = {tax: withheld}
        for surcharge in ['SOL', 'KIS']:
            surcharge_rate, _ = self.rates.rate(country, surcharge, day, known, region)
            if surcharge in booked and surcharge_rate is not None:
                amounts[surcharge] = money(withheld * surcharge_rate, cobol)
        return base, withheld, sum(amounts.get(name, Decimal('0.00')) for name in ['SOL', 'KIS']), amounts
