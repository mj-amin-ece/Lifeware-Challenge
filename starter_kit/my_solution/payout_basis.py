"""Premium basis and German adjustments used to report a payout gain."""
from decimal import Decimal


from rules import money
from tax_data import TaxData


class PayoutBasis(TaxData):
    def premium_basis(self, policy, day, withdrawals, country):
        """Unrounded remaining premium basis in tax currency before this payout.

        Each premium is converted on receipt, then reduced by subsequent shares
        withdrawn. Round only the share allocated to the current payout. Kept as
        a separate step so the research trace can inspect the actual calculation.
        """
        basis = Decimal(0)
        for paid_day, premium, _ in self.premiums[policy]:
            if paid_day <= day:
                left = self.convert(premium, policy, country, paid_day)
                for withdrawn_day, withdrawn in withdrawals:
                    if withdrawn_day >= paid_day:
                        left *= 1 - withdrawn
                basis += left
        return basis

    def gain(self, policy, payout, withdrawals, country):
        """
        Gain in tax currency: customer benefit less premiums belonging to the share paid out.

        Parameters:
        - policy (str): Policy number.
        - payout (tuple): (event, day, processed at, amount, share).
        - withdrawals (list): Earlier payouts of the policy as (day, share).
        - country (str): Country of the tax.

        Returns:
        - Decimal: Gain (negative for a loss).
        """
        _, day, _, _, share = payout
        basis = self.premium_basis(policy, day, withdrawals, country)
        return self.convert(self.amount_paid(policy, payout), policy, country, day) - money(
            basis * share, day < self.conversion)

    def german_base(self, policy, day, gain):
        """
        Taxable part of a gain in Germany: the whole gain. The insurer withholds on the full difference even when only
        half of it is taxable (the half-income rule is applied in the customer's tax return, section 43 (1) 4 EStG),
        and Neuron applied no partial exemption either.

        Parameters:
        - policy (str): Policy number.
        - day (datetime.date): Day of the payout.
        - gain (Decimal): Gain in EUR.

        Returns:
        - Decimal: Taxable base.
        """
        return money(gain, day < self.conversion)
