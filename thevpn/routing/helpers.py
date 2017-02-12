from .models import AS
import random
import string


def get_next_ASN(countrycode, ituregion):
    # We should always have a new AS number like 4214400000
    prefix = "%s%s%s" %('42', ituregion, countrycode)
    first_as = int("{:0<10}".format(prefix))
    last_as = int("{:0<10}".format(int(prefix)+1))-1
    try:
        last_allocated_as = AS.objects.filter(number__lte=last_as,number__gte=first_as).order_by('-number')[0]
        if last_as == last_allocated_as.number:
            return None
        else:
            return int(last_allocated_as.number) + 1
    except IndexError:
        return first_as

def make_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def file_get_contents(filename):
    with open(filename) as f:
        s = f.read()
    return s
