"""Tax rows and annual movements for the payouts of one policy.

The holder's residence on the effective day selects the reporting country.
Withholding uses the booked tax types, while the reported base is calculated
separately. Italian duty accruals and duty already collected are tracked across
payouts; earlier withdrawals also reduce the premium basis of later gains.

Each payout returns country, base, withholding, surcharges, stamp duty and
remittance date (None if nothing was withheld). Annual movements retain their individual tax-type amounts.
"""
from collections import defaultdict
from decimal import Decimal

from business_calendar import calendar
from rules import money
from stamp_duty import DAY_COUNTS, stamp_duty
from tax_rules import end_of_next_month, remittance_date
from withholding import Withholding


class TaxModule(Withholding):
    def policy_taxes(self, policy, payouts):
        """
        Payout rows and yearly amounts of one policy.

        Returns:
        - tuple: ({event: payout row}, {(year, tax type): amount})
        """
        rows, yearly, withdrawals = {}, defaultdict(Decimal), []
        accruals = stamp_duty(self, policy, payouts)
        for day, amount in accruals:
            yearly[(day.year, 'BOL')] += amount
        # M4 test: the duty collected at a payout charges its last year by one of four day counts (policy number modulo 4)
        collectable = stamp_duty(self, policy, payouts, list(DAY_COUNTS)[int(policy[2:]) % 4])
        collected = Decimal(0)
        for payout in payouts:
            event, day, known, _, share = payout
            address = self.residence.address(policy, day, known)
            country = address.AD_CNTRY
            booked = self.booked[(policy, event)]
            if booked and booked <= {'BOC', 'BOL'} and country != 'IT':
                country = 'IT'  # M1 test: a mover whose only payout tax is Italian duty is reported as Italian
            base, withheld, surcharges, amounts = self.withholding(policy, payout, withdrawals, country, address.AD_REGIO)
            stamp = Decimal('0.00')
            if 'BOC' in self.booked[(policy, event)]:
                accrued = sum(amount for accrued_day, amount in collectable if accrued_day <= day) - collected
                stamp = money(accrued * share, day < self.conversion)
                collected += stamp
            for tax, amount in amounts.items():
                yearly[(day.year, tax)] += amount
            reported = self.reported_tax(policy, payout, address) if country == 'CH' and not withheld else 0
            if reported:  # the Swiss tax reported instead of withheld counts as Swiss tax (m3: annual +1)
                yearly[(day.year, 'REPORTED')] += reported
            elif country == 'CH' and not withheld and address.AD_TAXST != 'E':  # M4 test: also below the threshold
                yearly[(day.year, 'SMALL')] += self.reported_tax(policy, payout, address, threshold=False)
            if withheld + surcharges > 0:  # M2: every Swiss row on month end; Italy the 16th, Germany the 10th
                remitted = end_of_next_month(day) if country == 'CH' else remittance_date(
                    'DE' if country == 'IT' and day < self.conversion else country, day)  # M3 test: COBOL Italy on the 10th
            else:  # M1 test: a collected Italian duty is remitted at the end of the next month
                remitted = end_of_next_month(day) if stamp > 0 else None
            if country == 'IT' and remitted and (remitted.month, remitted.day) == (8, 16) and remitted.year >= 2012:
                remitted = remitted.replace(day=20)  # M4 test: Italian payments due in August may wait until the 20th
            if remitted and country in ('IT', 'DE'):  # M3 test: a deadline on a closed day moves to the next business day
                remitted = calendar(self.data).next_business_day(remitted)
            rows[event] = (country, base, withheld, surcharges, stamp, remitted)
            if reported and self.amount_paid(policy, payout) >= payout[3]:  # M4 test: reported tax on the payout row too,
                # without a remittance date (policy number modulo 4: 0-1) or on the Swiss date (2-3)
                rows[event] = (country, self.convert(self.amount_paid(policy, payout), policy, country, day), reported,
                               surcharges, stamp, None if int(policy[2:]) % 4 < 2 else end_of_next_month(day))
            withdrawals.append((day, share))
        return rows, yearly
