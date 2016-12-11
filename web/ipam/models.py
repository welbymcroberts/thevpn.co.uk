from django.db import models

CIDR_SIZES=(
    (32,"/32 (1 Host)"),
    (31,"/31 (2 Hosts)"),
    (30,"/30 (4 Hosts)"),
    (29,"/29 (8 Hosts)"),
    (28,"/28 (16 Hosts)"),
    (27,"/27 (32 Hosts)"),
    (26,"/26 (64 Hosts)"),
    (25,"/25 (128 Hosts)"),
    (24,"/24 (256 Hosts)")
)


class IPNetwork(models.Model):
    address = models.GenericIPAddressField()
    size = models.PositiveSmallIntegerField(
        choices=CIDR_SIZES
    )
    description = models.CharField(max_length=500)
    in_use = models.BooleanField()

    def __str__(self):
        return "%s/%d" %(self.address, self.size)
