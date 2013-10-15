#!/usr/bin/env python

from optparse import OptionParser
import sys
import ConfigParser
import requests
import StringIO
import difflib
import getpass

BASEURL = 'http://kgs.4teamwork.ch/release/teamraum'


class Command(object):

    baseversion = None
    compairtoversion = None

    def __init__(self, argv):
        parser = OptionParser()
        parser.add_option('-u', '--user', dest='user', default='',
                          help='github username')

        self.options, self.arguments = parser.parse_args(argv)

        if len(self.arguments) != 2:
            print "Need two arguments 'tmdiff [version from] [version to]'"
            return sys.exit(0)


        self.auth = ()
        if self.options.user:
            password = getpass.getpass(
                'Password for user [%s]: ' % self.options.user)
            self.auth = (self.options.user, password)

        self.baseversion = self.arguments[0]
        self.compairtoversion = self.arguments[1]

        self.baseconfig = self.get_base_versions()
        self.compairconfig = self.get_compair_versions()


    def __call__(self):

        versions_from = set(self.baseconfig.items('versions'))
        versions_to = set(self.compairconfig.items('versions'))

        diff = versions_to - versions_from

        # Fetch data from github (specific versions)

        self.print_changelog(diff)

#        self.print_new(new)

        return sys.exit(1)

        import pdb; pdb.set_trace( )


    def print_changelog(self, version_diff):
        # 4teamwor url raw
        url = 'https://raw.github.com/4teamwork/{0}/{1}/docs/HISTORY.txt'
        old_versions = self.baseconfig._sections['versions']

        for pkg, new_version in version_diff:
            if pkg not in old_versions:
                print "+" * 20
                print "NEW PACKAGE: %s" % pkg
                print "+" * 20
                continue

            new_changelog = requests.get(url.format(pkg, new_version), auth=self.auth)
            old_changelog = requests.get(url.format(pkg, old_versions[pkg]), auth=self.auth)

            if pkg == 'egov.contectdirectory':
                import pdb; pdb.set_trace( )

            if new_changelog.status_code != 200 or old_changelog.status_code != 200:
                print "-" * 20
                print "WARNING: wasn't able to get infos for: %s" % pkg
                print "-" * 20
                continue


            old_file = StringIO.StringIO(old_changelog._content)
            new_file = StringIO.StringIO(new_changelog._content)

            old_file.seek(0)
            new_file.seek(0)

            differ = difflib.Differ()
            diff = differ.compare(old_file.readlines(), new_file.readlines())

            print "*" * 20
            print "PACKAGE: %s" % pkg
            print "*" * 20

            for line in list(diff):
                if line == '+ \n':
                    continue
                if line.startswith('+ '):
                    sys.stdout.write(line[2:])


    def get_base_versions(self):
        url = '/'.join([BASEURL, self.baseversion])
        return self.get_config(url)

    def get_compair_versions(self):
        url = '/'.join([BASEURL, self.compairtoversion])
        return self.get_config(url)

    def get_config(self, url):

        req = requests.get(url)

        if req.status_code != 200:
            print 'Something went wrong: %s' % req.status_code

        data = StringIO.StringIO(req._content)
        data.seek(0)

        config = ConfigParser.RawConfigParser()
        config.readfp(data)
        return config


if __name__ == '__main__':
    Command(sys.argv[1:])()
