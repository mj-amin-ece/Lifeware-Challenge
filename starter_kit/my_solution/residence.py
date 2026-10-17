"""Historical policyholders, residence versions and policyholder birth dates."""
from collections import defaultdict


class Residence:
    def __init__(self, data):
        """Index the policyholders and their addresses with their validity periods.
        Parameters: data (LegacyData): Decoded export.
        """
        self.holders, self.addresses = defaultdict(list), defaultdict(list)
        for row in data.table('NRHOLD').sort_values('HD_VRSNR').itertuples():
            self.holders[row.HD_POLNR].append((row.HD_VLDFR.date(), row.HD_VLDTO.date(), row.HD_PERNR))
        for row in data.table('NRADDR').sort_values('AD_VRSNR').itertuples():
            self.addresses[row.AD_PERNR].append((row.AD_VLDFR.date(), row.AD_VLDTO.date(), row))
        self.persons = data.table('NRPERS').set_index('PS_PERNR').PS_BIRTH.to_dict()

    @staticmethod
    def valid(rows, day):
        """The last (highest version) of the rows valid on `day`, or None."""
        valid = [row[2] for row in rows if row[0] <= day <= row[1]]
        return valid[-1] if valid else None

    def holder(self, policy, day):
        """Policyholder of a policy on `day`.
        Parameters: policy (str): Policy number; day (datetime.date): Day.
        Returns (str): Person number.
        """
        return self.valid(self.holders[policy], day) or self.holders[policy][0][2]

    def address(self, policy, day):
        """Address of the policyholder valid on `day`.
        Parameters: policy (str): Policy number; day (datetime.date): Day.
        Returns (namedtuple): Row of NRADDR (country, region, reporting status, church membership).
        """
        person = self.holder(policy, day)
        return self.valid(self.addresses[person], day) or self.addresses[person][-1][2]

    def birth(self, policy, day):
        """Birth date of the policyholder on `day`.
        Parameters: policy (str): Policy number; day (datetime.date): Day.
        Returns (datetime.date): Birth date.
        """
        return self.persons[self.holder(policy, day)].date()
