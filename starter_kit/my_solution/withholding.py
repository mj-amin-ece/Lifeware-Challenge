"""t7: the taxes withheld from a payout (withdrawal, surrender, death benefit).

- Gain of a payout: the customer benefit (after penalty or including insured death benefit), in tax currency,
  less the premiums paid, each one
  converted on the day it was received (and reduced by the shares already withdrawn), times the share now withdrawn.
- CH: withholding tax (VST) on the whole payout in CHF.
- IT: substitute tax (SOS) on the gain.
- DE: capital gains tax (KST) on the gain, less the partial exemption (TFS) from 2018 and only half of it (HEV) after
  12 years and from the age of 60 (62 from 2012); solidarity surcharge (SOL) and church tax (KIS) on the KST.
"""
from payout_basis import HALF_INCOME, PayoutBasis
from decimal import Decimal

from rules import money

WITHHOLDING = {'CH': 'VST', 'IT': 'SOS', 'DE': 'KST'}


class Withholding(PayoutBasis):
    def withholding(self, policy, payout, withdrawals, country, region):
        """
        Report the amount subject to a booked withholding tax; otherwise report zero.

        This candidate uses zero for the taxable base of untaxed payouts. The
        research comparison also tests reporting their economic gain or loss.

        Returns:
        - tuple: (base, withheld, surcharges, {tax type: amount})
        """
        event, day, known, _, _ = payout
        booked, cobol = self.booked[(policy, event)], day < self.conversion
        tax = WITHHOLDING.get(country)
        if tax not in booked:
            return self.untaxed_base(policy, payout, country), Decimal('0.00'), Decimal('0.00'), {}
        if country == 'CH':
            base = self.convert(self.amount_paid(policy, payout), policy, country, day)
        elif country in ('IT', 'DE'):
            base = self.gain(policy, payout, withdrawals, country)
            base = self.german_base(policy, day, base) if country == 'DE' else base
        else:
            base = Decimal('0.00')
        rate, _ = self.rates.rate(country, tax, day, known)
        withheld = money(base * rate, cobol)
        amounts = {tax: withheld}
        for surcharge in ['SOL', 'KIS']:
            surcharge_rate, _ = self.rates.rate(country, surcharge, day, known, region)
            if surcharge in booked and surcharge_rate is not None:
                amounts[surcharge] = money(withheld * surcharge_rate, cobol)
        return base, withheld, sum(amounts.get(name, Decimal('0.00')) for name in ['SOL', 'KIS']), amounts

    def untaxed_base(self, policy, payout, country):
        """M3 test, base of a payout nothing was withheld from (0.00 and the natural base never scored): outside
        Switzerland the amount paid; in Switzerland the value before the surrender penalty, 0.00 without a penalty."""
        _, day, _, sold, _ = payout
        paid = self.amount_paid(policy, payout)
        if country != 'CH':
            return self.convert(paid, policy, country, day)
        return self.convert(sold, policy, country, day) if paid < sold else Decimal('0.00')

    def reported_tax(self, policy, payout, address, threshold=True):
        """Swiss tax on a payout above the threshold of a holder who did not object: reported, not withheld."""
        _, day, known, _, _ = payout
        rate, limit = self.rates.rate('CH', 'VST', day, known)
        amount = self.convert(self.amount_paid(policy, payout), policy, 'CH', day)
        if address.AD_TAXST == 'E' or rate is None or (threshold and amount <= limit):
            return Decimal('0.00')
        return money(amount * rate, day < self.conversion)
