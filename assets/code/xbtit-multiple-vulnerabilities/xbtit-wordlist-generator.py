import hashlib
import sys
import time

if len(sys.argv) < 2:
    print 'Usage: python {name} /path/to/wordlist.txt'.format(name = sys.argv[0])
    exit(1)

start_time = time.time()

with open(sys.argv[1], 'r') as passwords:
  for password in passwords:
    digest = hashlib.md5()
    digest.update(password.strip())
    hash = digest.hexdigest()

    for rnd in range(100000, 1000000):
        print '{rnd}{hash}{rnd}'.format(rnd = rnd, hash = hash)

print >> sys.stderr, '--- %s seconds ---' % (time.time() - start_time)
