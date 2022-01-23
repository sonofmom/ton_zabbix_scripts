import re
import subprocess
import sys
import time

class TonNetwork:
    def __init__(self, lite_client, log):
        self.lc = lite_client
        self.log = log

    def get_last(self):
        self.log.log(self.__class__.__name__, 3, 'Retrieving last block info')

        try:
            output = self.lc.exec('last')
        except Exception as e:
            self.log.log(self.__class__.__name__, 1, "Could not execute `last`: " + str(e))
            return None

        match = re.match(r'.+server is (.*) created at \d* \((\d+) seconds ago\)', output, re.M | re.I)
        if (match):
            self.log.log(self.__class__.__name__, 3, 'Last block {} seconds ago'.format(match.group(2)))
            return {
                'ago': match.group(2),
                'block': self.parse_block_info(match.group(1))
            }

    def run_method(self, address, method):
        self.log.log(self.__class__.__name__, 3, "Running method '{}' on address '{}'".format(method, address))

        try:
            output = self.lc.exec('runmethod {} {}'.format(address, method))
        except Exception as e:
            self.log.log(self.__class__.__name__, 1, "Could not execute `runmethod`: " + str(e))
            return None

        match = re.search(r'^result:\s*\[(.*)\].*', output, re.MULTILINE)
        if (match):
            res = match.group(1).strip()
            self.log.log(self.__class__.__name__, 3, "Result: '{}'".format(res))
            return res

    def check_block_known(self, blockinfo):
        self.log.log(self.__class__.__name__, 3, "Checking for presence of block '{}'".format(blockinfo))

        self.log.log(self.__class__.__name__, 3, "Validate LS connectivity.")
        if not self.get_last():
            self.log.log(self.__class__.__name__, 1, "Could not validate LS")
            return None

        try:
            stdout = self.lc.exec('gethead {}'.format(blockinfo), True)
        except Exception as e:
            self.log.log(self.__class__.__name__, 1, "Could not execute `gethead`: " + str(e))
            return None

        match = re.search(r'^(block header.+).+', stdout, re.MULTILINE)
        if (match):
            self.log.log(self.__class__.__name__, 3, "Block is known!")
            return 1
        else:
            self.log.log(self.__class__.__name__, 3, "Unknown block!")
            return 0

    def parse_block_info(self, as_string):
        match = re.match(r'\((-?\d*),(\d*),(\d*)\)|(\w*):(\w*).+', as_string, re.M | re.I)
        if match:
            return {
                "as_string": match.group(),
                "chain": match.group(1),
                "shard": match.group(2),
                "seqno": match.group(3),
                "roothash": match.group(4),
                "filehash": match.group(5)
            }

    def get_wallet_value(self, wallet):
        [success, storage]  = self.lc.exec("getaccount %s" % wallet)
        if storage is None:
            return 0
        balance = self.lc.get_var(storage, "balance")
        grams = self.lc.get_var(balance, "grams")
        value = self.lc.get_var(grams, "value")
        return self.ng2g(value)

    def ng2g(self, grams):
        return int(grams)/10**9

# end class
